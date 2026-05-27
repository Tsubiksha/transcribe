import React from "react";

function stamp(value) {
  if (value == null) return "--:--";
  const total = Math.floor(value);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}

export default function ChatMessage({ message }) {
  const timestamps = message.timestamps?.length
    ? message.timestamps
    : message.start_time != null
      ? [{ start: stamp(message.start_time), end: stamp(message.end_time), start_seconds: message.start_time }]
      : [];

  return (
    <div className="space-y-3">
      <div className="ml-auto max-w-3xl rounded-lg bg-accent px-4 py-3 text-sm text-white">{message.question}</div>
      <div className="max-w-3xl rounded-lg border border-line bg-white px-4 py-3 text-sm shadow-sm">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          {message.source && <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{message.source}</span>}
          {timestamps.map((item, index) => (
            <button
              key={`${item.start}-${index}`}
              type="button"
              className="rounded-md bg-teal-50 px-2 py-1 text-xs font-semibold text-accent hover:bg-teal-100"
              onClick={() => window.dispatchEvent(new CustomEvent("media:seek", { detail: item.start_seconds }))}
              title="Jump to timestamp"
            >
              {item.start} - {item.end}
            </button>
          ))}
          {message.confidence_score != null && <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">confidence {message.confidence_score}</span>}
        </div>
        <p className="leading-6 text-slate-800">{message.answer}</p>
        {message.matched_text && <details className="mt-3 text-xs text-slate-500"><summary className="cursor-pointer font-semibold">Matched transcript</summary><p className="mt-2 whitespace-pre-line">{message.matched_text}</p></details>}
      </div>
    </div>
  );
}
