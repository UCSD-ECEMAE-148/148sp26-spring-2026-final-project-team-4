#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /home/pi/scout-survey-rover/slam_ros2_ws/install/setup.bash

ros2 run xiao_serial_bridge serial_bridge_node 2>/dev/null &
BRIDGE=$!
sleep 4

ros2 launch robot_slam launch_stage_1.launch.py 2>&1 | grep --line-buffered -E "process has died|ERROR" &
LAUNCH=$!

sleep 40

echo "=== nodes ==="
ros2 node list 2>&1 | grep -Ev "transform_listener|launch_ros|joy|teleop|vesc|ld06"

echo "=== topic hz ==="
for topic in /odom /scan /odometry/filtered /map; do
  rate=$(timeout 4 ros2 topic hz $topic 2>&1 | grep "average rate" | awk '{print $3}')
  echo "  $topic: ${rate:-NOT PUBLISHING}"
done

echo "=== TF frames ==="
cd /tmp && timeout 5 ros2 run tf2_tools view_frames 2>/dev/null
grep " -> " /tmp/frames.gv 2>/dev/null | sort | sed 's/.*"\(.*\)" -> "\(.*\)".*/  \1 -> \2/'

kill $LAUNCH $BRIDGE 2>/dev/null
wait 2>/dev/null
