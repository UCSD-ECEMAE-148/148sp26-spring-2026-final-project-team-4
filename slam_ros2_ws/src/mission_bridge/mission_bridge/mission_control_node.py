import os
import shutil

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String


class MissionControlNode(Node):
    def __init__(self):
        super().__init__('mission_control_node')
        self.command_sub = self.create_subscription(String, '/mission/control', self.command_cb, 10)
        self.started_pub = self.create_publisher(Bool, '/mission/started', 10)
        self.state_pub = self.create_publisher(String, '/mission/state', 10)
        self.mission_active = False

    def _publish_state(self, state: str):
        msg = String()
        msg.data = state
        self.state_pub.publish(msg)

    def _publish_bool(self, publisher, value: bool):
        msg = Bool()
        msg.data = value
        publisher.publish(msg)

    def _reset_artifacts(self):
        images_dir = '/tmp/mission_images'
        path_file = '/tmp/mission_path.json'
        manifest_path = os.path.join(images_dir, 'manifest.json')

        shutil.rmtree(images_dir, ignore_errors=True)
        os.makedirs(images_dir, exist_ok=True)

        for file_path in (path_file, manifest_path):
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def command_cb(self, msg: String):
        command = msg.data.strip().lower()
        if command == 'start':
            if self.mission_active:
                self.get_logger().info('Mission already active; ignoring duplicate start command')
                return

            self._reset_artifacts()
            self.mission_active = True
            self._publish_bool(self.started_pub, True)
            self._publish_state('started')
            self.get_logger().info('Mission start accepted')
            return

        if command == 'end':
            if not self.mission_active:
                self.get_logger().info('Mission is not active; ignoring end command')
                return

            self.mission_active = False
            self._publish_state('returning')
            self.get_logger().info('Mission end accepted; waiting for return-to-start completion')
            return

        self.get_logger().warning(f'Unknown mission control command: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = MissionControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()