import React, { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Bot,
  CheckCircle2,
  Clock3,
  FileSearch,
  Gauge,
  PlayCircle,
  Send,
  Sparkles,
  UserRound,
  Video
} from "lucide-react";
import api from "../api/axios";
import { Page, Reveal } from "../components/Motion";

const suggestedPrompts = [
  "Summarize this video",
  "Where does the introduction start?",
  "What are the key concepts discussed?",
  "Show timestamps for model evaluation",
  "What mistakes are explained in this video?"
];

function stamp(value) {
  if (value == null) return "--:--";
  const total = Math.floor(value);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}

function youtubeId(url) {
  if (!url) return "";
  const match = String(url).match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([^?&/]+)/);
  return match?.[1] || "";
}

function transcriptFromMessages(messages) {
  const snippets = messages.filter((message) => message.matched_text).map((message, index) => ({
    id: `${message.start_time || 0}-${index}`,
    start: message.start_time,
    end: message.end_time,
    text: message.matched_text,
    confidence: message.confidence_score
  }));
  return snippets.length ? snippets : [
    { id: "empty-1", label: "Waiting for context", text: "Retrieved transcript chunks will appear here after your first grounded question.", start: null },
    { id: "empty-2", label: "Timestamp sync", text: "Timestamp chips and jump controls stay synchronized with the selected source.", start: null },
    { id: "empty-3", label: "Grounded answers", text: "Answers are constrained to uploaded media, transcripts, and processed YouTube content.", start: null }
  ];
}

function renderInlineMarkdown(text) {
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

function normalizeMarkdown(text) {
  return String(text || "")
    .replace(/\s+(\*\*[^*]{3,90}\*\*)/g, "\n\n$1")
    .replace(/(\*\*[^*]{3,90}\*\*)\s+(?=[*-]\s+)/g, "$1\n")
    .replace(/\s+([*-]\s+)/g, "\n$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function MarkdownAnswer({ text }) {
  const lines = normalizeMarkdown(text).split("\n");
  const blocks = [];
  let listItems = [];

  const flushList = () => {
    if (!listItems.length) return;
    blocks.push(
      <ul key={`list-${blocks.length}`} className="answer-list my-3 space-y-2 pl-5 text-[0.95rem] leading-7">
        {listItems.map((item, index) => (
          <li key={index} className="pl-1">{renderInlineMarkdown(item)}</li>
        ))}
      </ul>
    );
    listItems = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      return;
    }

    const bullet = line.match(/^[-*]\s+(.+)/);
    if (bullet) {
      listItems.push(bullet[1]);
      return;
    }

    flushList();
    const heading = line.match(/^\*\*([^*]+)\*\*:?\s*$/);
    if (heading) {
      blocks.push(
        <h3 key={`heading-${blocks.length}`} className="mt-5 first:mt-0 text-[1.02rem] font-black text-slate-50">
          {heading[1]}
        </h3>
      );
      return;
    }

    blocks.push(
      <p key={`paragraph-${blocks.length}`} className="answer-paragraph my-3 text-[0.95rem] font-medium leading-7">
        {renderInlineMarkdown(line)}
      </p>
    );
  });

  flushList();
  return <div className="answer-markdown">{blocks}</div>;
}

