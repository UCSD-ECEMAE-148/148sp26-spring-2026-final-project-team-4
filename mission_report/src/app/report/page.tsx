import fs from "fs";
import path from "path";
import Link from "next/link";
import PrintButton from "./PrintButton";

export const dynamic = "force-dynamic"; // always read live filesystem, never cache

// ------------------------------------------------------------------ //
// Data helpers (server-side)                                          //
// ------------------------------------------------------------------ //

function getCaptureImages(): string[] {
  const dir = path.join(process.cwd(), "public", "captures");
  try {
    return fs
      .readdirSync(dir)
      .filter((f) => /\.(jpg|jpeg|png)$/i.test(f))
      .sort();
  } catch {
    return [];
  }
}

function parseTimestamp(filename: string): Date | null {
  const m = filename.match(
    /inspection_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/
  );
  if (!m) return null;
  return new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}`);
}

function formatTimestamp(filename: string): string {
  const d = parseTimestamp(filename);
  if (!d) return "—";
  return d.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

// ------------------------------------------------------------------ //
// Page (server component)                                             //
// ------------------------------------------------------------------ //

export default function ReportPage() {
  const images = getCaptureImages();
  const mapSnapshotExists = fs.existsSync(
    path.join(process.cwd(), "public", "map_snapshot.png")
  );

  // Derive timing from captured image filenames
  const firstTs = images.length > 0 ? parseTimestamp(images[0]) : null;
  const lastTs =
    images.length > 0 ? parseTimestamp(images[images.length - 1]) : null;

  const startTime = firstTs
    ? firstTs.toLocaleString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      })
    : "—";

  const duration =
    firstTs && lastTs
      ? formatDuration(
          Math.round((lastTs.getTime() - firstTs.getTime()) / 1000)
        )
      : "—";

  // Build event log from real captures
  const captureEvents = images.map(
    (f) => `[${formatTimestamp(f)}] Inspection photo captured: ${f}`
  );

  const events = [
    "[—] Dashboard initialized",
    "[—] SLAM mapping started",
    ...captureEvents,
    images.length > 0 ? `[${formatTimestamp(images[images.length - 1])}] Survey completed` : "[—] No captures yet",
  ];

  return (
    <main className="min-h-screen bg-white p-8 text-black">
      {/* Toolbar */}
      <div className="mb-8 flex items-center justify-between print:hidden">
        <Link href="/" className="rounded-lg border px-4 py-2 hover:bg-slate-100">
          ← Back to Dashboard
        </Link>
        <PrintButton />
      </div>

      <h1 className="mb-2 text-4xl font-bold">Mission Report</h1>
      <p className="mb-8 text-slate-600">
        Manual SLAM Mapping and Camera Inspection Platform
      </p>

      {/* Mission Info */}
      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">Mission Information</h2>
        <div className="grid grid-cols-2 gap-4">
          <InfoItem label="Mission Name" value="Scout Survey Mission" />
          <InfoItem label="Robot" value="Scout Survey Rover" />
          <InfoItem label="Mode" value="Manual SLAM Survey" />
          <InfoItem label="Drive Control" value="Web Dashboard (WASD)" />
          <InfoItem label="Camera Control" value="Pico-Controlled Servo" />
          <InfoItem label="Start Time" value={startTime} />
          <InfoItem label="Duration (first→last capture)" value={duration} />
          <InfoItem
            label="Captures"
            value={images.length > 0 ? `${images.length} photo${images.length !== 1 ? "s" : ""}` : "None"}
          />
        </div>
      </section>

      {/* Summary */}
      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">Mission Summary</h2>
        <p className="text-slate-700">
          The Scout Survey Rover was manually driven through the survey area
          using the web dashboard WASD controls. During the mission, LiDAR and
          odometry data were fused by the EKF and processed by SLAM Toolbox to
          generate a live occupancy map. The OAK-D-Lite camera and
          Pico-controlled servo were used to capture{" "}
          {images.length > 0 ? `${images.length} inspection image${images.length !== 1 ? "s" : ""}` : "inspection images"}{" "}
          during the survey.
        </p>
      </section>

      {/* SLAM Map */}
      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">Generated SLAM Map</h2>
        {mapSnapshotExists ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src="/map_snapshot.png"
            alt="SLAM Map Snapshot"
            className="max-h-96 rounded-lg border object-contain"
          />
        ) : (
          <div className="flex h-80 items-center justify-center rounded-lg border bg-slate-100 text-slate-500">
            No map snapshot saved yet — click &quot;Generate Report&quot; on the dashboard
            while SLAM is running to save one.
          </div>
        )}
      </section>

      {/* Captured Images */}
      <section className="mb-8">
        <h2 className="mb-4 text-2xl font-semibold">
          Captured Camera Images{" "}
          {images.length > 0 && (
            <span className="text-lg font-normal text-slate-500">
              ({images.length})
            </span>
          )}
        </h2>
        {images.length === 0 ? (
          <p className="text-slate-500">
            No captures yet. Press Enter (or the Take Picture button) on the
            dashboard to capture inspection images.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {images.map((filename) => (
              <CaptureCard key={filename} filename={filename} />
            ))}
          </div>
        )}
      </section>

      {/* Event Log */}
      <section>
        <h2 className="mb-4 text-2xl font-semibold">Mission Event Log</h2>
        <ul className="list-disc pl-6 space-y-1">
          {events.map((event, i) => (
            <li key={i} className="text-slate-700">
              {event}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

// ------------------------------------------------------------------ //
// Sub-components                                                      //
// ------------------------------------------------------------------ //

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

function CaptureCard({ filename }: { filename: string }) {
  return (
    <div className="rounded-lg border bg-slate-50 p-4">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`/captures/${filename}`}
        alt={filename}
        className="mb-3 h-40 w-full rounded object-cover"
      />
      <p className="font-semibold text-sm break-all">{filename}</p>
      <p className="text-sm text-slate-500">{formatTimestamp(filename)}</p>
    </div>
  );
}
