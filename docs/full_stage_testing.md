# Stage 1 End-to-End Testing Guide

This guide walks through a complete Stage 1 SLAM test: bring up all hardware, verify each subsystem, confirm the map is building, drive the rover to collect a map, and save it.

Stage 1 uses manual keyboard control for map collection. Autonomous navigation (Nav2) is deliberately disabled to keep CPU headroom on the Pi.

## Prerequisites

- ROS 2 Jazzy sourced
- `slam_ros2_ws` built with `colcon build --symlink-install`
- LD06 LiDAR connected (USB)
- XIAO nRF52840 Sense connected (USB CDC, `/dev/ttyACM0` or auto-detected)
- VESC motor controller powered and connected (`/dev/ttyACM1`)
- VESC servo output enabled in VESC Tool (App Settings → General → Use Servo Output → Write App Configuration)

## Step 1 — Source the environment (every terminal)

```bash
source /opt/ros/jazzy/setup.bash
source ~/scout-survey-rover/slam_ros2_ws/install/setup.bash
```

## Step 2 — Start the LiDAR

```bash
ros2 launch ucsd_robocar_sensor2_pkg lidar_ld06.launch.py
```

**Verify** (new terminal):

```bash
ros2 topic hz /scan
# Expected: ~10 Hz
```

If `/scan` does not appear, check the USB connection and re-run the launch.

## Step 3 — Start the IMU bridge

```bash
ros2 run xiao_serial_bridge serial_bridge_node
```

**Verify** (new terminal):

```bash
ros2 topic hz /odom
# Expected: ~50 Hz
```

If `/odom` does not appear within 10 s:
1. Replug the XIAO USB cable
2. Wait 5 s — the bridge reconnects automatically
3. Watch the bridge terminal for `Opened serial port /dev/ttyACMx`

## Step 4 — Start the SLAM stack

```bash
ros2 launch robot_slam launch_stage_1.launch.py
```

Do not start a manual `scan_relay_node` before this — the launch starts its own. Two `scan_relay_node` instances will send mismatched beam counts to slam_toolbox.

**What this starts:**

| Node | Role |
|------|------|
| `scan_relay_node` | Crops LD06 to 250° front FOV, resamples to 300 beams, publishes `/scan_fixed` |
| `ekf_local_node` | Fuses `/odom` + `/imu`, publishes `odom→base_link` TF at 10 Hz |
| `robot_state_publisher` | Publishes static TF: `base_link→laser`, `base_link→camera_link` |
| `slam_toolbox` | Online async mapping on `/scan_fixed`; starts 10 s after launch to let EKF stabilise |

**Expected log output** (in order, within 30 s):

```
[scan_relay_node]: Relaying /scan → /scan_fixed | 300 beams | FOV 250°
[ekf_node]: ... (no errors expected)
[robot_state_publisher]: Robot initialized
[slam_toolbox]: Configuring
[slam_toolbox]: Activating
[slam_toolbox]: Message Filter dropping message: ...   ← one drop at t=0 is normal
Registering sensor: [Custom Described Lidar]           ← first scan accepted; map building starts
```

One message-filter drop at startup is expected. If drops repeat every few seconds, the TF chain is broken — see Diagnostics below.

## Step 5 — Verify the full TF chain

```bash
ros2 topic echo /tf --once | grep -E "frame_id|child_frame"
ros2 topic echo /tf_static --once | grep child_frame
```

**Expected:**

- `/tf`: `odom → base_link` (from EKF)
- `/tf_static`: `base_link → laser`, `base_link → camera_link`, `base_link → base_imu_link`

If `odom → base_link` is missing, the EKF is not publishing. Check `/odom` and `/imu` are alive, then check the bridge terminal for errors.

## Step 6 — Verify the map is building

`/map` uses TRANSIENT_LOCAL QoS — `ros2 topic hz /map` always shows "not published" regardless of whether the map is real. Use the service:

```bash
ros2 service call /slam_toolbox/dynamic_map nav_msgs/srv/GetMap
```

**Valid response**: `width` and `height` are > 0; `data` contains a mix of `-1` (unknown), `0` (free), and `100` (occupied) values.

**Empty response** (`width: 0`): slam_toolbox has not yet accepted a scan. Wait 30 s and retry. If still empty after 60 s, see Diagnostics.

```bash
# Cross-check topic rates
ros2 topic hz /scan_fixed          # ~10 Hz, 300 beams
ros2 topic hz /odometry/filtered   # 10 Hz
ros2 node list                     # all 6 nodes should be present
```

