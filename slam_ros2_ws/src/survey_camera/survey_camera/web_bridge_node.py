import json
import math
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np
import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from cv_bridge import CvBridge
from nav_msgs.msg import OccupancyGrid
from pico_interfaces.srv import SetCameraAngle
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from sensor_msgs.msg import Image
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformListener


latest_jpeg = None
latest_jpeg_lock = threading.Lock()

latest_map = None
map_lock = threading.Lock()

_MAP_QOS = QoSProfile(
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
)

_MAP_SNAPSHOT_PATH = os.path.expanduser(
    '~/scout-survey-rover/mission_report/public/map_snapshot.png'
)


class CameraWebBridge(Node):
    def __init__(self):
        super().__init__('camera_web_bridge')
        self.bridge = CvBridge()

        self.create_subscription(Image, '/survey_camera/image_raw', self._image_cb, 10)
        self.create_subscription(OccupancyGrid, '/map', self._map_cb, _MAP_QOS)

        self.capture_client = self.create_client(Trigger, '/survey_camera/capture')
        # Publish AckermannDriveStamped directly — ackermann_to_vesc_node subscribes here
        self.ackermann_pub = self.create_publisher(AckermannDriveStamped, '/ackermann_cmd', 10)
        self.camera_angle_client = self.create_client(SetCameraAngle, 'pico/set_camera_angle')

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.get_logger().info('Camera web bridge started')
        self.get_logger().info('  MJPEG stream    : http://<host>:8080/video')
        self.get_logger().info('  Capture API     : POST http://<host>:8080/capture')
        self.get_logger().info('  Drive API       : POST http://<host>:8080/drive')
        self.get_logger().info('  Camera angle    : POST http://<host>:8080/camera_angle')
        self.get_logger().info('  SLAM map        : http://<host>:8080/map_image')
        self.get_logger().info('  Save map snap   : POST http://<host>:8080/save_map')

    # ------------------------------------------------------------------ #
    # ROS callbacks                                                        #
    # ------------------------------------------------------------------ #

    def _image_cb(self, msg):
        global latest_jpeg
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        ok, encoded = cv2.imencode('.jpg', frame)
        if not ok:
            return
        with latest_jpeg_lock:
            latest_jpeg = encoded.tobytes()

    def _map_cb(self, msg):
        global latest_map
        with map_lock:
            latest_map = msg

    # ------------------------------------------------------------------ #
    # Service call helpers (called from HTTP thread)                      #
    # ------------------------------------------------------------------ #

    def capture_image(self):
        if not self.capture_client.wait_for_service(timeout_sec=1.0):
            return False, 'Capture service not available'
        future = self.capture_client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)
        if future.result() is None:
            return False, 'Capture service failed'
        r = future.result()
        return r.success, r.message

    def set_camera_angle(self, angle: int):
        # Fire-and-forget: do not block the HTTP thread on the service round-trip.
        # service_is_ready() is a non-blocking check (unlike wait_for_service which
        # blocks up to timeout_sec even when the service is up).
        # spin_until_future_complete from a non-ROS thread while rclpy.spin() runs
        # on the main thread is also threading-unsafe, so we skip the wait entirely.
        if not self.camera_angle_client.service_is_ready():
            return False, 'pico/set_camera_angle not available (Pico disconnected?)'
        req = SetCameraAngle.Request()
        req.angle = int(angle)
        self.camera_angle_client.call_async(req)
        return True, 'ok'

    # ------------------------------------------------------------------ #
    # SLAM map rendering                                                   #
    # ------------------------------------------------------------------ #

    def render_map_image(self):
        with map_lock:
            grid = latest_map
        if grid is None:
            return None
        w, h = grid.info.width, grid.info.height
        if w == 0 or h == 0:
            return None

        data = np.array(grid.data, dtype=np.int8).reshape((h, w))
        img = np.empty((h, w, 3), dtype=np.uint8)
        img[:] = [71, 85, 105]             # unknown  — slate-600
        img[data == 0] = [226, 232, 240]   # free     — slate-200
        img[data > 0] = [15, 23, 42]       # occupied — slate-950
        img = np.flipud(img)               # ROS origin bottom-left → image top-left

        scale = 4
        display = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)

        try:
            t = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            rx = t.transform.translation.x
            ry = t.transform.translation.y
            qz = t.transform.rotation.z
            qw = t.transform.rotation.w
            yaw = 2.0 * math.atan2(qz, qw)

            ox = grid.info.origin.position.x
            oy = grid.info.origin.position.y
            res = grid.info.resolution

            px = int((rx - ox) / res) * scale
            py = (h - 1 - int((ry - oy) / res)) * scale

            cv2.circle(display, (px, py), 8, (59, 130, 246), -1)
            cv2.circle(display, (px, py), 9, (255, 255, 255), 2)
            ex = int(px + 22 * math.cos(yaw))
            ey = int(py - 22 * math.sin(yaw))
            cv2.arrowedLine(display, (px, py), (ex, ey), (255, 255, 255), 2, tipLength=0.4)
        except Exception:
            pass

        ok, buf = cv2.imencode('.png', display)
        return buf.tobytes() if ok else None

    def save_map_snapshot(self):
        png = self.render_map_image()
        if png is None:
            return False, 'No map available yet'
        try:
            with open(_MAP_SNAPSHOT_PATH, 'wb') as f:
                f.write(png)
            return True, _MAP_SNAPSHOT_PATH
        except Exception as e:
            return False, str(e)


