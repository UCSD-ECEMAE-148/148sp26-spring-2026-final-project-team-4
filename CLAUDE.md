# xiao_serial_bridge — ROS 2 Package

## Overview

A single ROS 2 package (`xiao_serial_bridge`) that bundles both the **XIAO nRF52840 Sense**
Arduino firmware and the **ROS 2 serial bridge node** together. Drop this package into any
existing `ros2_ws/src/` and build with colcon — no separate repo or workspace needed.

Hardware: XIAO reads the onboard **LSM6DS3TR-C IMU**, dead-reckons pose (x, y, θ), and streams
CSV over USB serial. The ROS 2 node reads that serial stream and publishes `nav_msgs/Odometry`
and `sensor_msgs/Imu`.

---

## Architecture

```
[XIAO nRF52840 Sense]
  └─ LSM6DS3TR-C IMU (I2C, 0x6A)
  └─ Dead-reckoning @ ~100 Hz
  └─ USB Serial → CSV packet @ ~50 Hz
         │
         ▼ /dev/ttyACM0
[ROS 2 Host — Ubuntu 22.04, Humble]
  └─ serial_bridge_node (rclpy)
       ├─ /odom  (nav_msgs/Odometry)
       ├─ /imu   (sensor_msgs/Imu)
       └─ TF: odom → base_link
```

---

## Package Layout

```
xiao_serial_bridge/               ← drop into ros2_ws/src/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
│   └── xiao_serial_bridge
├── xiao_serial_bridge/
│   ├── __init__.py
│   └── serial_bridge_node.py
└── firmware/
    └── xiao_odom/
        ├── xiao_odom.ino         # Arduino sketch
        └── imu_integration.h     # IMU read + dead-reckoning helpers
```

The `firmware/` directory is non-ROS — colcon ignores it. It lives here purely for co-location.

---

## Hardware

- **MCU**: XIAO nRF52840 Sense (ARM Cortex-M4 @ 64 MHz)
- **IMU**: LSM6DS3TR-C (onboard) — I2C address `0x6A`
- **Board package**: `Seeed nRF52 Boards` in Arduino IDE / arduino-cli
- **IMU library**: `Seeed_Arduino_LSM6DS3`

---

## Serial Packet Format

One line per sample, newline-terminated:

```
SEQ,TIMESTAMP_MS,AX,AY,AZ,GX,GY,GZ,X,Y,THETA,VX,VTHETA\n
```

| Field | Unit |
|-------|------|
| SEQ | integer counter |
| TIMESTAMP_MS | ms since boot |
| AX, AY, AZ | m/s² |
| GX, GY, GZ | rad/s |
| X, Y | meters |
| THETA | radians |
| VX | m/s |
| VTHETA | rad/s |

---

## Firmware Conventions (`firmware/`)

- **IMU ODR**: 104 Hz; **output rate**: 50 Hz (every other sample)
- **Dead-reckoning**: Euler integration — gyro Z → θ; accel X/Y rotated to world frame → x, y
- **Gyro bias calibration**: average first 200 samples at startup (board held still, ~2 s block)
- **Units**: Always SI inside the sketch — no unit conversion in the bridge node
- **No blocking calls** in `loop()` — use `millis()` for timing
- **Libraries**: `LSM6DS3.h`, `Wire.h`

```cpp
// xiao_odom.ino — top-level structure
#include "LSM6DS3.h"
#include "Wire.h"
#include "imu_integration.h"

LSM6DS3 imu(I2C_MODE, 0x6A);
ImuState state;

void setup() {
  Serial.begin(115200);
  imu.begin();
  calibrateGyroBias(imu, state, 200);
}

void loop() {
  // Non-blocking 50 Hz: read IMU → integrate → print CSV
}
```

---

## ROS 2 Node Conventions (`xiao_serial_bridge/`)

- **Node name**: `serial_bridge_node`
- **Language**: Python 3, `rclpy`
- **Serial library**: `pyserial` (must be installed: `pip install pyserial`)
- **ROS 2 distro**: Humble on Ubuntu 22.04

### Parameters

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `serial_port` | string | `/dev/ttyACM0` | USB CDC device path |
| `baud_rate` | int | `115200` | Baud (ignored by CDC, set for compatibility) |
| `odom_frame_id` | string | `odom` | Parent frame for odometry |
| `base_frame_id` | string | `base_link` | Child frame |
| `publish_tf` | bool | `true` | Broadcast odom → base_link TF |

### Topics Published

| Topic | Type | Notes |
|-------|------|-------|
| `/odom` | `nav_msgs/Odometry` | Stamped with `node.get_clock().now()` |
| `/imu` | `sensor_msgs/Imu` | Same timestamp as `/odom` |

### Covariance Convention

Diagonal-only, row-major 6×6 flattened. Do not leave as all-zeros — breaks EKF nodes.

```python
pose_covariance = [0.0] * 36
pose_covariance[0]  = 0.05   # x
pose_covariance[7]  = 0.05   # y
pose_covariance[35] = 0.02   # yaw

twist_covariance = [0.0] * 36
twist_covariance[0]  = 0.01  # vx
twist_covariance[35] = 0.01  # vtheta
```

### Threading Strategy

- Serial reads in a **background `threading.Thread`** — never block `rclpy.spin()`
- Parsed packets written to a `queue.Queue`
- ROS 2 **timer callback** drains the queue and publishes
- If a serial line fails to parse: log a warning, skip the packet, do not crash

---

## Build & Run

```bash
# From your workspace root
cd ~/ros2_ws
colcon build --packages-select xiao_serial_bridge
source install/setup.bash

# Run (default params)
ros2 run xiao_serial_bridge serial_bridge_node

# Override serial port
ros2 run xiao_serial_bridge serial_bridge_node \
  --ros-args -p serial_port:=/dev/ttyUSB0
```

### Flash Firmware

```bash
arduino-cli compile \
  --fqbn Seeeduino:nrf52:xiaonRF52840Sense \
  src/xiao_serial_bridge/firmware/xiao_odom

arduino-cli upload \
  --fqbn Seeeduino:nrf52:xiaonRF52840Sense \
  --port /dev/ttyACM0 \
  src/xiao_serial_bridge/firmware/xiao_odom
```

### Verify

```bash
ros2 topic echo /odom
ros2 topic echo /imu
ros2 run tf2_tools view_frames    # confirm odom → base_link
```

---

## Development Notes

- **nRF52840 USB CDC quirk**: Serial port disappears and reappears after upload — wait ~3 s before the bridge node opens the port. Add a retry loop with backoff in the node.
- **IMU drift**: Dead-reckoning without wheel encoders drifts quickly. This is a foundation for `robot_localization` EKF fusion, not a standalone nav solution. Keep covariance values honest.
- **future micro-ROS path**: `imu_integration.h` and all dead-reckoning math are reusable — only the CSV serial output section needs replacing with micro-ROS publisher calls.

## Out of Scope

- Wheel encoder integration (future)
- EKF/UKF sensor fusion (use `robot_localization`)
- micro-ROS transport implementation
- RViz2 launch file
