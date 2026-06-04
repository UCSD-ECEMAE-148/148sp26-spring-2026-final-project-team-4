import Link from "next/link";

export default function Home() {
  const cameraAngle = 0;

  const mission = {
    mode: "Manual Survey",
    state: "Idle",
  };

  const events = [
    "[00:00] Dashboard initialized",
    "[00:03] Robot connected",
    "[00:07] Camera servo centered",
    "[00:12] Waiting for SLAM data",
  ];

  const detections = [
    { type: "AprilTag", id: "Tag 01", location: "x: 1.2 m, y: 0.4 m" },
    { type: "Hazard", id: "Obstacle", location: "x: 2.1 m, y: -0.8 m" },
  ];

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-slate-100">
      <header className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Survey Robot Dashboard</h1>
          <p className="text-slate-400">
            Live mission monitoring and report generation
          </p>
        </div>

        <Link
          href="/report"
          className="rounded-lg bg-blue-600 px-4 py-2 font-semibold hover:bg-blue-500"
        >
          Generate Report
        </Link>
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Live Camera Feed">
          <div className="flex aspect-video items-center justify-center rounded-lg bg-slate-800 text-slate-400">
            OAK-D-Lite Camera Stream
          </div>
        </Card>

        <Card title="Live 2D Map">
          <div className="flex aspect-video items-center justify-center rounded-lg bg-slate-800 text-slate-400">
            SLAM Map / Robot Pose / Path Trace
          </div>
        </Card>

        <Card title="Camera Angle">
          <div className="mb-3 text-4xl font-bold">{cameraAngle}°</div>

          <input
            type="range"
            min="-135"
            max="135"
            value={cameraAngle}
            readOnly
            className="w-full"
          />

          <div className="mt-2 flex justify-between text-sm text-slate-400">
            <span>-135°</span>
            <span>0°</span>
            <span>+135°</span>
          </div>
        </Card>

        <Card title="Robot Status">
          <div className="grid grid-cols-2 gap-3">
            <StatusItem label="Connection" value="Connected" />
            <StatusItem label="Mission State" value={mission.state} />
            <StatusItem label="Battery" value="100%" />
            <StatusItem label="Mode" value={mission.mode} />
            <StatusItem label="Camera" value="Online" />
            <StatusItem label="SLAM" value="Waiting" />
          </div>
        </Card>
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Mission Event Log">
          <ul className="space-y-2 text-slate-300">
            {events.map((event, index) => (
              <li key={index} className="rounded-lg bg-slate-800 p-2">
                {event}
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Detections">
          <div className="space-y-3">
            {detections.map((detection, index) => (
              <div key={index} className="rounded-lg bg-slate-800 p-3">
                <p className="font-semibold">{detection.type}</p>
                <p className="text-slate-400">{detection.id}</p>
                <p className="text-slate-400">{detection.location}</p>
              </div>
            ))}
          </div>
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
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}