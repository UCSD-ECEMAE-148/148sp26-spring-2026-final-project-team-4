#!/bin/bash
set -e
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "[0/5] Checking Ollama..."
if ! curl -sf http://localhost:11434/api/tags > /dev/null; then
  echo "ERROR: Ollama is not running. Start it with: ollama serve"
  exit 1
fi
echo "  ✓ Ollama reachable"

echo "[1/5] Sourcing ROS 2 workspace..."
source /opt/ros/humble/setup.bash
if [ -f "$REPO_ROOT/slam_ros2_ws/install/setup.bash" ]; then
  source "$REPO_ROOT/slam_ros2_ws/install/setup.bash"
fi

echo "[2/5] Starting rosbridge WebSocket server..."
ros2 launch rosbridge_server rosbridge_websocket_launch.xml &
ROSBRIDGE_PID=$!

echo "[3/5] Starting mission_bridge ROS nodes..."
ros2 launch mission_bridge mission_bridge.launch.py &
ROS_NODES_PID=$!

echo "[4/5] Starting website backend and frontend..."
cd "$REPO_ROOT/website/backend"
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

if [ -d "$REPO_ROOT/website/frontend" ]; then
  cd "$REPO_ROOT/website/frontend"
  npm install -q
  npm run dev &
  FRONTEND_PID=$!
fi

echo ""
echo "✓ Stack is running:"
echo "  ollama     → http://localhost:11434"
echo "  rosbridge  → ws://localhost:9090"
echo "  backend    → http://localhost:8000"
echo "  frontend   → http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all processes."

trap "kill $ROSBRIDGE_PID $ROS_NODES_PID $BACKEND_PID ${FRONTEND_PID:-} 2>/dev/null; echo 'Stopped.'; exit" INT
wait
