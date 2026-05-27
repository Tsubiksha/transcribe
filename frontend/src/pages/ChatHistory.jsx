import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  CalendarDays,
  Clock3,
  Edit3,
  MessageSquareText,
  Play,
  Search,
  Trash2,
  Video,
  X
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import api from "../api/axios";
import { Page, Reveal } from "../components/Motion";

const filters = [
  ["all", "All"],
  ["today", "Today"],
  ["yesterday", "Yesterday"],
  ["week", "Previous 7 Days"],
  ["older", "Older"]
];

function startOfDay(date) {
  const next = new Date(date);
  next.setHours(0, 0, 0, 0);
  return next;
}

function safeDate(value) {
  const date = value ? new Date(value) : new Date();
  return Number.isNaN(date.getTime()) ? new Date() : date;
}

function lastUpdated(session) {
  const messages = session.messages || [];
  const newestMessage = messages.reduce((latest, message) => {
    const created = safeDate(message.created_at);
    return created > latest ? created : latest;
  }, safeDate(session.created_at));
  return newestMessage;
}

function filterBucket(session) {
  const createdDay = startOfDay(safeDate(session.created_at));
  const today = startOfDay(new Date());
  const diffDays = Math.floor((today - createdDay) / 86400000);
  if (diffDays === 0) return "today";
  if (diffDays === 1) return "yesterday";
  if (diffDays >= 2 && diffDays <= 7) return "week";
  return "older";
}

