"use client";

import Link from "next/link";

export default function ReportPage() {
  const mission = {
    name: "Scout Survey Mission",
    robot: "Scout Survey Rover",
    mode: "Manual SLAM Survey",
    driveControl: "Keyboard Teleoperation",
    cameraControl: "Pico-Controlled Servo",
    startTime: "00:00",
    duration: "03:42",
    result: "Survey Completed",
  };

  const cameraImages = [
    {
      fileName: "inspection_001.jpg",
      timeTaken: "00:48",
    },
    {
      fileName: "inspection_002.jpg",
      timeTaken: "01:36",
    },
    {
      fileName: "inspection_003.jpg",
      timeTaken: "02:14",
    },
  ];

  const events = [
    "[00:00] Dashboard initialized",
    "[00:03] Robot connected",
    "[00:07] Camera servo centered",
    "[00:12] LiDAR stream active",
    "[00:25] SLAM mapping started",
    "[00:48] Camera image captured: inspection_001.jpg",
    "[01:36] Camera image captured: inspection_002.jpg",
    "[02:14] Camera image captured: inspection_003.jpg",
    "[03:42] Survey completed",
  ];

  return (
    <main className="min-h-screen bg-white p-8 text-black">
      <div className="mb-8 flex items-center justify-between print:hidden">
        <Link href="/" className="rounded-lg border px-4 py-2 hover:bg-slate-100">
          Back to Dashboard
        </Link>

        <button
          onClick={() => window.print()}
          className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500"
        >
          Save as PDF
        </button>
      </div>

      <h1 className="mb-2 text-4xl font-bold">Mission Report</h1>

      <p className="mb-8 text-slate-600">
        Manual SLAM Mapping and Camera Inspection Platform
      </p>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">Mission Information</h2>

        <div className="grid grid-cols-2 gap-4">
          <InfoItem label="Mission Name" value={mission.name} />
          <InfoItem label="Robot" value={mission.robot} />
          <InfoItem label="Mode" value={mission.mode} />
          <InfoItem label="Drive Control" value={mission.driveControl} />
          <InfoItem label="Camera Control" value={mission.cameraControl} />
          <InfoItem label="Start Time" value={mission.startTime} />
          <InfoItem label="Duration" value={mission.duration} />
          <InfoItem label="Result" value={mission.result} />
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">Mission Summary</h2>

        <p className="text-slate-700">
          The Scout Survey Rover was manually driven through the survey area
          using keyboard teleoperation. During the mission, LiDAR and odometry
          data were used to generate a live SLAM map. The OAK-D-Lite camera and
          Pico-controlled servo were used to capture inspection images during the
          survey.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">Generated SLAM Map</h2>

        <div className="flex h-80 items-center justify-center rounded-lg border bg-slate-100">
          SLAM Map Snapshot
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">Captured Camera Images</h2>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {cameraImages.map((image) => (
            <CameraImageCard
              key={image.fileName}
              fileName={image.fileName}
              timeTaken={image.timeTaken}
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-2xl font-semibold">Mission Event Log</h2>

        <ul className="list-disc pl-6">
          {events.map((event, index) => (
            <li key={index}>{event}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

function CameraImageCard({
  fileName,
  timeTaken,
}: {
  fileName: string;
  timeTaken: string;
}) {
  return (
    <div className="rounded-lg border bg-slate-100 p-4">
      <div className="mb-3 flex h-40 items-center justify-center rounded bg-white text-slate-400">
        Camera Image
      </div>

      <p className="font-semibold">{fileName}</p>
      <p className="text-sm text-slate-500">Time taken: {timeTaken}</p>
    </div>
  );
}