function ChatBubble({ message }) {
  const timestamps = message.timestamps?.length
    ? message.timestamps
    : message.start_time != null
      ? [{ start: stamp(message.start_time), end: stamp(message.end_time), start_seconds: message.start_time }]
      : [];
  const confidence = typeof message.confidence_score === "number" ? Math.round(message.confidence_score * 100) : null;

  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <div className="flex justify-end gap-3">
        <div className="max-w-[82%] rounded-2xl bg-[linear-gradient(115deg,#2563eb,#0891b2,#7c3aed)] px-5 py-4 text-sm font-bold leading-6 text-white shadow-[0_18px_38px_rgba(37,99,235,0.22)]">
          {message.question}
        </div>
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-slate-950 text-slate-100 shadow-lg shadow-slate-950/20">
          <UserRound className="h-4 w-4" />
        </div>
      </div>

      <div className="flex gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-cyan-200/20 bg-cyan-300/12 text-cyan-100 shadow-lg shadow-cyan-950/10">
          <Bot className="h-4 w-4" />
        </div>
        <div className="max-w-[92%] rounded-2xl border border-white/12 bg-[linear-gradient(180deg,rgba(255,255,255,0.09),rgba(255,255,255,0.045))] px-5 py-5 text-sm leading-7 text-slate-100 shadow-[0_22px_46px_rgba(2,8,23,0.20)] backdrop-blur">
          <div className="mb-3 flex flex-wrap gap-2">
            {message.source && <span className="chat-meta-chip">{message.source}</span>}
            {confidence != null && (
              <span className="chat-meta-chip">
                <Gauge className="h-3.5 w-3.5 text-cyan-200" />
                {confidence}% confidence
              </span>
            )}
          </div>
          <MarkdownAnswer text={message.answer} />
          {timestamps.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {timestamps.map((item, index) => (
                <button
                  key={`${item.start}-${index}`}
                  type="button"
                  className="inline-flex items-center gap-2 rounded-full border border-cyan-200/40 bg-cyan-300/18 px-3 py-2 text-xs font-black text-cyan-50 shadow-sm shadow-cyan-950/20 transition hover:-translate-y-0.5 hover:border-cyan-100/70 hover:bg-cyan-300/28"
                  onClick={() => window.dispatchEvent(new CustomEvent("media:seek", { detail: item.start_seconds }))}
                  title="Jump to transcript timestamp"
                >
                  <Clock3 className="h-3.5 w-3.5" />
                  {item.start} - {item.end}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function Chat() {
  const [searchParams] = useSearchParams();
  const [sources, setSources] = useState([]);
  const [sourceId, setSourceId] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mediaUrl, setMediaUrl] = useState("");
  const [sourceNotice, setSourceNotice] = useState("");
  const [transcriptQuery, setTranscriptQuery] = useState("");
  const mediaRef = useRef(null);
  const youtubeRef = useRef(null);

  useEffect(() => {
    const requestedSourceId = searchParams.get("source_id");
    const requestedSessionId = searchParams.get("session_id");
    const newChatToken = searchParams.get("new");

    if (newChatToken) {
      setSessionId(null);
      setMessages([]);
      setQuestion("");
    }

    api.get("/api/sources").then(({ data }) => {
      setSources(data);
      const requested = data.find((source) => String(source.id) === String(requestedSourceId));
      if (requested) setSourceId(String(requested.id));
      else if (!requestedSessionId && data[0]) setSourceId(String(data[0].id));
    }).catch(() => setSources([]));

    if (requestedSessionId) {
      api.get("/api/chat/history").then(({ data }) => {
        const session = data.find((item) => String(item.session_id) === String(requestedSessionId));
        if (session) openSession(session);
      }).catch(() => {});
    }
  }, [searchParams]);

  useEffect(() => {
    if (!sourceId) {
      setMediaUrl("");
      setSourceNotice("");
      return;
    }
    const selected = sources.find((source) => String(source.id) === String(sourceId));
    if (selected?.source_type === "youtube" && youtubeId(selected.youtube_url)) {
      setMediaUrl("");
      setSourceNotice("");
      return;
    }
    let objectUrl = "";
    setSourceNotice("");
    api.get(`/api/sources/${sourceId}/media`, { responseType: "blob" })
      .then(({ data }) => {
        objectUrl = URL.createObjectURL(data);
        setMediaUrl(objectUrl);
      })
      .catch((err) => {
        setMediaUrl("");
        setSourceNotice(err.response?.data?.detail || "Media is not available yet.");
      });
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [sourceId, sources]);

  useEffect(() => {
    const seek = (event) => {
      if (typeof event.detail !== "number") return;
      if (mediaRef.current) {
        mediaRef.current.currentTime = event.detail;
        mediaRef.current.play().catch(() => {});
        return;
      }
      if (youtubeRef.current?.contentWindow) {
        youtubeRef.current.contentWindow.postMessage(
          JSON.stringify({ event: "command", func: "seekTo", args: [event.detail, true] }),
          "*"
        );
        youtubeRef.current.contentWindow.postMessage(
          JSON.stringify({ event: "command", func: "playVideo", args: [] }),
          "*"
        );
      }
    };
    window.addEventListener("media:seek", seek);
    return () => window.removeEventListener("media:seek", seek);
  }, []);

  const activeSource = sources.find((source) => String(source.id) === String(sourceId));
  const activeYouTubeId = youtubeId(activeSource?.youtube_url);
  const sourceTitle = activeSource?.title || "";
  const sourceReady = Boolean(activeSource && activeSource.status === "ready" && (activeSource.chunks_count || 0) > 0);
  const readinessMessage = !activeSource
    ? "Select a source to start chatting."
    : activeSource.status !== "ready"
      ? "This source is still processing. Please wait."
      : (activeSource.chunks_count || 0) <= 0
        ? "Transcript chunks are not ready yet."
        : "";
  const transcript = useMemo(() => {
    const items = transcriptFromMessages(messages);
    if (!transcriptQuery.trim()) return items;
    return items.filter((item) => item.text.toLowerCase().includes(transcriptQuery.toLowerCase()));
  }, [messages, transcriptQuery]);

  function openSession(session) {
    setSessionId(session.session_id);
    setSourceId(String(session.source_id));
    setMessages((session.messages || []).map((message) => ({
      question: message.question,
      answer: message.answer,
      source: session.source_title,
      start_time: message.start_time,
      end_time: message.end_time,
      matched_text: message.matched_text,
      confidence_score: message.confidence_score
    })));
  }

  const submit = async (e) => {
    e.preventDefault();
    if (!question.trim() || !sourceId || !sourceReady) return;
    setLoading(true);
    setError("");
    const asked = question.trim();
    try {
      setMessages((items) => [...items, { question: asked, answer: "Reading transcript chunks...", pending: true }]);
      setQuestion("");
      const { data } = await api.post("/api/chat", { question: asked, source_id: Number(sourceId), session_id: sessionId });
      setSessionId(data.session_id);
      setMessages((items) => items.filter((item) => !item.pending).concat({ question: asked, ...data }));
    } catch (err) {
      setMessages((items) => items.filter((item) => !item.pending));
      setError(err.response?.data?.detail || "Chat failed. Check Ollama and try again.");
    } finally {
      setLoading(false);
    }
  };

  const askPrompt = (prompt) => setQuestion(prompt);

  const handleInputKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  return (
    <Page className="min-h-[calc(100vh-8rem)]">
      <section className="grid gap-5 xl:grid-cols-[minmax(360px,0.92fr)_minmax(420px,1.08fr)]">
        <Reveal className="space-y-5">
          <div className="chat-premium-panel overflow-hidden p-5">
            <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0">
                <span className="chat-meta-chip mb-3">
                  <PlayCircle className="h-3.5 w-3.5 text-cyan-200" />
                  {activeSource?.source_type || "source"} - {activeSource?.status || "select"}
                </span>
                <h1 className="truncate text-2xl font-black tracking-tight text-slate-50">{sourceTitle || "Select a source"}</h1>
                {activeSource && <p className="mt-2 text-xs font-bold text-slate-400">{activeSource.chunks_count || 0} transcript chunks</p>}
              </div>
              <select className="field max-w-full lg:max-w-72" value={sourceId} onChange={(e) => { setSourceId(e.target.value); setMessages([]); setSessionId(null); }}>
                <option value="">Choose source</option>
                {sources.map((source) => <option key={source.id} value={source.id}>{source.title}</option>)}
              </select>
            </div>

            <div className="overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl shadow-black/20">
              {activeYouTubeId ? (
                <iframe
                  ref={youtubeRef}
                  className="aspect-video w-full bg-black"
                  src={`https://www.youtube.com/embed/${activeYouTubeId}?enablejsapi=1&origin=${encodeURIComponent(window.location.origin)}`}
                  title={sourceTitle || "YouTube video player"}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                />
              ) : mediaUrl ? (
                <video ref={mediaRef} className="max-h-[46vh] w-full bg-black" controls src={mediaUrl} />
              ) : (
                <div className="grid aspect-video place-items-center bg-[linear-gradient(135deg,#111827,#1d2e42,#172554)] text-center">
                  <div>
                    <Video className="mx-auto h-12 w-12 text-blue-200" />
                    <p className="mt-3 text-sm text-slate-400">{sourceNotice || readinessMessage || "Media player appears when a source file is available."}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="chat-premium-panel p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-black text-slate-50">Transcript Context</h2>
                <p className="mt-1 text-xs font-semibold text-slate-400">Retrieved passages used by the assistant</p>
              </div>
              <div className="transcript-search flex min-w-[150px] items-center gap-2 rounded-xl px-3 py-2">
                <FileSearch className="h-4 w-4 text-cyan-200" />
                <input className="w-full bg-transparent text-xs font-semibold text-slate-100 outline-none placeholder:text-slate-500" placeholder="Search" value={transcriptQuery} onChange={(event) => setTranscriptQuery(event.target.value)} />
              </div>
            </div>
            <div className="thin-scrollbar max-h-[330px] space-y-3 overflow-y-auto pr-1">
              {transcript.map((item, index) => (
                <button
                  key={item.id}
                  type="button"
                  disabled={item.start == null}
                  onClick={() => item.start != null && window.dispatchEvent(new CustomEvent("media:seek", { detail: item.start }))}
                  className={`transcript-card w-full p-4 text-left transition disabled:cursor-default ${index === 0 ? "is-active" : ""}`}
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className="timestamp-pill">
                      <Clock3 className="h-3.5 w-3.5" />
                      {item.start == null ? item.label || "No timestamp yet" : `${stamp(item.start)} - ${stamp(item.end)}`}
                    </span>
                    {typeof item.confidence === "number" && <span className="chat-meta-chip">{Math.round(item.confidence * 100)}% match</span>}
                  </div>
                  <p className="line-clamp-4 text-sm font-medium leading-6 text-slate-300">{item.text}</p>
                </button>
              ))}
            </div>
          </div>
        </Reveal>

        <Reveal className="chat-premium-panel flex min-h-[760px] flex-col overflow-hidden">
          <div className="border-b p-5" style={{ borderColor: "var(--line)" }}>
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-slate-950 text-white shadow-sm dark:bg-white/10">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold">AI Timestamp Assistant</h2>
                <p className="text-xs font-semibold text-slate-400">Grounded retrieval only, with timestamp jumps when available</p>
              </div>
            </div>
          </div>

          {readinessMessage && <p className="alert alert-info mx-5 mt-4">{readinessMessage}</p>}
          {error && <p className="alert alert-error mx-5 mt-4">{error}</p>}

          <div className="thin-scrollbar flex-1 space-y-6 overflow-y-auto p-5">
            {messages.filter((item) => !item.pending).length === 0 ? (
              <div className="chat-empty-state grid min-h-full place-items-center rounded-2xl p-6 text-center">
                <div className="max-w-2xl">
                  <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl border" style={{ borderColor: "var(--line)", background: "var(--field)" }}>
                    <Bot className="h-8 w-8 text-slate-500" />
                  </div>
                  <h3 className="mt-5 text-2xl font-black tracking-tight">Hello</h3>
                  <p className="mt-3 text-lg font-semibold">I'm your AI Timestamp Assistant.</p>
                  <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">
                    Ask questions about your uploaded audio/video or YouTube source.
                  </p>
                  <div className="mt-6 flex flex-wrap justify-center gap-2">
                    {suggestedPrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => askPrompt(prompt)}
                        disabled={!sourceReady}
                        className="rounded-full border border-white/10 bg-white/[0.055] px-4 py-2 text-xs font-semibold text-slate-300 transition hover:-translate-y-0.5 hover:border-blue-300/30 hover:bg-blue-400/10 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : messages.filter((item) => !item.pending).map((message, index) => <ChatBubble key={index} message={message} />)}

            {loading && (
              <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-sm text-slate-300">
                <span className="mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-blue-300" />
                  Retrieving transcript chunks before answering...
                </span>
                <span className="block h-1.5 overflow-hidden rounded-full bg-white/10">
                  <motion.span className="block h-full w-1/3 rounded-full bg-[linear-gradient(90deg,#8f9cff,#4bb7f0)]" animate={{ x: ["-100%", "320%"] }} transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }} />
                </span>
              </div>
            )}
          </div>

          <form onSubmit={submit} className="border-t p-4" style={{ borderColor: "var(--line)" }}>
            <div className="flex items-end gap-2 rounded-2xl border p-2" style={{ borderColor: "var(--line)", background: "var(--field)" }}>
              <textarea
                className="max-h-32 min-h-[52px] flex-1 resize-none bg-transparent px-3 py-3 text-sm outline-none placeholder:text-slate-500"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Ask a grounded question about this media source..."
                disabled={!sourceReady}
                required
              />
              <button className="btn-primary px-4 py-3" disabled={loading || !sourceId || !sourceReady} title={!sourceId ? "Choose a source first" : readinessMessage || "Send message"}>
                {loading ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> : <Send className="h-4 w-4" />}
              </button>
            </div>
          </form>
        </Reveal>
      </section>
    </Page>
  );
}
