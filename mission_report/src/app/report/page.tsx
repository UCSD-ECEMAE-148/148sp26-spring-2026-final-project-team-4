"use client";

import Link from "next/link";

export default function ReportPage() {
  const mission = {
    name: "Scout Survey Mission",
    robot: "Survey Robot",
    startTime: "00:00",
    duration: "00:12",
    result: "Success",
  };

  const detections = [
    {
      type: "AprilTag",
      id: "Tag 01",
      location: "x: 1.2 m, y: 0.4 m",
    },
    {
      type: "Hazard",
      id: "Obstacle",
      location: "x: 2.1 m, y: -0.8 m",
    },
  ];

  const events = [
    "[00:00] Dashboard initialized",
    "[00:03] Robot connected",
    "[00:07] Camera servo centered",
    "[00:12] Waiting for SLAM data",
  ];

  return (
    <main className="min-h-screen bg-white p-8 text-black">
      <div className="mb-8 flex items-center justify-between print:hidden">
        <Link
          href="/"
          className="rounded-lg border px-4 py-2 hover:bg-slate-100"
        >
          Back to Dashboard
        </Link>

        <button
          onClick={() => window.print()}
          className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500"
        >
          Save as PDF
        </button>
      </div>

      <h1 className="mb-2 text-4xl font-bold">
        Mission Report
      </h1>

      <p className="mb-8 text-slate-600">
        Autonomous Scout and Survey Rover
      </p>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">
          Mission Information
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <InfoItem label="Mission Name" value={mission.name} />
          <InfoItem label="Robot" value={mission.robot} />
          <InfoItem label="Start Time" value={mission.startTime} />
          <InfoItem label="Duration" value={mission.duration} />
          <InfoItem label="Result" value={mission.result} />
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">
          Mission Summary
        </h2>

        <p className="text-slate-700">
          The rover successfully completed its survey mission.
          AprilTags and hazards were detected and recorded.
          The generated map, robot trajectory, and camera
          observations are summarized below.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">
          Map Snapshot
        </h2>

        <div className="flex h-80 items-center justify-center rounded-lg border bg-slate-100">
          SLAM Map Image
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">
          Camera Images
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex h-48 items-center justify-center rounded-lg border bg-slate-100">
            Image 1
          </div>

          <div className="flex h-48 items-center justify-center rounded-lg border bg-slate-100">
            Image 2
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">
          Detections
        </h2>

        <table className="w-full border-collapse border">
          <thead>
            <tr>
              <th className="border p-2">Type</th>
              <th className="border p-2">ID</th>
              <th className="border p-2">Location</th>
            </tr>
          </thead>

          <tbody>
            {detections.map((detection, index) => (
              <tr key={index}>
                <td className="border p-2">
                  {detection.type}
                </td>

                <td className="border p-2">
                  {detection.id}
                </td>

                <td className="border p-2">
                  {detection.location}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2 className="mb-4 text-2xl font-semibold">
          Event Log
        </h2>

        <ul className="list-disc pl-6">
          {events.map((event, index) => (
            <li key={index}>{event}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}

function InfoItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}