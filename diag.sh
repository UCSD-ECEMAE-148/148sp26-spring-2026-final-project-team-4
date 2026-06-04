#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /home/pi/scout-survey-rover/slam_ros2_ws/install/setup.bash

pkill -9 -f "serial_bridge_node|ekf_node|slam_toolbox|robot_state_publisher|scan_relay_node" 2>/dev/null
sleep 2

ros2 run xiao_serial_bridge serial_bridge_node 2>/dev/null &
sleep 4

ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat /home/pi/scout-survey-rover/slam_ros2_ws/src/robot_slam/urdf/robot.urdf.xacro)" 2>/dev/null &

ros2 run robot_localization ekf_node \
  --ros-args --params-file /home/pi/scout-survey-rover/slam_ros2_ws/install/robot_slam/share/robot_slam/config/ekf_local.yaml 2>&1 | grep --line-buffered -Ev "^$" &

ros2 run xiao_serial_bridge scan_relay_node 2>/dev/null &

sleep 10

echo "=== pre-slam state ==="
for topic in /odom /scan_fixed /odometry/filtered; do
  rate=$(timeout 3 ros2 topic hz $topic 2>&1 | grep "average rate" | awk '{print $3}')
  echo "  $topic: ${rate:-NOT PUBLISHING}"
done

echo "=== TF ==="
cd /tmp && timeout 5 ros2 run tf2_tools view_frames 2>/dev/null
grep " -> " /tmp/frames.gv 2>/dev/null | sed 's/.*"\(.*\)" -> "\(.*\)".*/  \1 -> \2/' | sort

echo "=== starting slam_toolbox ==="
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=/home/pi/scout-survey-rover/slam_ros2_ws/install/robot_slam/share/robot_slam/config/slam_toolbox.yaml \
  use_lifecycle_manager:=false autostart:=true 2>&1 &
SLAM_PID=$!

sleep 20

echo "=== slam alive after 20s? ==="
kill -0 $SLAM_PID 2>/dev/null && echo "YES - still running" || echo "NO - crashed"
ros2 node list 2>&1 | grep -E "slam|ekf"

kill $(jobs -p) 2>/dev/null
wait 2>/dev/null
