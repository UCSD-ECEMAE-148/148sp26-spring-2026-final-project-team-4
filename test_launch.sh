#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /home/pi/scout-survey-rover/slam_ros2_ws/install/setup.bash

pkill -9 -f "serial_bridge_node|ekf_node|ekf_filter_node|slam_toolbox|async_slam|robot_state_publisher|scan_relay_node" 2>/dev/null || true
sleep 2

ros2 run xiao_serial_bridge serial_bridge_node 2>/dev/null &
BRIDGE=$!
sleep 4

ros2 launch robot_slam launch_stage_1.launch.py > /tmp/launch_out.txt 2>&1 &
LAUNCH=$!

sleep 60

echo "=== nodes ==="
ros2 node list 2>&1 | grep -Ev "transform_listener|launch_ros|joy|teleop|vesc|ld06"

echo "=== topics ==="
for topic in /odom /scan_fixed /odometry/filtered /map /slam_toolbox/scan_visualization; do
  rate=$(timeout 4 ros2 topic hz $topic 2>&1 | grep "average rate" | awk '{print $3}')
  echo "  $topic: ${rate:-NOT PUBLISHING}"
done

echo "=== TF frames ==="
cd /tmp && timeout 6 ros2 run tf2_tools view_frames 2>/dev/null
cat /tmp/frames.gv 2>/dev/null | grep " -> " | sed 's/.*"\(.*\)" -> "\(.*\)".*/  \1 -> \2/' | sort

echo "=== launch errors ==="
grep -E "ERROR|process has died|Caught exception|Message Filter dropping" /tmp/launch_out.txt | grep -v "^$" | tail -10

kill $LAUNCH $BRIDGE 2>/dev/null
wait 2>/dev/null
