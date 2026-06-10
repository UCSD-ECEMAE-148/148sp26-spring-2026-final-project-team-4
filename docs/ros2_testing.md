# ROS 2 Testing Guide

This document covers how to bring up and verify each hardware sensor, and how to run and validate the SLAM stack.

**Before any ROS 2 operations, source the environment:**

```bash
source /opt/ros/jazzy/setup.bash
source ~/scout-survey-rover/slam_ros2_ws/install/setup.bash
```

## 1. Build the workspace

After making source changes, rebuild with symlink install so edits to Python nodes and launch files take effect immediately without rebuilding:

```bash
cd ~/scout-survey-rover/slam_ros2_ws
colcon build --symlink-install
source install/setup.bash
```

To rebuild only changed packages:

```bash
colcon build --packages-select xiao_serial_bridge robot_slam --symlink-install
```

To start fresh (e.g. after switching ROS distros or resolving broken installs):

```bash
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

Never edit `build/` or `install/` directly — they are generated.

## 2. Hardware sensor tests

### LiDAR (LD06)

```bash
ros2 launch ucsd_robocar_sensor2_pkg lidar_ld06.launch.py
```

Verify:

```bash
ros2 topic hz /scan           # expect ~10 Hz
ros2 topic echo /scan --once  # check angle_min, angle_max, ranges length
```

The LD06 scans 0→2π and outputs 449–453 beams per scan (variable). The `scan_relay_node` normalises this downstream — no action needed here.

Other available LiDAR launch files:

```bash
ros2 launch ucsd_robocar_sensor2_pkg lidar_livox.launch.py
ros2 launch ucsd_robocar_sensor2_pkg lidar_rp.launch.py
ros2 launch ucsd_robocar_sensor2_pkg lidar_sicktim.launch.py
```

### IMU (XIAO nRF52840 Sense)

The IMU is handled by the custom `xiao_serial_bridge` package, not `razor_imu_9dof`. The bridge reads CSV packets from the XIAO over USB CDC serial, dead-reckons pose, and publishes `/odom` and `/imu`.

```bash
ros2 run xiao_serial_bridge serial_bridge_node
```

The node auto-detects the XIAO by USB VID/PID (0x2886:0x8045) if `/dev/ttyACM0` is not found. If the port changes after a replug, it recovers automatically.

Verify:

```bash
ros2 topic hz /odom   # expect ~50 Hz
ros2 topic hz /imu    # expect ~50 Hz
ros2 topic echo /odom --once
```

If `/odom` does not appear within 10 s, replug the XIAO USB cable and wait 5 s for the CDC port to reappear — the bridge will reconnect automatically.

### Camera

```bash
ros2 launch ucsd_robocar_sensor2_pkg camera_oakd.launch.py
# or
ros2 launch ucsd_robocar_sensor2_pkg camera_webcam.launch.py
```

Verify:

```bash
ros2 topic list | grep camera
ros2 topic echo /camera/color/image_raw --once
```

## 3. SLAM stack

### Architecture overview

```
[LD06 LiDAR]  →  /scan  →  scan_relay_node  →  /scan_fixed (300 beams, 250° front FOV)
                                                        ↓
[XIAO IMU]  →  /odom, /imu  →  ekf_local_node  →  odom→base_link TF (10 Hz)
                                                        ↓
[robot_state_publisher]  →  base_link→laser TF (static)
                                                        ↓
                                              slam_toolbox (online async)
                                                        ↓
                                              /map  +  map→odom TF
