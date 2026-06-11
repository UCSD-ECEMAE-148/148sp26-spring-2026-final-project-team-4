# Scout Survey Rover — Web Dashboard

Browser-based mission control for the Scout Survey Rover. Provides live camera feed, manual WASD driving, inspection photo capture, and real-time SLAM map visualization.

## Stack

- **Next.js 16** (React 19, TypeScript, Tailwind CSS v4)
- **ROS 2 HTTP bridge** at port 8080 (`survey_camera/web_bridge_node.py`)

## Running

The dashboard depends on the ROS 2 stack being up. See the full launch sequence in [`docs/ros2_testing.md`](../docs/ros2_testing.md#5-web-dashboard).

**Full launch (3 terminals):**

```bash
# Terminal 1 — SLAM + VESC stack (--headless so keyboard teleop doesn't block the terminal)
cd ~/scout-survey-rover && ./stage1_start.sh --headless

# Terminal 2 — Camera + HTTP bridge
source /opt/ros/jazzy/setup.bash && source ~/scout-survey-rover/slam_ros2_ws/install/setup.bash
ros2 launch survey_camera survey_camera.launch.py

# Terminal 3 — Web dashboard
cd ~/scout-survey-rover/mission_report && npm run dev
```

Then open `http://<Pi-IP>:3000` in a browser. Find the Pi's IP with `hostname -I`.

> Requires Node.js ≥ 20. Run `node --version` to check.

## HTTP bridge endpoints (port 8080)

All served by `survey_camera/survey_camera/web_bridge_node.py`:

| Endpoint | Description |
|----------|-------------|
| `GET /video` | MJPEG stream from OAK-D camera |
| `POST /capture` | Trigger inspection snapshot; saves to `public/captures/` |
| `POST /drive` | Publish `{linear_x, angular_z}` Twist to `/key_vel` |
| `GET /map_image` | Current SLAM map as PNG with robot dot (503 if no map yet) |
| `GET /health` | Returns `OK` |

## Keyboard controls

| Key | Action |
|-----|--------|
| `W` / `S` | Forward / Reverse |
| `A` / `D` | Turn left / right |
| `Space` | Emergency stop |
| `J` / `L` | Pan camera left / right |
| `K` | Center camera |
| `Enter` | Take inspection photo |

Drive keys are press-and-hold — the bridge repeats commands at 100 ms intervals to keep the ackermann mux (0.5 s timeout) from dropping them.

## Captured images

Saved to `public/captures/inspection_<timestamp>.jpg`.
Accessible at `http://<Pi-IP>:3000/captures/<filename>` once the dev server is running.

## Development

```bash
npm install        # first time only
npm run dev        # hot-reload dev server on :3000
npm run build      # production build
npm start          # serve production build
npx tsc --noEmit   # type-check without building
```