## Step 6b — (Optional) Visualize in RViz

To open RViz alongside the SLAM stack, add `use_rviz:=true` to the Step 4 launch command:

```bash
ros2 launch robot_slam launch_stage_1.launch.py use_rviz:=true
```

This loads `robot_slam/rviz/mapping.rviz` and shows the live occupancy grid, TF chain, and `/scan_fixed` overlay.

> **CPU warning**: RViz is heavy on the Pi. If the map stops updating or EKF lag increases, close RViz and use the service-call method in Step 6 instead. Alternatively, run RViz on a separate machine on the same network (same `ROS_DOMAIN_ID`):
>
> ```bash
> export ROS_DOMAIN_ID=0
> source /opt/ros/jazzy/setup.bash
> rviz2 -d <path-to>/robot_slam/rviz/mapping.rviz
> ```

## Step 7 — Start the VESC driver

In a new terminal:

```bash
ros2 launch ucsd_robocar_control2_pkg keyboard_teleop.launch.py
```

This starts `ackermann_to_vesc_node` and `vesc_driver_node` pointed at `/dev/ttyACM1`. The driver connects to the VESC and enters operating mode within a few seconds — look for:

```
[vesc_driver_node]: Connected to VESC with firmware version X.X
```

**Verify** the driver is live:

```bash
ros2 topic hz /sensors/core   # expect ~50 Hz VESC telemetry
```

## Step 8 — Start keyboard control

In a separate terminal (this terminal captures keyboard input):

```bash
ros2 run ucsd_robocar_control2_pkg keyboard_teleop_node
```

| Key | Action |
|-----|--------|
| `w` | Forward (accumulates by 0.05 m/s per press, max 0.5 m/s) |
| `s` | Backward |
| `a` | Steer left |
| `d` | Steer right |
| `space` | Stop immediately (zero speed + center steering) |
| `r` / `f` | Increase / decrease speed step |
| `e` / `c` | Increase / decrease steer step |
| `q` | Quit |

**Verify** commands are flowing:

```bash
ros2 topic hz /ackermann_cmd   # should show ~10 Hz when keys are pressed
```

## Step 9 — Drive and map

Drive slowly through the area. SLAM adds a new pose node when the robot moves **≥ 0.1 m** or rotates **≥ 0.2 rad** — short, slow movements may not trigger updates.

Watch the map grow via the service:

```bash
watch -n 5 "ros2 service call /slam_toolbox/dynamic_map nav_msgs/srv/GetMap 2>&1 | grep -E 'width|height'"
```

Good signs:
- `width` and `height` grow as new area is covered
- No new "Message Filter dropping" lines appear in the launch terminal

## Step 10 — Save the map

When coverage is complete:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/scout-survey-rover/slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map
```

Verify the files were created:

```bash
ls -lh ~/scout-survey-rover/slam_ros2_ws/src/robot_slam/ros_data/maps/custom/
# stage1_map.yaml  stage1_map.pgm
```

## Diagnostics

### TF chain is broken (repeated message-filter drops)

```bash
ros2 topic echo /tf --once | grep "frame_id\|child_frame"
```

- `odom → base_link` missing → EKF not publishing. Check `/odom` and `/imu` rates.
- `base_link → laser` missing → robot_state_publisher crashed. Check the launch terminal.

### slam_toolbox says "LaserRangeScan contains X readings, expected Y"

Two `scan_relay_node` instances are running. Kill all and restart cleanly:

```bash
pkill -9 -f "scan_relay_node|slam_toolbox|ekf_node|robot_state_publisher"
# Then re-run Step 4 only (LiDAR and bridge can stay running)
```

### XIAO bridge not connecting

```bash
# Check if device is visible
ls /dev/ttyACM*
python3 -c "from serial.tools import list_ports; [print(p.device, hex(p.vid or 0), hex(p.pid or 0)) for p in list_ports.comports()]"
# XIAO shows as vid=0x2886 pid=0x8045
```

If the device appears but the bridge still fails, replug the USB cable and wait 5 s.

### Checking all node rates at once

```bash
for t in /scan /scan_fixed /odom /imu /odometry/filtered; do
  rate=$(timeout 4 ros2 topic hz $t 2>&1 | grep "average rate" | awk '{print $3}')
  echo "  $t: ${rate:-NOT PUBLISHING}"
done
```

## What is intentionally out of scope for Stage 1

- Nav2 autonomous navigation (`use_nav2:=true` enables it, but not tested in Stage 1)
- Frontier exploration planner
- Mission reporting backend
- Oak-D YOLO safety layer
