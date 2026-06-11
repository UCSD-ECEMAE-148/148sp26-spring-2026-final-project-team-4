# <div align="center">Software Systems</div>

## Overall Architecture

![image](https://raw.githubusercontent.com/UCSD-ECEMAE-148/148sp26-spring-2026-final-project-team-4/main/docs/media/rosgraph_nodes_only.png)

## Native Ubuntu 24.04 and ROS 2 Jazzy Distro

Instead of using Docker containers, we decided to re-flash the Raspberry Pi with Ubuntu 24.04 and run ROS 2 Jazzy natively on its compatible OS. This enabled us to have easier development with the RPi, however, one of the challenges was that we had to install all dependencies that the UCSD RoboCar Hub2 package used in previous assignments.

## IMU Odometry Firmware and ROS2 Driver

- 10s calibration and bias error correction

## SLAM (Simultaneous Localization and Mapping)

- EKF with IMU and VESC odom
- 2D LiDAR
- SLAM Toolbox

## Servo + LED Strip Firmware and Serial Communication

- Arduino stuff
- serial commands
- ros2 -> pico bridge

## WebSocket Communication to Website Back-End

- web socket bridges
- backend stuff