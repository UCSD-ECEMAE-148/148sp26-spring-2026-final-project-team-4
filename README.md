# WORK IN PROGRESS (not submission ready)

---

# <div align="center">Scout Survey Rover w/ Mission Report Generation</div>
### <div align="center"> ECE/MAE 148 Final Project </div>
#### <div align="center"> Team4 Spring 2026 </div>
![image](https://raw.githubusercontent.com/UCSD-ECEMAE-148/148sp26-spring-2026-final-project-team-4/main/docs/media/car.jpg)

## Team Members

Evan Chou - ECE, Machine Learning and Controls

Kenneth Foead - MAE

Evan Robert - ECE

Thejo Tattala - MAE

## Abstract

Our project aimed to develop a SLAM and autonomous navigation system capable of fusing multiple sensors for mapping a full indoor room and localizing the robot's position. With telemetry data and logging from the ROS 2 system, we also aimed to expose the robot through a web-based controller and dashboard for remote control, and to generate mission reports from its exploration data.

## What We Promised
### Must Have
* Integrate SLAM and autonomous navigation into the ROS2 system through pre-built packages
* Conduct mission exploration and publish reports of findings into a full-stack website
* Rotational camera for scanning and examining surrounding environment at wider angles

### Nice to Have
* Computer vision and object detection/avoidance with standard YOLO model
* LLM-based summarization of reported findings through on-board edge inference
* Cosmetic additions such as LED strip for indicating exploration status 

## Accomplishments

- Successfully launched visual SLAM with an Extended Kalman Filter for robot localization
- Integrated a web controller and dashboard for robot control via ROS 2 socket bridges
- Configured IMU odometry firmware and ROS 2 driver for the Seeed XIAO nRF52840 Sense
- Added rotational camera and LED strip features, and coded firmware for operating them via serial commands

## Challenges

- Calibrating and finetuning parameters for EKF-related configurations, including VESC and IMU odometry
- Hardware limitations with CPU and RAM power forced us to lower frequencies of data publishing and perform timed launching
- Integrating Nav2 for autonomous navigation, which was not able to be accomplished during this time

## Final Project Videos

[Final Presentation Slides](https://docs.google.com/presentation/d/100er0TgurMbT8JcgmrrsiwRIkXcWnn7BoJnauJ2WcTg/edit?usp=sharing)

TBD

## Documentation

- [Project Reproduction guide](docs/reproduction.md) if you are interested in reproducing our project.
- [ROS 2 testing guide](docs/ros2_testing.md) for camera, IMU, LiDAR, and SLAM/RViz2 checks.
- [Stage 1 verification & troubleshooting reference](docs/full_stage_testing.md) for confirming the mapping stack is healthy, diagnosing failures, and saving maps. Launch the full stack with `./stage1_start.sh` (or `--full` to also start the survey camera and mission report web server).
- [Software Systems documentation](docs/software_systems.md) for learning about our software architectures and systems.
- [Robot Hardware documentation](docs/robot_hardware.md) for learning about our improved hardware components, including electrical and mechanical revamps.

## Acknowledgements

Special thank you to Professor Silberman and TAs Jose Castillo and Winston Chou for facilitating this course!

README.md Format, reference to [winter-2024-final-project-team-7](https://github.com/UCSD-ECEMAE-148/winter-2024-final-project-team-7)

## Contacts

* Evan Chou - e3chou@ucsd.edu | evan.chou@live.com | [LinkedIn](https://www.linkedin.com/in/evanjchou/)
* Kenneth Foead - kfoead@ucsd.edu | | [LinkedIn](https://www.linkedin.com/in/kenneth-hubert-foead/)
* Evan Robert - erobert@ucsd.edu
* Thejo Tattala - ttattala@ucsd.edu | | [LinkedIn](https://www.linkedin.com/in/thejo-tattala-b719b2271/)
