# Manual Stage 1 Logitech SLAM Guide

This guide covers the current workflow: use a Logitech controller to drive the rover manually while the SLAM stack builds a map of the indoor room.

The autonomous frontier explorer and Nav2 mission flow are intentionally out of the active workflow for now. The frontier package remains in the workspace, but this guide does not use it.

## Prerequisites

- ROS 2 installed and sourced for your distro.
- Workspace built at least once.
- Logitech controller connected as `/dev/input/js0`.
- Camera, LiDAR, IMU, and motor control available on the rover.

## 1. Start the hardware and controller stack

Use the hub2 packages as the teleop pattern:

```bash
ros2 launch ucsd_robocar_control2_pkg manual_joy_control_launch.launch.py
ros2 launch ucsd_robocar_actuator2_pkg vesc_twist.launch.py
```

This is the key pattern from `ucsd_robocar_hub2`:

- `joy` reads the Logitech controller.
- `teleop_twist_joy` converts joystick input into drive commands.
- `vesc_twist` consumes `/cmd_vel` and drives the car.

Start the sensors you need for mapping. Example commands:

```bash
ros2 launch ucsd_robocar_sensor2_pkg camera_oakd.launch.py
ros2 launch ucsd_robocar_sensor2_pkg lidar_ld06.launch.py
ros2 launch ucsd_robocar_sensor2_pkg imu_artemis.launch.py
```

If your hardware uses a different camera or LiDAR, pick the matching launch file from `ucsd_robocar_sensor2_pkg`.

## 2. Start the SLAM stack

In a separate terminal:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash
ros2 launch robot_slam launch_stage_1.launch.py use_rviz:=true
```

The Stage 1 launch now just starts SLAM and RViz support. It does not launch frontier exploration or autonomous navigation.

## 3. Drive and map

Use the Logitech controller to drive the rover around the room while SLAM is running. Watch these topics:

```bash
ros2 topic list | grep -E '^/map$|^/scan$|^/tf$|^/odom$|^/cmd_vel$'
ros2 topic hz /map
ros2 topic hz /scan
ros2 topic hz /odom
```

In RViz, confirm:

- The occupancy grid updates as the robot moves.
- Laser scans align with obstacles.
- TF remains stable from `map` to `odom` to `base_link`.

## 4. Save the map

When the room is covered well enough:

```bash
ros2 run nav2_map_server map_saver_cli -f src/robot_slam/ros_data/maps/custom/stage1_map
```

Expected files:

- `slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map.yaml`
- `slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map.pgm`

## 5. What is intentionally out of scope now

- Frontier exploration planner
- Autonomous room coverage
- Nav2 mission handoff and backend transfer workflow
- Oak-D YOLO object safety layer during Stage 1

Those can come back later, but the current path is manual drive first, SLAM second.
