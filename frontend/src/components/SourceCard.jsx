import React from "react";
import Icon from "./Icon";

export default function SourceCard({ source, onDelete }) {
  return (
    <article className="rounded-lg border border-line bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-ink">{source.title}</h3>
          <p className="mt-1 text-sm text-slate-500">{source.source_type} {source.duration ? `• ${Math.round(source.duration)}s` : ""}</p>
        </div>
        {onDelete && <button className="btn-secondary px-3" onClick={() => onDelete(source.id)} title="Delete source"><Icon name="trash" size={16} /></button>}
      </div>
    </article>
  );
}