function formatDate(value) {
  return safeDate(value).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function formatDateTime(value) {
  return safeDate(value).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function getTitle(session, aliases) {
  return aliases[session.session_id] || session.title || session.source_title || `Conversation ${session.session_id}`;
}

function getPreview(session) {
  const messages = session.messages || [];
  const last = messages[messages.length - 1];
  return last?.question || last?.answer || "Empty conversation";
}

function SourceThumbnail({ session }) {
  if (session.source_thumbnail_url) {
    return <img src={session.source_thumbnail_url} alt="" className="h-full w-full object-cover" />;
  }
  return (
    <div className="grid h-full w-full place-items-center bg-[linear-gradient(135deg,#111827,#1f3b58,#312e81)] text-blue-100">
      {session.source_type === "youtube" ? <Video className="h-6 w-6" /> : <MessageSquareText className="h-6 w-6" />}
    </div>
  );
}

export default function ChatHistory() {
  const [history, setHistory] = useState([]);
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [aliases, setAliases] = useState(() => JSON.parse(localStorage.getItem("chat_aliases") || "{}"));
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const activeSessionId = searchParams.get("session_id");

  const load = () => api.get("/api/chat/history").then(({ data }) => setHistory(data)).catch(() => setHistory([]));
  useEffect(() => { load(); }, []);

  const visibleHistory = useMemo(() => {
    return history
      .filter((session) => {
        const text = `${getTitle(session, aliases)} ${getPreview(session)} ${session.source_type || ""}`.toLowerCase();
        const matchesSearch = text.includes(query.toLowerCase());
        const matchesDate = activeFilter === "all" || filterBucket(session) === activeFilter;
        return matchesSearch && matchesDate;
      })
      .sort((a, b) => lastUpdated(b) - lastUpdated(a));
  }, [history, aliases, query, activeFilter]);

  const startRename = (session) => {
    setEditingId(session.session_id);
    setEditingTitle(getTitle(session, aliases));
  };

  const saveRename = (event) => {
    event?.preventDefault();
    if (!editingTitle.trim()) return;
    const updated = { ...aliases, [editingId]: editingTitle.trim() };
    setAliases(updated);
    localStorage.setItem("chat_aliases", JSON.stringify(updated));
    setEditingId(null);
    setEditingTitle("");
  };

  const remove = async () => {
    if (!deleteTarget) return;
    await api.delete(`/api/chat/history/${deleteTarget.session_id}`);
    setHistory((items) => items.filter((item) => item.session_id !== deleteTarget.session_id));
    setDeleteTarget(null);
  };

  const openChat = (session) => navigate(`/chat?session_id=${session.session_id}`);

  return (
    <Page className="space-y-6">
      <Reveal className="premium-panel overflow-hidden p-6 md:p-8">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
          <div>
            <span className="chip mb-4">
              <Clock3 className="h-3.5 w-3.5 text-blue-300" />
              Conversation management
            </span>
            <h1 className="text-3xl font-black tracking-tight md:text-5xl">History</h1>
            <p className="mt-3 max-w-2xl text-slate-500">Search, rename, continue, and clean up timestamp conversations from one dedicated workspace.</p>
          </div>
        </div>
      </Reveal>

      <Reveal className="chat-focus p-5 md:p-6">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto] lg:items-center">
          <div className="flex items-center gap-3 rounded-2xl border px-4 py-3" style={{ borderColor: "var(--line)", background: "var(--field)" }}>
            <Search className="h-4 w-4 text-slate-500" />
            <input className="w-full bg-transparent text-sm outline-none placeholder:text-slate-500" placeholder="Search chats" value={query} onChange={(event) => setQuery(event.target.value)} />
          </div>
          <div className="flex flex-wrap gap-2">
            {filters.map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => setActiveFilter(value)}
                className={`rounded-full border px-4 py-2 text-xs font-semibold transition ${
                  activeFilter === value
                    ? "border-slate-950 bg-slate-950 text-white dark:border-white/20 dark:bg-white/15"
                    : "border-transparent text-slate-500 hover:bg-slate-500/10"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between border-y py-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500" style={{ borderColor: "var(--line)" }}>
          <span>{visibleHistory.length} conversations</span>
          <span className="inline-flex items-center gap-2">
            <CalendarDays className="h-4 w-4" />
            Sorted by latest activity
          </span>
        </div>

        <div className="thin-scrollbar mt-5 max-h-[calc(100vh-22rem)] min-h-[360px] space-y-3 overflow-y-auto pr-1">
          {visibleHistory.map((session) => (
            <motion.article
              key={session.session_id}
              layout
              onClick={() => openChat(session)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => event.key === "Enter" && openChat(session)}
              className={`group grid cursor-pointer gap-4 rounded-2xl border p-4 transition duration-300 hover:-translate-y-0.5 hover:shadow-xl md:grid-cols-[92px_1fr_auto] ${
                String(activeSessionId) === String(session.session_id)
                  ? "border-blue-300/40 bg-blue-400/10"
                  : "border-white/10 bg-white/[0.045] hover:border-blue-300/25 hover:bg-white/[0.07]"
              }`}
            >
              <div className="h-24 overflow-hidden rounded-2xl border border-white/10 md:h-full">
                <SourceThumbnail session={session} />
              </div>

              <div className="min-w-0">
                {editingId === session.session_id ? (
                  <form className="flex gap-2" onSubmit={saveRename} onClick={(event) => event.stopPropagation()}>
                    <input className="field py-2" value={editingTitle} onChange={(event) => setEditingTitle(event.target.value)} autoFocus />
                    <button className="btn-primary px-3 py-2" type="submit">Save</button>
                    <button className="btn-secondary px-3 py-2" type="button" onClick={() => setEditingId(null)} title="Cancel rename">
                      <X className="h-4 w-4" />
                    </button>
                  </form>
                ) : (
                  <h2 className="truncate text-lg font-bold">{getTitle(session, aliases)}</h2>
                )}
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">{getPreview(session)}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="chip">{session.source_type || "source"}</span>
                  <span className="chip">Created {formatDate(session.created_at)}</span>
                  <span className="chip">Updated {formatDateTime(lastUpdated(session))}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 md:opacity-0 md:transition md:group-hover:opacity-100" onClick={(event) => event.stopPropagation()}>
                <button className="btn-secondary px-3 py-2" type="button" onClick={() => openChat(session)} title="Continue chat">
                  <Play className="h-4 w-4" />
                </button>
                <button className="btn-secondary px-3 py-2" type="button" onClick={() => startRename(session)} title="Rename chat">
                  <Edit3 className="h-4 w-4" />
                </button>
                <button className="btn-secondary px-3 py-2 hover:border-red-300/40 hover:text-red-200" type="button" onClick={() => setDeleteTarget(session)} title="Delete chat">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </motion.article>
          ))}

          {visibleHistory.length === 0 && (
            <div className="grid min-h-[360px] place-items-center rounded-2xl border text-center" style={{ borderColor: "var(--line)", background: "var(--field)" }}>
              <div>
                <MessageSquareText className="mx-auto h-14 w-14 text-slate-400" />
                <h2 className="mt-4 text-xl font-bold">{history.length ? "No matching conversations" : "No conversations yet"}</h2>
                <p className="mt-2 text-sm text-slate-500">Try another search or start a new chat from the sidebar.</p>
              </div>
            </div>
          )}
        </div>
      </Reveal>

      <AnimatePresence>
        {deleteTarget && (
          <motion.div
            className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-6 text-white shadow-2xl"
              initial={{ scale: 0.96, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.96, y: 10 }}
            >
              <h2 className="text-xl font-bold">Delete conversation?</h2>
              <p className="mt-2 text-sm leading-6 text-slate-300">This removes "{getTitle(deleteTarget, aliases)}" and all saved messages from history.</p>
              <div className="mt-6 flex justify-end gap-2">
                <button className="btn-secondary" type="button" onClick={() => setDeleteTarget(null)}>Cancel</button>
                <button className="btn-primary" type="button" onClick={remove}>
                  <Trash2 className="h-4 w-4" />
                  Delete
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Page>
  );
}
