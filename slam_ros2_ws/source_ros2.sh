#!/usr/bin/env bash

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function source_ros2_pkg() {
  source /opt/ros/${ROS_DISTRO}/setup.bash
}

function source_ros2() {
  source_ros2_pkg
  cd "$WORKSPACE_ROOT"
  source install/setup.bash
}

function build_ros2() {
  cd "$WORKSPACE_ROOT"
  rm -rf build/ install/ log/
  colcon build
  source install/setup.bash
}

function build_ros2_pkg() {
  cd "$WORKSPACE_ROOT"
  colcon build --packages-select "$@"
  source install/setup.bash
}

complete -W "robot_slam" build_ros2_pkg
