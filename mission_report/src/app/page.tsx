"use client";

import { useEffect, useRef, useState } from "react";

// ------------------------------------------------------------------ //
// Drive helpers (module-level, no React deps)                         //
// ------------------------------------------------------------------ //

const DRIVE_KEYS = new Set(["w", "a", "s", "d"]);
const SPEED_LIN = 0.3;  // m/s   — conservative indoor speed
const SPEED_ANG = 0.35; // rad   — matches keyboard_teleop MAX_STEER; goes directly to steering_angle

function computeTwist(keys: Set<string>) {
  return {
    linear_x: keys.has("w") ? SPEED_LIN : keys.has("s") ? -SPEED_LIN : 0,
    angular_z: (keys.has("a") ? SPEED_ANG : 0) - (keys.has("d") ? SPEED_ANG : 0),
  };
}

function commandLabel(keys: Set<string>): string {
  const f = keys.has("w"), r = keys.has("s"), l = keys.has("a"), ri = keys.has("d");
  if (!f && !r && !l && !ri) return "Stop";
  if (f && l) return "Forward Left";
  if (f && ri) return "Forward Right";
  if (r && l) return "Reverse Left";
  if (r && ri) return "Reverse Right";
  if (f) return "Forward";
  if (r) return "Reverse";
  if (l) return "Turn Left";
  return "Turn Right";
}

// ------------------------------------------------------------------ //
// Component                                                           //
// ------------------------------------------------------------------ //

