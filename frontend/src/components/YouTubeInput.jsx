import React from "react";
import Icon from "./Icon";
import LoadingSpinner from "./LoadingSpinner";

export default function YouTubeInput({ url, setUrl, onSubmit, loading }) {
  return (
    <form onSubmit={onSubmit} className="panel space-y-4">
      <div className="flex items-center gap-2">
        <Icon name="youtube" className="text-coral" size={22} />
        <h2 className="text-lg font-semibold">Process a YouTube video</h2>
      </div>
      <input className="field" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://www.youtube.com/watch?v=..." required />
      <button className="btn-primary" disabled={loading}>{loading && <LoadingSpinner />} Download and transcribe</button>
    </form>
  );
}
