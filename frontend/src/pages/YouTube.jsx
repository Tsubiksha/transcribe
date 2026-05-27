import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clapperboard, Clock3, Loader2, MessageSquareText, Play, Search, Video, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { cancelJob, getJob, isTerminalJob, listActiveJobs } from "../api/jobs";
import { fetchYouTubeMetadata, formatDuration, listYouTubeSources, processYouTubeUrl } from "../api/youtube";
import { Card, Page, Reveal } from "../components/Motion";

function youtubeId(url) {
  const match = url.match(/(?:v=|youtu\.be\/|shorts\/)([a-zA-Z0-9_-]{6,})/);
  return match?.[1] || "";
}

const stages = [
  ["pending", "Queued"],
  ["captions", "Checking captions"],
  ["downloading", "Downloading audio"],
  ["converting", "Extracting audio"],
  ["transcribing", "Transcribing audio"],
  ["chunking", "Creating chunks"],
  ["embedding", "Generating embeddings"],
  ["saving_source", "Saving source"],
  ["completed", "Completed"]
];

function stageIndex(stage) {
  return Math.max(0, stages.findIndex(([value]) => value === stage));
}

function completionMessage(response) {
  const sourceTitle = response?.title || response?.source_name || "YouTube video";
  const chunksCount = response?.chunks_count ?? response?.chunk_count ?? response?.chunks_stored ?? 0;
  if (!chunksCount) {
    return "Processing completed, but no transcript chunks were created. Please check transcription.";
  }
  return `Indexed ${sourceTitle} with ${chunksCount} chunks.`;
}

