import json
import math
import os
from typing import Dict, List, Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Bool, String


DEFAULT_ANCHORS = [10.0, 14.0, 23.0, 27.0, 37.0, 58.0, 81.0, 82.0, 135.0, 169.0, 344.0, 319.0]
DEFAULT_ANCHOR_MASKS = {
    'side52': [0, 1, 2],
    'side26': [3, 4, 5],
}


class OakdYoloSafetyNode(Node):
    def __init__(self):
        super().__init__('oakd_yolo_safety_node')

        self.declare_parameter('enable', True)
        self.declare_parameter('blob_path', '')
        self.declare_parameter('stop_on_detection', True)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('hazard_topic', '/oakd/yolo/hazard')
        self.declare_parameter('detection_topic', '/oakd/yolo/detections')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('iou_threshold', 0.45)
        self.declare_parameter('num_classes', 80)
        self.declare_parameter('coordinate_size', 4)
        self.declare_parameter('preview_width', 416)
        self.declare_parameter('preview_height', 416)
        self.declare_parameter('camera_fps', 30.0)
        self.declare_parameter('hold_time_s', 0.5)
        self.declare_parameter('center_x_ratio', 0.35)
        self.declare_parameter('center_y_ratio', 0.35)
        self.declare_parameter('min_area_ratio', 0.06)
        self.declare_parameter('hazard_label_ids', '0,1,2,3,4,5,6,7,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29')
        self.declare_parameter('anchors', ','.join(str(v) for v in DEFAULT_ANCHORS))
        self.declare_parameter('anchor_masks_json', json.dumps(DEFAULT_ANCHOR_MASKS))

        self.enabled = bool(self.get_parameter('enable').value)
        self.stop_on_detection = bool(self.get_parameter('stop_on_detection').value)
        self.cmd_vel_topic = str(self.get_parameter('cmd_vel_topic').value)
        self.hazard_topic = str(self.get_parameter('hazard_topic').value)
        self.detection_topic = str(self.get_parameter('detection_topic').value)
        self.blob_path = str(self.get_parameter('blob_path').value)
        self.confidence_threshold = float(self.get_parameter('confidence_threshold').value)
        self.iou_threshold = float(self.get_parameter('iou_threshold').value)
        self.num_classes = int(self.get_parameter('num_classes').value)
        self.coordinate_size = int(self.get_parameter('coordinate_size').value)
        self.preview_width = int(self.get_parameter('preview_width').value)
        self.preview_height = int(self.get_parameter('preview_height').value)
        self.camera_fps = float(self.get_parameter('camera_fps').value)
        self.hold_time_s = float(self.get_parameter('hold_time_s').value)
        self.center_x_ratio = float(self.get_parameter('center_x_ratio').value)
        self.center_y_ratio = float(self.get_parameter('center_y_ratio').value)
        self.min_area_ratio = float(self.get_parameter('min_area_ratio').value)
        self.hazard_label_ids = self._parse_int_set(self.get_parameter('hazard_label_ids').value)
        self.anchors = self._parse_float_list(self.get_parameter('anchors').value, DEFAULT_ANCHORS)
        self.anchor_masks = self._parse_json_dict(self.get_parameter('anchor_masks_json').value, DEFAULT_ANCHOR_MASKS)

        self.hazard_pub = self.create_publisher(Bool, self.hazard_topic, 10)
        self.summary_pub = self.create_publisher(String, self.detection_topic, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)

        self.last_hazard_time = None
        self.last_summary = ''
        self.depthai = None
        self.device = None
        self.detections_queue = None

        if self.enabled:
            self._setup_depthai()

        self.timer = self.create_timer(0.05, self._tick)

    def _parse_int_set(self, value) -> set:
        if isinstance(value, (list, tuple)):
            return {int(v) for v in value}
        text = str(value).strip()
        if not text:
            return set()
        return {int(part.strip()) for part in text.split(',') if part.strip()}

    def _parse_float_list(self, value, default: List[float]) -> List[float]:
        if isinstance(value, (list, tuple)):
            return [float(v) for v in value]
        text = str(value).strip()
        if not text:
            return list(default)
        return [float(part.strip()) for part in text.split(',') if part.strip()]

    def _parse_json_dict(self, value, default: Dict[str, List[int]]) -> Dict[str, List[int]]:
        if isinstance(value, dict):
            return {str(k): [int(i) for i in v] for k, v in value.items()}
        text = str(value).strip()
        if not text:
            return dict(default)
        try:
            loaded = json.loads(text)
            return {str(k): [int(i) for i in v] for k, v in loaded.items()}
        except Exception:
            self.get_logger().warning('Failed to parse anchor_masks_json; using defaults')
            return dict(default)

    def _setup_depthai(self):
        if not self.blob_path:
            self.get_logger().warning('oakd_yolo_safety enabled but blob_path is empty; detector will stay idle')
            return
        if not os.path.exists(self.blob_path):
            self.get_logger().warning(f'YOLO blob path does not exist: {self.blob_path}; detector will stay idle')
            return

        try:
            import depthai as dai
        except Exception as exc:
            self.get_logger().warning(f'depthai is not available: {exc}; detector will stay idle')
            return

        self.depthai = dai
        pipeline = dai.Pipeline()

        cam = pipeline.createColorCamera()
        cam.setBoardSocket(dai.CameraBoardSocket.CAM_A)
        cam.setPreviewSize(self.preview_width, self.preview_height)
        cam.setInterleaved(False)
        cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        cam.setFps(self.camera_fps)

        nn = pipeline.createYoloDetectionNetwork()
        nn.setBlobPath(self.blob_path)
        nn.setConfidenceThreshold(self.confidence_threshold)
        nn.setIouThreshold(self.iou_threshold)
        nn.setNumClasses(self.num_classes)
        nn.setCoordinateSize(self.coordinate_size)
        nn.setAnchors(self.anchors)
        nn.setAnchorMasks(self.anchor_masks)

        cam.preview.link(nn.input)

        xout = pipeline.createXLinkOut()
        xout.setStreamName('detections')
        nn.out.link(xout.input)

        try:
            self.device = dai.Device(pipeline)
            self.detections_queue = self.device.getOutputQueue(name='detections', maxSize=4, blocking=False)
            self.get_logger().info(f'DepthAI YOLO detector started using {self.blob_path}')
        except Exception as exc:
            self.get_logger().warning(f'Failed to start DepthAI pipeline: {exc}; detector will stay idle')
            self.device = None
            self.detections_queue = None

    def _tick(self):
        hazard = False
        summaries = []

        if self.detections_queue is not None:
            packet = self.detections_queue.tryGet()
            if packet is not None:
                hazard, summaries = self._interpret_detections(packet.detections)
                if hazard:
                    self.last_hazard_time = self.get_clock().now()
                if summaries:
                    summary = '; '.join(summaries)
                    self.last_summary = summary
                    msg = String()
                    msg.data = summary
                    self.summary_pub.publish(msg)

        if self.last_hazard_time is not None:
            elapsed = (self.get_clock().now() - self.last_hazard_time).nanoseconds / 1e9
            if elapsed <= self.hold_time_s:
                hazard = True

        hazard_msg = Bool()
        hazard_msg.data = hazard
        self.hazard_pub.publish(hazard_msg)

        if hazard and self.stop_on_detection:
            self.cmd_vel_pub.publish(self._zero_twist())

    def _interpret_detections(self, detections):
        hazard = False
        summaries = []
        for det in detections:
            label_id = int(det.label)
            conf = float(det.confidence)
            xmin = float(det.xmin)
            ymin = float(det.ymin)
            xmax = float(det.xmax)
            ymax = float(det.ymax)
            area = max(0.0, (xmax - xmin) * (ymax - ymin))
            cx = (xmin + xmax) / 2.0
            cy = (ymin + ymax) / 2.0

            center_hit = abs(cx - 0.5) <= self.center_x_ratio / 2.0 and abs(cy - 0.5) <= self.center_y_ratio / 2.0
            area_hit = area >= self.min_area_ratio
            label_hit = not self.hazard_label_ids or label_id in self.hazard_label_ids

            if label_hit and (center_hit or area_hit):
                hazard = True

            summaries.append(
                f'class_{label_id}@{conf:.2f} area={area:.3f} center={cx:.2f},{cy:.2f}'
            )

        return hazard, summaries

    def _zero_twist(self):
        twist = Twist()
        twist.linear.x = 0.0
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = 0.0
        return twist


def main(args=None):
    rclpy.init(args=args)
    node = OakdYoloSafetyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
