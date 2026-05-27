import React from "react";
import Icon from "./Icon";
import LoadingSpinner from "./LoadingSpinner";

export default function UploadBox({ onSubmit, loading }) {
  return (
    <form onSubmit={onSubmit} className="panel space-y-4">
      <label className="flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-line bg-slate-50 p-6 text-center">
        <Icon name="cloud" className="mb-3 text-accent" size={34} />
        <span className="font-semibold">Choose audio or video</span>
        <span className="mt-1 text-sm text-slate-500">mp3, wav, m4a, aac, flac, mp4, mov, mkv, webm</span>
        <input className="mt-4 block text-sm" type="file" name="file" accept=".mp3,.wav,.m4a,.aac,.flac,.mp4,.mov,.mkv,.webm" required />
      </label>
      <button className="btn-primary" disabled={loading}>{loading && <LoadingSpinner />} Upload and transcribe</button>
    </form>
  );
}