# ------------------------------------------------------------------ #
# HTTP server                                                          #
# ------------------------------------------------------------------ #

ros_node = None


class CameraHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress per-request stdout noise

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json(self, code: int, body: bytes):
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == '/video':
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            while True:
                with latest_jpeg_lock:
                    frame = latest_jpeg
                if frame is None:
                    continue
                try:
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                except BrokenPipeError:
                    break

        elif self.path.startswith('/map_image'):
            png = ros_node.render_map_image()
            if png is None:
                self.send_response(503)
                self._cors()
                self.end_headers()
                return
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'image/png')
            self.send_header('Cache-Control', 'no-cache, no-store')
            self.end_headers()
            self.wfile.write(png)

        elif self.path == '/health':
            self.send_response(200)
            self._cors()
            self.end_headers()
            self.wfile.write(b'OK')

        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def do_POST(self):
        if self.path == '/capture':
            success, message = ros_node.capture_image()
            self._json(
                200 if success else 500,
                f'{{"success":{str(success).lower()},"message":"{message}"}}'.encode(),
            )

        elif self.path == '/drive':
            try:
                length = int(self.headers.get('Content-Length', 0))
                data = json.loads(self.rfile.read(length))
                msg = AckermannDriveStamped()
                msg.header.stamp = ros_node.get_clock().now().to_msg()
                msg.drive.speed = float(data.get('linear_x', 0.0))
                # angular_z from the frontend is already in rad (max 0.35 = MAX_STEER)
                msg.drive.steering_angle = float(data.get('angular_z', 0.0))
                ros_node.ackermann_pub.publish(msg)
                self._json(200, b'{"ok":true}')
            except Exception:
                self._json(400, b'{"ok":false}')

        elif self.path == '/camera_angle':
            try:
                length = int(self.headers.get('Content-Length', 0))
                data = json.loads(self.rfile.read(length))
                angle = int(data.get('angle', 0))
                success, message = ros_node.set_camera_angle(angle)
                self._json(
                    200 if success else 500,
                    f'{{"success":{str(success).lower()},"message":"{message}"}}'.encode(),
                )
            except Exception as e:
                self._json(400, f'{{"ok":false,"message":"{e}"}}'.encode())

        elif self.path == '/save_map':
            success, message = ros_node.save_map_snapshot()
            self._json(
                200 if success else 503,
                f'{{"success":{str(success).lower()},"message":"{message}"}}'.encode(),
            )

        else:
            self.send_response(404)
            self._cors()
            self.end_headers()


def _start_http_server():
    server = ThreadingHTTPServer(('0.0.0.0', 8080), CameraHTTPHandler)
    server.serve_forever()


def main(args=None):
    global ros_node
    rclpy.init(args=args)
    ros_node = CameraWebBridge()
    threading.Thread(target=_start_http_server, daemon=True).start()
    rclpy.spin(ros_node)
    ros_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
