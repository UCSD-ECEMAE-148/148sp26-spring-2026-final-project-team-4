#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /home/pi/scout-survey-rover/slam_ros2_ws/install/setup.bash

pkill -9 -f "serial_bridge_node|ekf_node|slam_toolbox|robot_state_publisher|scan_relay_node" 2>/dev/null || true
sleep 2

ros2 run xiao_serial_bridge serial_bridge_node 2>/dev/null &
sleep 4

ros2 launch robot_slam launch_stage_1.launch.py > /tmp/launch_out.txt 2>&1 &
LAUNCH_PID=$!

sleep 25

echo "=== /scan active? ==="
timeout 4 ros2 topic hz /scan 2>&1 | grep -E "rate|WARNING"

echo "=== /scan_fixed active? ==="
timeout 4 ros2 topic hz /scan_fixed 2>&1 | grep -E "rate|WARNING"

echo "=== /tf data ==="
timeout 3 ros2 topic echo /tf --once 2>&1 | head -30

echo "=== /tf_static ==="
timeout 3 ros2 topic echo /tf_static --once 2>&1 | head -15

echo "=== last 15 launch lines ==="
tail -15 /tmp/launch_out.txt

kill $LAUNCH_PID 2>/dev/null
wait 2>/dev/null
