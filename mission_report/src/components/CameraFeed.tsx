export default function CameraFeed() {
  return (
    <div className="bg-slate-900 rounded-xl p-4">
      <h2 className="text-xl font-semibold mb-3">
        Live Camera Feed
      </h2>

      <div className="aspect-video bg-slate-800 rounded-lg flex items-center justify-center">
        Camera Stream
      </div>
    </div>
  );
}