```

### Launch sequence

Start each in a separate terminal in this order:

**Terminal 1 — LiDAR:**

```bash
source /opt/ros/jazzy/setup.bash
source ~/scout-survey-rover/slam_ros2_ws/install/setup.bash
ros2 launch ucsd_robocar_sensor2_pkg lidar_ld06.launch.py
```

**Terminal 2 — IMU bridge:**

```bash
source /opt/ros/jazzy/setup.bash
source ~/scout-survey-rover/slam_ros2_ws/install/setup.bash
ros2 run xiao_serial_bridge serial_bridge_node
```

**Terminal 3 — Stage 1 SLAM launch:**

```bash
source /opt/ros/jazzy/setup.bash
source ~/scout-survey-rover/slam_ros2_ws/install/setup.bash
ros2 launch robot_slam launch_stage_1.launch.py
```

The launch starts: `scan_relay_node`, `ekf_local_node`, `robot_state_publisher`, and `slam_toolbox` (with a 10 s startup delay to allow the EKF to publish TF first).

Do not start a manual `scan_relay_node` before step 3 — the launch starts its own. Running two at once sends interleaved scans with mismatched beam counts to slam_toolbox.

### Verify the stack

**TF chain** (expect odom→base_link and base_link→laser within 15 s of launch):

```bash
ros2 topic echo /tf --once | grep -E "frame_id|child_frame"
ros2 topic echo /tf_static --once | grep child_frame
```

**Sensor rates:**

```bash
ros2 topic hz /scan_fixed          # expect ~10 Hz, 300 beams, ±125°
ros2 topic hz /odometry/filtered   # expect 10 Hz (EKF output)
```

**Map — use the service, not topic hz:**

`/map` is published with TRANSIENT_LOCAL QoS. `ros2 topic hz /map` always returns "not published" for subscribers that join after the initial publish. Use the service instead:

```bash
ros2 service call /slam_toolbox/dynamic_map nav_msgs/srv/GetMap
```

A valid response has `width` and `height` > 0 and non-empty `data`. If it returns an empty map, wait 30 s and retry — slam_toolbox may still be initialising.

**Expected log output** in the launch terminal (look for these in order):

```
[scan_relay_node]: Relaying /scan → /scan_fixed | 300 beams | FOV 250°
[slam_toolbox]: Configuring
[slam_toolbox]: Activating
[slam_toolbox]: Message Filter dropping message: ...   ← one drop at startup is normal
Registering sensor: [Custom Described Lidar]          ← first scan accepted
```

One message-filter drop at slam_toolbox startup is expected — the TF buffer is momentarily empty when the node first activates. Repeated drops (more than 2–3 in a row) indicate a broken TF chain.

### Visualize in RViz

Pass `use_rviz:=true` to the Stage 1 launch to open RViz with the mapping layout:

```bash
ros2 launch robot_slam launch_stage_1.launch.py use_rviz:=true
```

This loads `robot_slam/rviz/mapping.rviz` automatically. RViz shows:
- The live `/map` occupancy grid
- The `odom→base_link→laser` TF chain
- The `/scan_fixed` laser scan overlay

RViz can run on the Pi itself (over a remote desktop / X11 session), but it is CPU-heavy. If SLAM becomes unstable when RViz is open, run RViz on a separate machine instead:

```bash
# On the remote machine (same ROS_DOMAIN_ID, same network):
export ROS_DOMAIN_ID=0
source /opt/ros/jazzy/setup.bash
rviz2 -d <path-to>/robot_slam/rviz/mapping.rviz
```

### Save the map

When mapping is complete:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/scout-survey-rover/slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map
```

This writes `stage1_map.yaml` and `stage1_map.pgm`.

## 4. Keyboard teleop (Stage 1 manual driving)

The keyboard teleop stack uses the `vesc_driver` package directly — no `pyvesc`. The VESC must be connected on `/dev/ttyACM1` and servo output must be enabled in VESC Tool before use.

### Architecture

```
keyboard_teleop_node  →  /ackermann_cmd  →  ackermann_to_vesc_node
                                                     ↓
                          commands/motor/speed + commands/servo/position
                                                     ↓
                                           vesc_driver_node  →  /dev/ttyACM1
```

### Launch the VESC driver

```bash
ros2 launch ucsd_robocar_control2_pkg keyboard_teleop.launch.py
```

Confirm the VESC connected:

```bash
ros2 topic hz /sensors/core   # expect ~50 Hz
```

### Start keyboard control (separate terminal)

```bash
ros2 run ucsd_robocar_control2_pkg keyboard_teleop_node
```

Keys: `w`/`s` = forward/backward, `a`/`d` = steer left/right, `space` = stop, `q` = quit.
Speed step/steer step adjustable with `r`/`f` and `e`/`c` at runtime.

### Steering calibration

If the wheels don't steer or are off-center, tune these two values in `ucsd_robocar_control2_pkg/config/keyboard_teleop_config.yaml`:

```yaml
steering_angle_to_servo_gain: -0.6    # flip sign if steering is reversed
steering_angle_to_servo_offset: 0.5   # servo value (0–1) that centers the wheels
```

Find the correct offset by publishing directly to the VESC driver:

```bash
ros2 run vesc_driver vesc_driver_node --ros-args -p port:=/dev/ttyACM1
ros2 topic pub /commands/servo/position std_msgs/msg/Float64 "data: 0.5" --once
# adjust data: value until wheels are visually straight → that value is your offset
```

Then calculate gain:

```
gain = (servo_full_left - offset) / max_steering_angle_radians
```

Rebuild after editing the config:

```bash
colcon build --packages-select ucsd_robocar_control2_pkg
```

## 5. Diagnostics

Check all nodes are alive:

```bash
ros2 node list
```

Expected nodes for Stage 1: `/ld06_node`, `/serial_bridge_node`, `/scan_relay_node`, `/ekf_local_node`, `/robot_state_publisher`, `/slam_toolbox`.

Check for errors:

```bash
grep -E "ERROR|process has died|Caught exception|Message Filter dropping" /tmp/launch_out.txt
```

If `ekf_node` is not found, the system-level `robot_localization` package is being used (correct). If a locally-built version was broken, remove it:

```bash
rm -rf ~/scout-survey-rover/slam_ros2_ws/build/robot_localization \
       ~/scout-survey-rover/slam_ros2_ws/install/robot_localization
```

## 6. What is intentionally out of scope here

- Nav2 autonomous navigation (disabled in Stage 1 by default, enable with `use_nav2:=true`)
- Frontier exploration
- Mission reporting backend
