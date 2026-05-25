import os
import json
import math
from threading import Lock

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import CompressedImage


def _quat_to_yaw(qx, qy, qz, qw):
    # yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


class ImageCaptureNode(Node):
    def __init__(self):
        super().__init__('image_capture_node')

        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.image_sub = self.create_subscription(CompressedImage, '/camera/image_raw/compressed', self.image_cb, 10)
        self.pub = self.create_publisher(CompressedImage, '/mission/images', 10)

        self.lock = Lock()
        self.last_pose = None
        self.last_capture_pose = None
        self.capture_distance = 0.75
        self.counter = 0
        self.images_dir = '/tmp/mission_images'
        os.makedirs(self.images_dir, exist_ok=True)
        self.manifest_path = os.path.join(self.images_dir, 'manifest.json')
        self.manifest = []
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, 'r') as fh:
                    self.manifest = json.load(fh)
                    self.counter = len(self.manifest)
            except Exception:
                self.get_logger().warning('Failed to load existing manifest.json')

    def odom_cb(self, msg: Odometry):
        with self.lock:
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            q = msg.pose.pose.orientation
            yaw = _quat_to_yaw(q.x, q.y, q.z, q.w)
            self.last_pose = {'x': float(x), 'y': float(y), 'yaw': float(yaw), 'timestamp': float(self.get_clock().now().nanoseconds) / 1e9}

    def _distance(self, a, b):
        return math.hypot(a['x'] - b['x'], a['y'] - b['y'])

    def image_cb(self, msg: CompressedImage):
        with self.lock:
            if self.last_pose is None:
                return
            if self.last_capture_pose is None:
                should_capture = True
            else:
                should_capture = self._distance(self.last_pose, self.last_capture_pose) >= self.capture_distance
            if not should_capture:
                return
            # prepare message
            out_msg = CompressedImage()
            out_msg.format = msg.format
            out_msg.data = msg.data
            # store pose as JSON in header.frame_id
            header_json = json.dumps(self.last_pose)
            out_msg.header.frame_id = header_json
            out_msg.header.stamp = msg.header.stamp

            # publish
            self.pub.publish(out_msg)

            # save to disk
            filename = f'img_{self.counter:04d}.jpg'
            path = os.path.join(self.images_dir, filename)
            try:
                with open(path, 'wb') as fh:
                    fh.write(bytes(msg.data))
            except Exception:
                self.get_logger().error(f'Failed to write image to {path}')
                return

            entry = {'filename': filename, 'pose': self.last_pose}
            self.manifest.append(entry)
            try:
                with open(self.manifest_path, 'w') as fh:
                    json.dump(self.manifest, fh)
            except Exception:
                self.get_logger().warning('Failed to update manifest.json')

            self.counter += 1
            self.last_capture_pose = dict(self.last_pose)
            self.get_logger().info(f'Captured image {filename} at {self.last_capture_pose}')


def main(args=None):
    rclpy.init(args=args)
    node = ImageCaptureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
