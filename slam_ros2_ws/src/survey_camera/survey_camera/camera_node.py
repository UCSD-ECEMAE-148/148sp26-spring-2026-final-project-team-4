import os
import cv2
import depthai as dai
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_srvs.srv import Trigger
from cv_bridge import CvBridge
from datetime import datetime


class SurveyCameraNode(Node):
    def __init__(self):
        super().__init__("survey_camera_node")

        self.bridge = CvBridge()
        self.latest_frame = None

        self.image_pub = self.create_publisher(Image, "/survey_camera/image_raw", 10)
        self.capture_srv = self.create_service(
            Trigger,
            "/survey_camera/capture",
            self.capture_callback,
        )

        self.save_dir = os.path.expanduser(
            "~/scout-survey-rover/mission_report/public/captures"
        )
        os.makedirs(self.save_dir, exist_ok=True)

        pipeline = dai.Pipeline()

        cam = pipeline.create(dai.node.ColorCamera)
        cam.setPreviewSize(640, 480)
        cam.setInterleaved(False)
        cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

        xout = pipeline.create(dai.node.XLinkOut)
        xout.setStreamName("video")
        cam.preview.link(xout.input)

        self.device = dai.Device(pipeline)
        self.queue = self.device.getOutputQueue(
            name="video",
            maxSize=4,
            blocking=False,
        )

        self.timer = self.create_timer(0.03, self.timer_callback)

        self.get_logger().info("Survey camera node started")

    def timer_callback(self):
        frame_packet = self.queue.tryGet()

        if frame_packet is None:
            return

        frame = frame_packet.getCvFrame()
        self.latest_frame = frame

        msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "oakd_camera"

        self.image_pub.publish(msg)

    def capture_callback(self, request, response):
        if self.latest_frame is None:
            response.success = False
            response.message = "No camera frame available"
            return response

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspection_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)

        cv2.imwrite(filepath, self.latest_frame)

        response.success = True
        response.message = filename

        self.get_logger().info(f"Saved image: {filepath}")

        return response


def main(args=None):
    rclpy.init(args=args)
    node = SurveyCameraNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()