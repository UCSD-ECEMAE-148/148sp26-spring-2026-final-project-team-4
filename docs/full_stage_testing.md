# Full Stage 1 + Stage 2 Testing Guide (With Backend Website Data Flow)

This guide validates the complete workflow in two stages:

1. Stage 1: SLAM mapping and map save.
2. Stage 2: Localization + autonomous navigation + mission payload transfer to the backend website server.

## Prerequisites

- Ubuntu with ROS 2 installed (this repo docs target Jazzy).
- Workspace already built at least once.
- Hardware connected and publishing required topics (camera, LiDAR, IMU).
- Optional but recommended: Ollama running for VLM/LLM report generation.

Activate ROS 2 and workspace:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
colcon build --symlink-install
source install/setup.bash
```

If you switch ROS distros, rebuild from a clean state:

```bash
cd slam_ros2_ws
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

## Process Overview and Startup Order

The mission payload transfer path is:

mission_bridge ROS nodes -> rosbridge websocket topic /mission/payload -> website backend mission_receiver -> data/missions/* -> website frontend

### Should the website be started before or after ROS 2 launch?

Recommended for Stage 2 testing: start website backend and frontend before running the mission (before mission end/transfer).

Reason:

- The backend subscribes to /mission/payload through rosbridge and should already be online when mission completion triggers a one-time payload publish.
- The backend can be started either before or after ROS launch because it reconnects automatically, but starting it early reduces risk of missing the transfer window during testing.

## Terminal Layout (Recommended)

Use 5 terminals:

- T1: ROS 2 environment + rosbridge server
- T2: Stage launch file (Stage 1 or Stage 2)
- T3: Website backend (FastAPI)
- T4: Website frontend (Vite)
- T5: ROS 2 test/verification commands

## Stage 1: SLAM Mapping + Frontier Exploration Validation

### 1. Start rosbridge (needed later for mission transfer checks)

In T1:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

Expected:

- WebSocket server available on ws://localhost:9090

### 2. Launch Stage 1 stack (SLAM + mission_bridge + frontier explorer)

In T2:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash
ros2 launch robot_slam launch_stage_1.launch.py use_rviz:=true
```

Current defaults in Stage 1 launch:

- enable_exploration:=true
- exploration_auto_start:=true
- exploration_publish_end_on_complete:=false

Useful overrides:

```bash
# Disable exploration planner for manual mapping only
ros2 launch robot_slam launch_stage_1.launch.py enable_exploration:=false

# Keep exploration off until you send /mission/control start
ros2 launch robot_slam launch_stage_1.launch.py exploration_auto_start:=false
```

### 3. Verify mapping topics and node health

In T5:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash

ros2 topic list | grep -E '^/map$|^/scan$|^/tf$|^/odom$'
ros2 topic hz /map
ros2 topic hz /scan
ros2 topic echo /mission/state --once
```

Expected Stage 1 exploration behavior:

- frontier_explorer selects frontier goals from /map and sends Nav2 goals.
- robot should autonomously move to uncovered areas while map updates.
- return-to-start on mission end works in Stage 1 using TF fallback when /amcl_pose is unavailable.

Extra checks:

```bash
ros2 node list | grep frontier_explorer
ros2 topic echo /mission/state
```

Stage 1 return-to-start check:

```bash
ros2 topic pub --once /mission/control std_msgs/msg/String "{data: start}"
# let robot explore for a while
ros2 topic pub --once /mission/control std_msgs/msg/String "{data: end}"
ros2 topic echo /mission/state
```

You should see state transitions including returning and then returned (or a return status code).

### 4. Save a map for Stage 2 localization

After a usable map is built, in T5:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash

ros2 run nav2_map_server map_saver_cli -f src/robot_slam/ros_data/maps/custom/stage1_map
```

Expected output files:

- slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map.yaml
- slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map.pgm

Stop Stage 1 launch after map save.

## Can you test this if SLAM is not fully stable yet?

Yes, partially. You can validate exploration plumbing before full SLAM quality is solved.

What you can test now:

- Node startup: frontier_explorer node launches and stays alive.
- Nav2 integration: goal requests are sent to navigate_to_pose.
- Mission control hooks: /mission/control end cancels active exploration goal.
- Return-to-start trigger path in Stage 1 (with TF-based start pose fallback).
- Basic movement attempts when /map, TF, and Nav2 are intermittently available.

What still requires SLAM to work reliably:

- Useful frontier detection (needs a valid /map occupancy grid).
- Stable autonomous room coverage.
- Good localization quality for repeatable trajectories.
- Accurate map output for Stage 2 localization.

Minimum signals required for meaningful exploration tests:

- /map publishes OccupancyGrid
- map -> base_link TF is available
- navigate_to_pose action server is available

Quick preflight:

```bash
ros2 topic hz /map
ros2 topic hz /tf
ros2 action list | grep navigate_to_pose
```

## Stage 2: Localization + Autonomous Navigation + Backend Transfer

### Optional Oak-D Lite object safety layer

Stage 2 now supports an optional Oak-D Lite YOLO safety node. This is not required for standard Nav2 obstacle avoidance, but it can act as an extra stop layer when you have a trained DepthAI blob ready.

Current behavior:

- If `enable_oakd_yolo:=false` (default), Stage 2 runs without the Oak-D YOLO node.
- If `enable_oakd_yolo:=true` and `oakd_yolo_blob_path` points to a valid DepthAI blob, the node monitors detections and can publish a zero `/cmd_vel` on hazardous detections.
- If the blob path is empty or DepthAI is missing, the node stays idle and logs a warning.

Example enable command:

```bash
ros2 launch robot_slam launch_stage_2.launch.py \
  map_yaml:=/home/evanc/ece148/scout-survey-rover/slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map.yaml \
  enable_oakd_yolo:=true \
  oakd_yolo_blob_path:=/path/to/yolo.blob
```

Useful topics when enabled:

- `/oakd/yolo/hazard` publishes `std_msgs/Bool`
- `/oakd/yolo/detections` publishes a summary string

### 1. Start website backend first (recommended)

In T3:

```bash
cd website/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Expected:

- Backend up at http://localhost:8000
- Log line eventually showing rosbridge connection from mission_receiver (after rosbridge is running)

### 2. Start website frontend

In T4:

```bash
cd website/frontend
npm install
npm run dev
```

Expected:

- Frontend up at http://localhost:5173

### 3. Ensure rosbridge is running

If T1 is not already running, start it now:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### 4. Launch Stage 2 with the saved map

In T2:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash

ros2 launch robot_slam launch_stage_2.launch.py \
  map_yaml:=/home/evanc/ece148/scout-survey-rover/slam_ros2_ws/src/robot_slam/ros_data/maps/custom/stage1_map.yaml
```

If you want to use the package default map, omit map_yaml.

### 5. Initialize localization and run autonomous navigation

- In RViz2, set initial pose with 2D Pose Estimate.
- Send a Nav2 goal using Nav2 Goal (or equivalent action client).
- Confirm robot plans and follows path.

In T5, validate localization/nav stack:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash

ros2 topic hz /amcl_pose
ros2 topic echo /mission/state
ros2 action list | grep navigate_to_pose
```

## Stage 2 Mission-to-Backend Transfer Test

This confirms that mission data is sent from ROS 2 to backend and visible on website APIs/UI.

### 1. Start a mission

In T5:

```bash
source /opt/ros/jazzy/setup.bash
cd slam_ros2_ws
source install/setup.bash

ros2 topic pub --once /mission/control std_msgs/msg/String "{data: start}"
```

Drive autonomously (or manually if needed) so the mission nodes can record:

- path samples (/tmp/mission_path.json)
- captured images (/tmp/mission_images/*)

### 2. End the mission

In T5:

```bash
ros2 topic pub --once /mission/control std_msgs/msg/String "{data: end}"
```

Expected ROS behavior:

- mission_return_node sends robot back toward start pose.
- mission_trigger_node publishes one mission payload to rosbridge topic /mission/payload.
- /mission/transfer_complete publishes true.

### 3. Verify ROS-side transfer completion

In T5:

```bash
ros2 topic echo /mission/transfer_complete --once
ros2 topic echo /mission/state
```

### 4. Verify backend receipt and mission artifacts

In a shell:

```bash
curl http://localhost:8000/api/missions
```

Then inspect one mission id:

```bash
curl http://localhost:8000/api/missions/<MISSION_ID>
```

Expected artifacts under website/backend/data/missions/<MISSION_ID>/:

- map.png
- annotations.json
- report.md
- images/

### 5. Verify on frontend

Open http://localhost:5173 and confirm the new mission appears with:

- rendered map
- captured images
- generated report

## Common Failure Checks

### No backend mission data appears

- Confirm rosbridge is running on ws://localhost:9090.
- Confirm backend logs include successful rosbridge connection.
- Confirm mission was ended (this triggers payload send).
- Confirm /mission/transfer_complete becomes true.

### Stage 2 does not localize

- Confirm map_yaml points to an existing YAML map file.
- In RViz2, set 2D Pose Estimate before sending goals.
- Check /amcl_pose is publishing.

### Navigation goals fail

- Confirm navigate_to_pose action server exists.
- Confirm Nav2 lifecycle nodes are active.
- Check TF chain and odometry health (/tf, /odom).

### Oak-D safety layer stays idle

- Confirm `enable_oakd_yolo:=true` was passed to the Stage 2 launch.
- Confirm the YOLO blob path exists on disk.
- Confirm the DepthAI Python package is installed in the runtime environment.
- Check `/oakd/yolo/hazard` and `/oakd/yolo/detections` topics.

## Optional One-Command Stack Startup

If you want a single command to bring up backend/frontend/bridge helper nodes, use:

```bash
./run_mission.sh
```

Then separately launch Stage 1 or Stage 2 from robot_slam as shown above.
