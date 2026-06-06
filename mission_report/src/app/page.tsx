"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function Home() {
  const [driveCommand, setDriveCommand] = useState("Stop");
  const [cameraAngle, setCameraAngle] = useState(0);
  const [cameraCommand, setCameraCommand] = useState("Center");
  const [lastPhoto, setLastPhoto] = useState("None");
  const [photoTriggered, setPhotoTriggered] = useState(false);

  const events = [
    "[00:00] Dashboard initialized",
    "[00:03] Robot connected",
    "[00:07] Camera servo centered",
    "[00:12] LiDAR stream active",
    "[00:25] SLAM mapping started",
    `[03:42] Last photo: ${lastPhoto}`,
  ];

  function takePicture() {
    const fileName = `inspection_${Date.now()}.jpg`;

    setLastPhoto(fileName);

    setPhotoTriggered(true);

    setTimeout(() => {
      setPhotoTriggered(false);
    }, 250);

    // Future:
    // Call ROS2 capture service here
  }

  function panCameraLeft() {
    setCameraCommand("Left");
    setCameraAngle((prev) => Math.max(-45, prev - 1));
  }

  function centerCamera() {
    setCameraCommand("Center");
    setCameraAngle(0);
  }

  function panCameraRight() {
    setCameraCommand("Right");
    setCameraAngle((prev) => Math.min(45, prev + 1));
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const key = event.key.toLowerCase();

      if (key === "w") setDriveCommand("Forward");
      if (key === "s") setDriveCommand("Reverse");
      if (key === "a") setDriveCommand("Turn Left");
      if (key === "d") setDriveCommand("Turn Right");

      if (event.code === "Space") {
        event.preventDefault();
        setDriveCommand("Stop");
      }

      if (key === "j") panCameraLeft();
      if (key === "k") centerCamera();
      if (key === "l") panCameraRight();

      if (key === "enter") takePicture();
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-slate-100">
      <header className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Scout Survey Rover Dashboard
          </h1>

          <p className="text-slate-400">
            Manual driving, live SLAM mapping, camera inspection, and mission
            report generation
          </p>
        </div>

        <Link
          href="/report"
          className="rounded-lg bg-blue-600 px-4 py-2 font-semibold hover:bg-blue-500"
        >
          Generate Report
        </Link>
      </header>

      <section className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatusItem label="Mode" value="Manual Control" />
        <StatusItem label="Drive Command" value={driveCommand} />
        <StatusItem label="Camera Angle" value={`${cameraAngle}°`} />
        <StatusItem label="Last Photo" value={lastPhoto} />
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Live Camera Feed">
          <div className="flex aspect-video items-center justify-center rounded-lg bg-slate-800 text-slate-400">
            OAK-D-Lite Camera Stream
          </div>

          <button
            onClick={takePicture}
            className={`mt-4 w-full rounded-lg px-4 py-3 font-semibold transition-all duration-200 ${
              photoTriggered
                ? "bg-green-600 scale-95"
                : "bg-blue-600 hover:bg-blue-500"
            }`}
          >
            {photoTriggered ? "Captured!" : "Take Picture (Enter)"}
          </button>
        </Card>

        <Card title="Live SLAM Map">
          <div className="flex aspect-video items-center justify-center rounded-lg bg-slate-800 text-slate-400">
            /map visualization / robot pose / path trace
          </div>
        </Card>

        <Card title="Rover Driving Control">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div />

            <Key
              label="W"
              action="Forward"
              active={driveCommand === "Forward"}
              onClick={() => setDriveCommand("Forward")}
            />

            <div />

            <Key
              label="A"
              action="Left"
              active={driveCommand === "Turn Left"}
              onClick={() => setDriveCommand("Turn Left")}
            />

            <Key
              label="Space"
              action="Stop"
              active={driveCommand === "Stop"}
              onClick={() => setDriveCommand("Stop")}
            />

            <Key
              label="D"
              action="Right"
              active={driveCommand === "Turn Right"}
              onClick={() => setDriveCommand("Turn Right")}
            />

            <div />

            <Key
              label="S"
              action="Reverse"
              active={driveCommand === "Reverse"}
              onClick={() => setDriveCommand("Reverse")}
            />

            <div />
          </div>
        </Card>

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
              const nextAngle = Number(e.target.value);
              setCameraAngle(nextAngle);

              if (nextAngle < 0) setCameraCommand("Left");
              else if (nextAngle > 0) setCameraCommand("Right");
              else setCameraCommand("Center");
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

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
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
}: {
  label: string;
  action: string;
  active: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg p-3 ${
        active ? "bg-blue-600" : "bg-slate-800 hover:bg-slate-700"
      }`}
    >
      <p className="font-bold">{label}</p>
      <p className="text-sm text-slate-300">{action}</p>
    </button>
  );
}