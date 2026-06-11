"use client";

export default function PrintButton() {
  return (
    <button
      onClick={() => window.print()}
      className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500"
    >
      Save as PDF
    </button>
  );
}