export default function Home() {
  const [driveCommand, setDriveCommand] = useState("Stop");
  const [cameraAngle, setCameraAngle] = useState(0);
  const [cameraCommand, setCameraCommand] = useState("Center");
  const [lastPhoto, setLastPhoto] = useState("None");
  const [photoTriggered, setPhotoTriggered] = useState(false);
  const [bridge, setBridge] = useState("");
  const [mapTimestamp, setMapTimestamp] = useState(0);
  const [mapReady, setMapReady] = useState(false);

  // Refs for drive loop — stable across renders, safe to read from closures
  const pressedKeys = useRef(new Set<string>());
  const driveIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Stable refs to drive callbacks so JSX pointer handlers can call them
  const pressDriveKeyRef = useRef<(key: string) => void>(() => {});
  const releaseDriveKeyRef = useRef<(key: string) => void>(() => {});
  const emergencyStopRef = useRef<() => void>(() => {});

  // Mirror cameraAngle in a ref so the keyboard useEffect can read it without a stale closure
  const cameraAngleRef = useRef(0);
  useEffect(() => { cameraAngleRef.current = cameraAngle; }, [cameraAngle]);

  // ---------------------------------------------------------------- //
  // Drive + keyboard setup (runs once after mount)                   //
  // ---------------------------------------------------------------- //
  useEffect(() => {
    const b = `http://${window.location.hostname}:8080`;
    setBridge(b);

    function sendDrive(cmd: { linear_x: number; angular_z: number }) {
      fetch(`${b}/drive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cmd),
      }).catch(() => {});
    }

    function stopDriveLoop() {
      if (driveIntervalRef.current) {
        clearInterval(driveIntervalRef.current);
        driveIntervalRef.current = null;
      }
      sendDrive({ linear_x: 0, angular_z: 0 });
    }

    function startDriveLoop() {
      if (driveIntervalRef.current) return;
      // Repeat at 100ms so the mux (0.5s timeout) never drops the command
      driveIntervalRef.current = setInterval(() => {
        const keys = pressedKeys.current;
        if (![...DRIVE_KEYS].some((k) => keys.has(k))) {
          stopDriveLoop();
          return;
        }
        sendDrive(computeTwist(keys));
      }, 100);
    }

    function pressDriveKey(key: string) {
      pressedKeys.current.add(key);
      setDriveCommand(commandLabel(pressedKeys.current));
      sendDrive(computeTwist(pressedKeys.current));
      startDriveLoop();
    }

    function releaseDriveKey(key: string) {
      pressedKeys.current.delete(key);
      const anyActive = [...DRIVE_KEYS].some((k) => pressedKeys.current.has(k));
      if (anyActive) {
        setDriveCommand(commandLabel(pressedKeys.current));
        sendDrive(computeTwist(pressedKeys.current));
      } else {
        setDriveCommand("Stop");
        stopDriveLoop();
      }
    }

    function emergencyStop() {
      pressedKeys.current.clear();
      setDriveCommand("Stop");
      stopDriveLoop();
    }

    // Expose to JSX pointer handlers via refs
    pressDriveKeyRef.current = pressDriveKey;
    releaseDriveKeyRef.current = releaseDriveKey;
    emergencyStopRef.current = emergencyStop;

    function handleKeyDown(event: KeyboardEvent) {
      const key = event.key.toLowerCase();

      if (DRIVE_KEYS.has(key)) {
        pressDriveKey(key);
        return;
      }

      if (event.code === "Space") {
        event.preventDefault();
        emergencyStop();
        return;
      }

      if (key === "j") {
        const next = Math.max(-45, cameraAngleRef.current - 1);
        cameraAngleRef.current = next;
        setCameraAngle(next);
        setCameraCommand(next < 0 ? "Left" : "Center");
        fetch(`${b}/camera_angle`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ angle: next }) }).catch(() => {});
      } else if (key === "k") {
        cameraAngleRef.current = 0;
        setCameraAngle(0);
        setCameraCommand("Center");
        fetch(`${b}/camera_angle`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ angle: 0 }) }).catch(() => {});
      } else if (key === "l") {
        const next = Math.min(45, cameraAngleRef.current + 1);
        cameraAngleRef.current = next;
        setCameraAngle(next);
        setCameraCommand(next > 0 ? "Right" : "Center");
        fetch(`${b}/camera_angle`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ angle: next }) }).catch(() => {});
      } else if (key === "enter") {
        // Inline capture — uses closure-local `b`, not stale `bridge` state
        setPhotoTriggered(true);
        setTimeout(() => setPhotoTriggered(false), 250);
        fetch(`${b}/capture`, { method: "POST" })
          .then((r) => r.json())
          .then((data) => setLastPhoto(data.message ?? "captured"))
          .catch(() => {});
      }
    }

    function handleKeyUp(event: KeyboardEvent) {
      const key = event.key.toLowerCase();
      if (DRIVE_KEYS.has(key)) releaseDriveKey(key);
    }

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      stopDriveLoop(); // safety: stop robot if dashboard is closed
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------- //
  // Map refresh interval                                              //
  // ---------------------------------------------------------------- //
  useEffect(() => {
    const id = setInterval(() => setMapTimestamp(Date.now()), 500);
    return () => clearInterval(id);
  }, []);

  // ---------------------------------------------------------------- //
  // Camera capture                                                    //
  // ---------------------------------------------------------------- //
  function takePicture() {
    if (!bridge) return;
    setPhotoTriggered(true);
    setTimeout(() => setPhotoTriggered(false), 250);
    fetch(`${bridge}/capture`, { method: "POST" })
      .then((r) => r.json())
      .then((data) => setLastPhoto(data.message ?? "captured"))
      .catch(() => {});
  }

  // ---------------------------------------------------------------- //
  // Camera pan + servo                                               //
  // ---------------------------------------------------------------- //
  function sendCameraAngle(angle: number) {
    if (!bridge) return;
    fetch(`${bridge}/camera_angle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ angle: Math.round(angle) }),
    }).catch(() => {});
  }

  function panCameraLeft() {
    const next = Math.max(-45, cameraAngleRef.current - 1);
    cameraAngleRef.current = next;
    setCameraAngle(next);
    setCameraCommand("Left");
    sendCameraAngle(next);
  }

  function centerCamera() {
    cameraAngleRef.current = 0;
    setCameraAngle(0);
    setCameraCommand("Center");
    sendCameraAngle(0);
  }

  function panCameraRight() {
    const next = Math.min(45, cameraAngleRef.current + 1);
    cameraAngleRef.current = next;
    setCameraAngle(next);
    setCameraCommand("Right");
    sendCameraAngle(next);
  }

  async function generateReport() {
    if (bridge) {
      try { await fetch(`${bridge}/save_map`, { method: "POST" }); } catch { /* no map yet, continue */ }
    }
    window.location.href = "/report";
  }

  // ---------------------------------------------------------------- //
  // Active-state helpers for drive button highlights                 //
  // ---------------------------------------------------------------- //
  const cmd = driveCommand;

  const events = [
    "[00:00] Dashboard initialized",
    "[00:03] Robot connected",
    "[00:07] Camera servo centered",
    "[00:12] LiDAR stream active",
    "[00:25] SLAM mapping started",
    `[03:42] Last photo: ${lastPhoto}`,
  ];

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-slate-100">
      <header className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Scout Survey Rover Dashboard</h1>
          <p className="text-slate-400">
            Manual driving, live SLAM mapping, camera inspection, and mission
            report generation
          </p>
        </div>
        <button
          onClick={generateReport}
          className="rounded-lg bg-blue-600 px-4 py-2 font-semibold hover:bg-blue-500"
        >
          Generate Report
        </button>
      </header>

      <section className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatusItem label="Mode" value="Manual Control" />
        <StatusItem label="Drive Command" value={driveCommand} />
        <StatusItem label="Camera Angle" value={`${cameraAngle}°`} />
        <StatusItem label="Last Photo" value={lastPhoto} />
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Live Camera Feed */}
        <Card title="Live Camera Feed">
          {bridge ? (
            <img
              src={`${bridge}/video`}
              alt="OAK-D Camera Stream"
              className="aspect-video w-full rounded-lg bg-slate-800 object-contain"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
          ) : (
            <div className="flex aspect-video items-center justify-center rounded-lg bg-slate-800 text-slate-400">
              Connecting…
            </div>
          )}
          <button
            onClick={takePicture}
            className={`mt-4 w-full rounded-lg px-4 py-3 font-semibold transition-all duration-200 ${
              photoTriggered
                ? "scale-95 bg-green-600"
                : "bg-blue-600 hover:bg-blue-500"
            }`}
          >
            {photoTriggered ? "Captured!" : "Take Picture (Enter)"}
          </button>
        </Card>

        {/* Live SLAM Map */}
        <Card title="Live SLAM Map">
          <div className="relative aspect-video overflow-hidden rounded-lg bg-slate-800">
            {bridge && mapTimestamp > 0 && (
              <img
                src={`${bridge}/map_image?t=${mapTimestamp}`}
                alt="SLAM Map"
                className="h-full w-full object-contain"
                onLoad={() => setMapReady(true)}
                onError={() => setMapReady(false)}
              />
            )}
            {!mapReady && (
              <div className="absolute inset-0 flex items-center justify-center text-slate-400">
                Waiting for SLAM map…
              </div>
            )}
          </div>
        </Card>

        {/* Rover Driving Control */}
        <Card title="Rover Driving Control">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div />
            <DriveKey
              label="W"
              action="Forward"
              active={cmd.includes("Forward")}
              driveKey="w"
              pressFn={pressDriveKeyRef}
              releaseFn={releaseDriveKeyRef}
            />
            <div />
            <DriveKey
              label="A"
              action="Left"
              active={cmd.includes("Left")}
              driveKey="a"
              pressFn={pressDriveKeyRef}
              releaseFn={releaseDriveKeyRef}
            />
            <Key
              label="Space"
              action="Stop"
              active={cmd === "Stop"}
              onPointerDown={() => emergencyStopRef.current()}
            />
            <DriveKey
              label="D"
              action="Right"
              active={cmd.includes("Right")}
              driveKey="d"
              pressFn={pressDriveKeyRef}
              releaseFn={releaseDriveKeyRef}
            />
            <div />
            <DriveKey
              label="S"
              action="Reverse"
              active={cmd.includes("Reverse")}
              driveKey="s"
              pressFn={pressDriveKeyRef}
              releaseFn={releaseDriveKeyRef}
            />
            <div />
          </div>
        </Card>

        {/* Camera Servo Control */}
        <Card title="Camera Servo Control">
          <div className="mb-4 text-center">
            <p className="text-5xl font-bold">{cameraAngle}°</p>
          </div>
          <input
            type="range"
            min={-45}
            max={45}
            step={1}
            value={cameraAngle}
            onChange={(e) => {
              const next = Number(e.target.value);
              cameraAngleRef.current = next;
              setCameraAngle(next);
              setCameraCommand(next < 0 ? "Left" : next > 0 ? "Right" : "Center");
              sendCameraAngle(next);
            }}
            className="w-full"
          />
          <div className="mt-2 flex justify-between text-sm text-slate-400">
            <span>-45°</span>
            <span>0°</span>
            <span>45°</span>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            <Key
              label="J"
              action="-1°"
              active={cameraCommand === "Left"}
              onClick={panCameraLeft}
            />
            <Key
              label="K"
              action="Center"
              active={cameraCommand === "Center"}
              onClick={centerCamera}
            />
            <Key
              label="L"
              action="+1°"
              active={cameraCommand === "Right"}
              onClick={panCameraRight}
            />
          </div>
        </Card>
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Robot System Status">
          <div className="grid grid-cols-2 gap-3">
            <StatusItem label="Connection" value="Connected" />
            <StatusItem label="LiDAR" value="Online" />
            <StatusItem label="Odometry" value="Online" />
            <StatusItem label="Camera" value="Online" />
            <StatusItem label="SLAM" value="Mapping" />
            <StatusItem label="Pico" value="Connected" />
          </div>
        </Card>
        <Card title="Mission Event Log">
          <ul className="space-y-2 text-slate-300">
            {events.map((event, index) => (
              <li key={index} className="rounded-lg bg-slate-800 p-2">
                {event}
              </li>
            ))}
          </ul>
        </Card>
      </section>
    </main>
  );
}

