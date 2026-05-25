import os
import json
import asyncio
from threading import Event

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from nav_msgs.msg import OccupancyGrid
from std_srvs.srv import Trigger


class MissionTriggerNode(Node):
    def __init__(self):
        super().__init__('mission_trigger_node')
        self.sub = self.create_subscription(Bool, '/mission/complete', self.trigger_cb, 10)
        self.transfer_pub = self.create_publisher(Bool, '/mission/transfer_complete', 10)

    def trigger_cb(self, msg: Bool):
        if not msg.data:
            return
        self.get_logger().info('Mission complete received; initiating transfer')
        # 1) call path recorder flush service
        client = self.create_client(Trigger, 'mission/flush_path')
        if not client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('mission/flush_path service not available')
        else:
            req = Trigger.Request()
            fut = client.call_async(req)
            rclpy.spin_until_future_complete(self, fut, timeout_sec=5.0)
            if fut.result() is None:
                self.get_logger().warning('Flush path service call failed or timed out')
            else:
                self.get_logger().info(f'Flush result: {fut.result().message}')

        # 2) wait for /map (OccupancyGrid) once
        map_event = Event()
        map_container = {}

        def map_cb(map_msg: OccupancyGrid):
            map_container['msg'] = map_msg
            map_event.set()

        sub_map = self.create_subscription(OccupancyGrid, '/map', map_cb, 10)
        got_map = map_event.wait(timeout=5.0)
        if not got_map:
            self.get_logger().warning('Timed out waiting for /map; proceeding without map')
            map_msg = None
        else:
            map_msg = map_container.get('msg')

        # 3) serialize map
        map_json = None
        if map_msg is not None:
            info = map_msg.info
            map_json = {
                'width': info.width,
                'height': info.height,
                'resolution': info.resolution,
                'origin_x': info.origin.position.x,
                'origin_y': info.origin.position.y,
                'data': list(map_msg.data),
            }

        # 4) build mission bundle
        images_dir = '/tmp/mission_images'
        manifest_path = os.path.join(images_dir, 'manifest.json')
        image_manifest = []
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as fh:
                    image_manifest = json.load(fh)
            except Exception:
                self.get_logger().warning('Failed to read image manifest')

        path_file = '/tmp/mission_path.json'
        path_data = []
        if os.path.exists(path_file):
            try:
                with open(path_file, 'r') as fh:
                    path_data = json.load(fh)
            except Exception:
                self.get_logger().warning('Failed to read mission path')

        bundle = {
            'map': map_json,
            'path': path_data,
            'images': images_dir,
            'image_manifest': image_manifest,
        }

        # 5) publish to rosbridge via websocket
        try:
            asyncio.get_event_loop().run_until_complete(self._send_to_rosbridge(bundle))
        except Exception as e:
            self.get_logger().error(f'Failed to send to rosbridge: {e}')

        # 6) publish transfer complete
        out = Bool()
        out.data = True
        self.transfer_pub.publish(out)
        self.get_logger().info('Published /mission/transfer_complete')

    async def _send_to_rosbridge(self, bundle):
        try:
            import websockets
        except Exception:
            self.get_logger().error('websockets package is required to publish via rosbridge (pip install websockets)')
            return

        uri = 'ws://localhost:9090'
        txt = json.dumps(bundle)
        # rosbridge publish message
        msg = json.dumps({'op': 'publish', 'topic': '/mission/payload', 'msg': {'data': txt}})
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(msg)
                self.get_logger().info('Published mission payload to rosbridge')
        except Exception as e:
            self.get_logger().error(f'WebSocket publish failed: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = MissionTriggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
