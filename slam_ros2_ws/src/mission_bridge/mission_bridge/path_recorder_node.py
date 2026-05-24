import os
import json
from threading import Lock

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_srvs.srv import Trigger


class PathRecorderNode(Node):
    def __init__(self):
        super().__init__('path_recorder_node')
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.timer = self.create_timer(0.5, self.sample_pose)
        self.lock = Lock()
        self.last_odom = None
        self.path = []
        self.path_file = '/tmp/mission_path.json'

        self.srv = self.create_service(Trigger, 'mission/flush_path', self.handle_flush)

    def odom_cb(self, msg: Odometry):
        with self.lock:
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            q = msg.pose.pose.orientation
            # compute yaw minimally
            yaw = 0.0
            try:
                import math
                siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
                cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
                yaw = math.atan2(siny_cosp, cosy_cosp)
            except Exception:
                pass
            self.last_odom = {'x': float(x), 'y': float(y), 'yaw': float(yaw), 'timestamp': float(self.get_clock().now().nanoseconds) / 1e9}

    def sample_pose(self):
        with self.lock:
            if self.last_odom is not None:
                self.path.append(self.last_odom.copy())

    def handle_flush(self, request, response):
        try:
            with open(self.path_file, 'w') as fh:
                json.dump(self.path, fh)
            response.success = True
            response.message = f'Wrote {len(self.path)} poses to {self.path_file}'
            self.get_logger().info(response.message)
        except Exception as e:
            response.success = False
            response.message = str(e)
            self.get_logger().error(f'Failed to write path: {e}')
        return response

    def destroy_node(self):
        # write path on shutdown
        try:
            with open(self.path_file, 'w') as fh:
                json.dump(self.path, fh)
            self.get_logger().info(f'Wrote path to {self.path_file} on shutdown')
        except Exception as e:
            self.get_logger().warning(f'Failed to write path on shutdown: {e}')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PathRecorderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
