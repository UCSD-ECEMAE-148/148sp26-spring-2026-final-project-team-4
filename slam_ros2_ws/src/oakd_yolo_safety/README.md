# oakd_yolo_safety

DepthAI/Oak-D Lite safety node for Stage 2.

This package runs a YOLO detector on an Oak-D device when given a valid DepthAI blob path.
When a detection is considered hazardous, it publishes:
- `/oakd/yolo/hazard` as `std_msgs/Bool`
- `/oakd/yolo/detections` as `std_msgs/String`
- a zero `geometry_msgs/Twist` to `/cmd_vel` by default
