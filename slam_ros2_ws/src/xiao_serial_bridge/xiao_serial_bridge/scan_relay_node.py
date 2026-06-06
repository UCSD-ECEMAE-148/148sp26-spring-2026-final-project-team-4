import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class ScanRelayNode(Node):
    """Republish /scan with a fixed beam count to avoid slam_toolbox segfault on variable-size scans."""

    def __init__(self):
        super().__init__('scan_relay_node')
        self.declare_parameter('input_topic', '/scan')
        self.declare_parameter('output_topic', '/scan_fixed')
        self.declare_parameter('target_beams', 450)

        self._n = self.get_parameter('target_beams').get_parameter_value().integer_value
        in_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        out_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self._pub = self.create_publisher(LaserScan, out_topic, 10)
        self._sub = self.create_subscription(LaserScan, in_topic, self._cb, 10)
        self.get_logger().info(f'Relaying {in_topic} → {out_topic} at {self._n} beams')

    def _cb(self, msg: LaserScan):
        n = self._n
        src_n = len(msg.ranges)
        if src_n == 0:
            return

        out = LaserScan()
        out.header = msg.header
        out.angle_min = msg.angle_min
        out.angle_increment = (msg.angle_max - msg.angle_min) / (n - 1)
        out.angle_max = msg.angle_min + out.angle_increment * (n - 1)
        out.time_increment = msg.time_increment * src_n / n
        out.scan_time = msg.scan_time
        out.range_min = msg.range_min
        out.range_max = msg.range_max

        # Nearest-neighbour resample — fast and avoids interpolation across obstacles
        out.ranges = []
        for i in range(n):
            src_idx = int(round(i * (src_n - 1) / (n - 1)))
            out.ranges.append(msg.ranges[src_idx])

        out.intensities = []
        if msg.intensities:
            for i in range(n):
                src_idx = int(round(i * (src_n - 1) / (n - 1)))
                out.intensities.append(msg.intensities[src_idx])

        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ScanRelayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