export default function YouTube() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [metadataLoading, setMetadataLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [sources, setSources] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [activeJob, setActiveJob] = useState(null);
  const [thumbLoaded, setThumbLoaded] = useState(false);
  const id = useMemo(() => youtubeId(url), [url]);
  const progress = useMemo(() => {
    if (activeJob?.status === "completed" && (activeJob?.chunks_count > 0 || activeJob?.chunks_stored > 0)) return 100;
    if (activeJob?.status === "failed") return activeJob?.percentage || 0;
    if (activeJob) return activeJob.percentage ?? activeJob.progress ?? 8;
    return lastResult ? 100 : 0;
  }, [activeJob, lastResult]);
  const activeStageIndex = activeJob ? stageIndex(activeJob.stage) : (lastResult ? stages.length : -1);

  const loadSources = () => listYouTubeSources().then((data) => {
    setSources(data);
    return data;
  }).catch(() => {
    setSources([]);
    return [];
  });

  useEffect(() => {
    loadSources();
    listActiveJobs().then((jobs) => {
      const youtubeJob = jobs.find((job) => job.job_type === "youtube");
      if (youtubeJob) setActiveJob(youtubeJob);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setThumbLoaded(false);
    setMetadata(null);
    if (!id || !url.trim()) return;
    const timer = window.setTimeout(async () => {
      setMetadataLoading(true);
      try {
        const data = await fetchYouTubeMetadata(url);
        setMetadata(data);
      } catch {
        setMetadata(null);
      } finally {
        setMetadataLoading(false);
      }
    }, 700);
    return () => window.clearTimeout(timer);
  }, [id, url]);

  useEffect(() => {
    if (!activeJob?.job_id || isTerminalJob(activeJob)) return;
    const timer = window.setInterval(async () => {
      try {
        const next = await getJob(activeJob.job_id);
        setActiveJob(next);
        if (next.status === "completed") {
          const chunksCount = next.chunks_count ?? next.chunk_count ?? next.chunks_stored ?? 0;
          const refreshedSources = await loadSources();
          const sourceExists = refreshedSources.some((source) => String(source.id) === String(next.source_id) && source.status === "ready" && (source.chunks_count > 0));
          setStatus({
            type: chunksCount && next.source_id && sourceExists ? "success" : "error",
            text: chunksCount && next.source_id && sourceExists
              ? completionMessage(next)
              : "Processing completed, but the source is not ready in Sources yet. Please refresh and check transcription."
          });
          setLastResult(sourceExists ? next : null);
        }
        if (next.status === "failed") setStatus({ type: "error", text: next.error_message || "YouTube processing failed." });
        if (next.status === "cancelled") setStatus({ type: "error", text: "YouTube processing cancelled." });
      } catch (err) {
        setStatus({ type: "error", text: err.message || "Could not read processing status." });
        await loadSources();
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [activeJob?.job_id, activeJob?.status]);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    setLastResult(null);
    try {
      const job = await processYouTubeUrl(url);
      if (!job?.job_id) {
        throw new Error("Backend did not return a processing job id.");
      }
      setActiveJob(job);
      setStatus({ type: "success", text: "Processing started. Large videos may take several minutes." });
      setUrl("");
    } catch (err) {
      setStatus({ type: "error", text: err.message || "Could not start YouTube processing" });
    } finally {
      setLoading(false);
    }
  };

  const cancelActiveJob = async () => {
    if (!activeJob?.job_id) return;
    const next = await cancelJob(activeJob.job_id);
    setActiveJob(next);
    setStatus({ type: "error", text: "Cancellation requested." });
  };

  return (
    <Page>
      <Reveal>
        <span className="chip mb-4"><Video className="h-3.5 w-3.5 text-rose-300" /> YouTube ingestion</span>
        <h1 className="text-3xl font-black tracking-tight md:text-4xl">Process YouTube videos</h1>
        <p className="mt-3 max-w-2xl text-slate-400">Paste a YouTube URL, preview the video, then save it into Sources for retrieval and timestamp chat. Large videos may take several minutes.</p>
      </Reveal>

      <section className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <Reveal className="media-panel animated-border p-6">
          <form onSubmit={submit} className="space-y-5">
            <div className="relative">
              <Video className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-rose-300" />
              <input className="field pl-12" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://www.youtube.com/watch?v=..." required />
            </div>
            <div className="alert alert-info flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>Large videos may take several minutes. You can continue using the app while processing continues.</span>
            </div>
            <div className="overflow-hidden rounded-3xl border border-white/10 bg-slate-950 shadow-2xl shadow-black/20">
              {id ? (
                <div className="relative aspect-video overflow-hidden">
                  {!thumbLoaded && <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900" />}
                  <img
                    className={`h-full w-full object-cover transition duration-700 ${thumbLoaded ? "scale-100 opacity-100" : "scale-105 opacity-0"}`}
                    src={`https://img.youtube.com/vi/${id}/maxresdefault.jpg`}
                    alt="YouTube thumbnail preview"
                    onLoad={() => setThumbLoaded(true)}
                  />
                </div>
              ) : (
                <div className="grid aspect-video place-items-center bg-[linear-gradient(135deg,#211925,#17233e)] text-center">
                  <div>
                    <Play className="mx-auto h-12 w-12 text-rose-200" />
                    <p className="mt-3 text-sm text-slate-400">Thumbnail appears after you paste a link</p>
                  </div>
                </div>
              )}
              <div className="grid gap-3 p-5 md:grid-cols-3">
                <div><p className="text-xs text-slate-500">Title</p><p className="truncate text-sm font-semibold">{metadataLoading ? "Fetching metadata..." : metadata?.title || (id ? "YouTube video preview" : "Awaiting link")}</p></div>
                <div><p className="text-xs text-slate-500">Channel</p><p className="truncate text-sm font-semibold">{metadata?.channel || (id ? "Detected after processing" : "--")}</p></div>
                <div><p className="text-xs text-slate-500">Duration</p><p className="text-sm font-semibold">{metadata?.duration ? formatDuration(metadata.duration) : (id ? "Fetched by backend" : "--")}</p></div>
              </div>
            </div>
            <button className="btn-primary w-full" disabled={loading || (activeJob && !isTerminalJob(activeJob))}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              {activeJob && !isTerminalJob(activeJob) ? "Processing in background..." : "Process and save source"}
            </button>
            {lastResult?.source_id && (
              <div className="grid gap-3 sm:grid-cols-2">
                <Link className="btn-primary" to={`/chat?source_id=${lastResult.source_id}`}><MessageSquareText className="h-4 w-4" /> Open Chat</Link>
                <Link className="btn-secondary" to="/sources">View Source</Link>
              </div>
            )}
            {status && <p className={`alert ${status.type === "success" ? "alert-success" : "alert-error"}`}>{status.text}</p>}
          </form>
        </Reveal>

        <div className="space-y-5">
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-bold">Processing progress</h2>
              <span className="text-sm text-slate-400">{progress}%</span>
            </div>
            <div className="mb-4 h-2 rounded-full bg-slate-800">
              <div className="h-2 rounded-full bg-[linear-gradient(90deg,#fb7185,#8f9cff,#4bb7f0)] transition-all duration-700" style={{ width: `${progress}%` }} />
            </div>
            {activeJob && !isTerminalJob(activeJob) && (
              <button className="btn-secondary mb-4 w-full hover:border-red-300/40 hover:text-red-200" type="button" onClick={cancelActiveJob}>
                <XCircle className="h-4 w-4" />
                Cancel processing
              </button>
            )}
            {stages.map(([value, step], index) => (
              <div key={value} className="mb-3 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-3 transition hover:border-blue-300/20 hover:bg-white/[0.07]">
                {activeJob && !isTerminalJob(activeJob) && index >= activeStageIndex ? <Loader2 className="h-5 w-5 animate-spin text-rose-200" /> : <CheckCircle2 className="h-5 w-5 text-blue-300" />}
                <span className="text-sm">{step}</span>
              </div>
            ))}
            {activeJob?.status === "failed" && <p className="alert alert-error mt-2 text-xs">{activeJob.error_message}</p>}
            {activeJob?.status === "completed" && activeJob?.source_id && (activeJob?.chunks_count || activeJob?.chunks_stored) > 0 && <span className="chip mt-2">Transcript ready</span>}
          </Card>
          <Card>
            <h2 className="mb-4 font-bold">Recently processed</h2>
            <div className="space-y-3">
              {(sources.length ? sources.slice(0, 4) : [{ title: "No YouTube videos yet", duration: 0 }]).map((source, index) => (
                <div key={source.id || index} className="flex items-center gap-3 rounded-2xl bg-white/[0.04] p-3 transition hover:bg-white/[0.07]">
                  <div className="grid h-11 w-11 place-items-center rounded-xl bg-rose-500/15"><Clapperboard className="h-5 w-5 text-rose-200" /></div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold">{source.title}</p>
                    <p className="flex items-center gap-1 text-xs text-slate-500"><Clock3 className="h-3 w-3" /> {formatDuration(source.duration)}</p>
                  </div>
                </div>
              ))}
            </div>
            <Link className="btn-secondary mt-4 w-full" to={sources[0]?.id ? `/chat?source_id=${sources[0].id}` : "/chat"}>Go to Chat</Link>
          </Card>
        </div>
      </section>
      {status && <div className={`toast ${status.type === "success" ? "alert-success" : "alert-error"}`}>{status.text}</div>}
    </Page>
  );
}
