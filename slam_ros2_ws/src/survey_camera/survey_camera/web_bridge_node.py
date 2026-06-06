import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_srvs.srv import Trigger


latest_jpeg = None
latest_jpeg_lock = threading.Lock()


class CameraWebBridge(Node):
    def __init__(self):
        super().__init__("camera_web_bridge")

        self.bridge = CvBridge()

        self.create_subscription(
            Image,
            "/survey_camera/image_raw",
            self.image_callback,
            10,
        )

        self.capture_client = self.create_client(
            Trigger,
            "/survey_camera/capture",
        )

        self.get_logger().info("Camera web bridge started")
        self.get_logger().info("MJPEG stream: http://localhost:8080/video")
        self.get_logger().info("Capture API:  http://localhost:8080/capture")

    def image_callback(self, msg):
        global latest_jpeg

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        success, encoded = cv2.imencode(".jpg", frame)

        if not success:
            return

        with latest_jpeg_lock:
            latest_jpeg = encoded.tobytes()

    def capture_image(self):
        if not self.capture_client.wait_for_service(timeout_sec=1.0):
            return False, "Capture service not available"

        request = Trigger.Request()
        future = self.capture_client.call_async(request)

        rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)

        if future.result() is None:
            return False, "Capture service failed"

        result = future.result()
        return result.success, result.message


ros_node = None


class CameraHTTPHandler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/video":
            self.send_response(200)
            self._cors_headers()
            self.send_header(
                "Content-Type",
                "multipart/x-mixed-replace; boundary=frame",
            )
            self.end_headers()

            while True:
                with latest_jpeg_lock:
                    frame = latest_jpeg

                if frame is None:
                    continue

                try:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                except BrokenPipeError:
                    break

        elif self.path == "/health":
            self.send_response(200)
            self._cors_headers()
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            self.send_response(404)
            self._cors_headers()
            self.end_headers()

    def do_POST(self):
        if self.path == "/capture":
            success, message = ros_node.capture_image()

            self.send_response(200 if success else 500)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = (
                f'{{"success": {str(success).lower()}, '
                f'"message": "{message}"}}'
            )

            self.wfile.write(response.encode("utf-8"))

        else:
            self.send_response(404)
            self._cors_headers()
            self.end_headers()


def start_http_server():
    server = ThreadingHTTPServer(("0.0.0.0", 8080), CameraHTTPHandler)
    server.serve_forever()


def main(args=None):
    global ros_node

    rclpy.init(args=args)

    ros_node = CameraWebBridge()

    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    rclpy.spin(ros_node)

    ros_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()