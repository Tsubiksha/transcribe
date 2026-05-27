import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, FileAudio, FileVideo, Loader2, MessageSquareText, UploadCloud, Wand2, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import api, { getApiErrorMessage } from "../api/axios";
import { cancelJob, getJob, isTerminalJob, listActiveJobs } from "../api/jobs";
import { Card, Page, Reveal } from "../components/Motion";

const steps = [
  ["pending", "Queued"],
  ["converting", "Extracting audio"],
  ["transcribing", "Transcribing"],
  ["chunking", "Creating chunks"],
  ["embedding", "Generating embeddings"],
  ["saving_source", "Saving to Sources"],
  ["completed", "Completed"]
];
const formats = ["mp3", "wav", "m4a", "aac", "flac", "mp4", "mov", "mkv", "webm"];

function stepIndex(stage) {
  return Math.max(0, steps.findIndex(([value]) => value === stage));
}

export default function Upload() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("success");
  const [fileName, setFileName] = useState("");
  const [sources, setSources] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [activeJob, setActiveJob] = useState(null);

  const loadSources = () => api.get("/api/sources").then(({ data }) => {
    setSources(data);
    return data;
  }).catch(() => {
    setSources([]);
    return [];
  });
  useEffect(() => {
    loadSources();
    listActiveJobs().then((jobs) => {
      const uploadJob = jobs.find((job) => job.job_type === "upload");
      if (uploadJob) setActiveJob(uploadJob);
    }).catch(() => {});
  }, []);

  const progress = useMemo(() => {
    if (activeJob?.status === "completed" && (activeJob?.chunks_count > 0 || activeJob?.chunks_stored > 0)) return 100;
    if (activeJob?.status === "failed") return activeJob?.percentage || 0;
    if (activeJob) return activeJob.percentage ?? activeJob.progress ?? 18;
    return lastResult ? 100 : 0;
  }, [activeJob, lastResult]);
  const activeStepIndex = activeJob ? stepIndex(activeJob.stage) : (lastResult ? steps.length : -1);

  useEffect(() => {
    if (!activeJob?.job_id || isTerminalJob(activeJob)) return;
    const timer = window.setInterval(async () => {
      const next = await getJob(activeJob.job_id);
      setActiveJob(next);
      if (next.status === "completed") {
        setMessageType("success");
        setMessage("Upload source is ready for timestamp chat.");
        const refreshedSources = await loadSources();
        const sourceExists = refreshedSources.some((source) => String(source.id) === String(next.source_id) && source.status === "ready" && (source.chunks_count > 0));
        setLastResult(sourceExists ? next : null);
      }
      if (next.status === "failed") {
        setMessageType("error");
        setMessage(next.error_message || "Upload processing failed.");
      }
      if (next.status === "cancelled") {
        setMessageType("error");
        setMessage("Upload processing cancelled.");
      }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [activeJob?.job_id, activeJob?.status]);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setLastResult(null);
    const form = e.currentTarget;
    const formData = new FormData(form);
    try {
      const { data } = await api.post("/api/upload/process", formData, { headers: { "Content-Type": "multipart/form-data" }, timeout: 120000 });
      setMessageType("success");
      setMessage("Processing started. Large media may take several minutes.");
      setActiveJob(data);
      form.reset();
      setFileName("");
    } catch (err) {
      setMessageType("error");
      setMessage(getApiErrorMessage(err, "Could not start upload processing"));
    } finally {
      setLoading(false);
    }
  };

  const cancelActiveJob = async () => {
    if (!activeJob?.job_id) return;
    const next = await cancelJob(activeJob.job_id);
    setActiveJob(next);
    setMessageType("error");
    setMessage("Cancellation requested.");
  };

  return (
    <Page>
      <Reveal>
        <span className="chip mb-4"><UploadCloud className="h-3.5 w-3.5 text-emerald-200" /> Media ingestion</span>
        <h1 className="text-3xl font-black tracking-tight md:text-4xl">Upload audio or video</h1>
        <p className="mt-3 max-w-2xl text-slate-400">Drop in a recording and watch the AI pipeline extract, transcribe, chunk, and index it for timestamp Q&A.</p>
      </Reveal>

      <section className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <Reveal className="studio-panel p-6">
          <form onSubmit={submit} className="space-y-6">
            <label className="group relative flex min-h-[360px] cursor-pointer flex-col items-center justify-center overflow-hidden rounded-[1.5rem] border border-dashed border-blue-200/35 bg-[linear-gradient(135deg,rgba(143,156,255,0.12),rgba(75,183,240,0.08))] p-8 text-center transition duration-300 hover:-translate-y-0.5 hover:border-blue-200/70 hover:shadow-[0_24px_60px_rgba(79,70,229,0.14)]">
              <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,#8f9cff,#4bb7f0,transparent)] opacity-70" />
              <div className="relative grid h-20 w-20 place-items-center rounded-3xl bg-[linear-gradient(135deg,#8f9cff,#4bb7f0)] text-white shadow-[0_18px_40px_rgba(79,70,229,0.22)] transition duration-300 group-hover:scale-105">
                <UploadCloud className="h-9 w-9" />
              </div>
              <h2 className="mt-6 text-2xl font-bold">Drag, drop, or browse media</h2>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">Large lectures, podcasts, product demos, meetings, and videos are welcome.</p>
              <input
                className="sr-only"
                type="file"
                name="file"
                accept=".mp3,.wav,.m4a,.aac,.flac,.mp4,.mov,.mkv,.webm"
                required
                onChange={(event) => setFileName(event.target.files?.[0]?.name || "")}
              />
              {fileName && <span className="relative mt-5 rounded-2xl border border-blue-200/15 bg-black/55 px-4 py-2 text-sm text-blue-100">{fileName}</span>}
            </label>
            <div className="alert alert-info flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>Large files may take several minutes. You can leave this page; processing continues in the backend.</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {formats.map((format) => <span key={format} className="chip">{format}</span>)}
            </div>
            <button className="btn-primary w-full" disabled={loading || (activeJob && !isTerminalJob(activeJob))}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
              {activeJob && !isTerminalJob(activeJob) ? "Processing in background..." : "Upload and transcribe"}
            </button>
            {lastResult?.source_id && (
              <div className="grid gap-3 sm:grid-cols-2">
                <Link className="btn-primary" to={`/chat?source_id=${lastResult.source_id}`}><MessageSquareText className="h-4 w-4" /> Open Chat</Link>
                <Link className="btn-secondary" to="/sources">View Source</Link>
              </div>
            )}
            {message && <p className={`alert ${messageType === "success" ? "alert-success" : "alert-error"}`}>{message}</p>}
          </form>
        </Reveal>

        <div className="space-y-5">
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-bold">Processing pipeline</h2>
              <span className="text-sm text-slate-400">{progress}%</span>
            </div>
            <div className="mb-5 h-3 rounded-full bg-black/60"><div className="h-3 rounded-full bg-[linear-gradient(90deg,#8f9cff,#4bb7f0,#a985ff)] transition-all" style={{ width: `${progress}%` }} /></div>
            {activeJob && !isTerminalJob(activeJob) && (
              <button className="btn-secondary mb-4 w-full hover:border-red-300/40 hover:text-red-200" type="button" onClick={cancelActiveJob}>
                <XCircle className="h-4 w-4" />
                Cancel processing
              </button>
            )}
            <div className="space-y-3">
              {steps.map(([value, step], index) => (
                <div key={value} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-3">
                  {activeJob && !isTerminalJob(activeJob) && index >= activeStepIndex ? <Loader2 className="h-5 w-5 animate-spin text-blue-200" /> : <CheckCircle2 className="h-5 w-5 text-blue-300" />}
                  <span className="text-sm">{step}</span>
                </div>
              ))}
            </div>
            {activeJob?.status === "failed" && <p className="alert alert-error mt-4 text-xs">{activeJob.error_message}</p>}
          </Card>
          <Card>
            <h2 className="mb-4 font-bold">Recent uploads</h2>
            <div className="space-y-3">
              {(sources.length ? sources.slice(0, 4) : [{ title: "Waiting for your first upload", source_type: "AI-ready source" }]).map((source, index) => (
                <div key={source.id || index} className="flex items-center gap-3 rounded-2xl bg-white/[0.04] p-3">
                  <div className="grid h-10 w-10 place-items-center rounded-xl bg-blue-400/10">{source.source_type === "youtube" ? <FileVideo className="h-5 w-5 text-blue-200" /> : <FileAudio className="h-5 w-5 text-blue-300" />}</div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">{source.title}</p>
                    <p className="text-xs text-slate-500">{source.source_type}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </section>
      {message && <div className={`toast ${messageType === "success" ? "alert-success" : "alert-error"}`}>{message}</div>}
    </Page>
  );
}