// ------------------------------------------------------------------ //
// Sub-components                                                      //
// ------------------------------------------------------------------ //

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h2 className="mb-3 text-xl font-semibold">{title}</h2>
      {children}
    </div>
  );
}

function StatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-800 p-3">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="break-words text-lg font-semibold">{value}</p>
    </div>
  );
}

function Key({
  label,
  action,
  active,
  onClick,
  onPointerDown,
  onPointerUp,
  onPointerLeave,
}: {
  label: string;
  action: string;
  active: boolean;
  onClick?: () => void;
  onPointerDown?: () => void;
  onPointerUp?: () => void;
  onPointerLeave?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      onPointerDown={onPointerDown}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerLeave}
      className={`rounded-lg p-3 select-none ${
        active ? "bg-blue-600" : "bg-slate-800 hover:bg-slate-700"
      }`}
    >
      <p className="font-bold">{label}</p>
      <p className="text-sm text-slate-300">{action}</p>
    </button>
  );
}

// Drive key: press-and-hold via pointer events
function DriveKey({
  label,
  action,
  active,
  driveKey,
  pressFn,
  releaseFn,
}: {
  label: string;
  action: string;
  active: boolean;
  driveKey: string;
  pressFn: React.MutableRefObject<(k: string) => void>;
  releaseFn: React.MutableRefObject<(k: string) => void>;
}) {
  return (
    <Key
      label={label}
      action={action}
      active={active}
      onPointerDown={() => pressFn.current(driveKey)}
      onPointerUp={() => releaseFn.current(driveKey)}
      onPointerLeave={() => releaseFn.current(driveKey)}
    />
  );
}
