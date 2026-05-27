import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useSearchParams } from "react-router-dom";
import { Calendar, Clock3, MessageSquareText, Music2, Play, Trash2, Video } from "lucide-react";
import api from "../api/axios";
import { Card, Page, Reveal } from "../components/Motion";

function formatDuration(value) {
  if (!value) return "Unknown";
  const total = Math.round(value);
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export default function Sources() {
  const [sources, setSources] = useState([]);
  const [searchParams] = useSearchParams();
  const search = searchParams.get("search") || "";

  const load = () => api.get("/api/sources").then(({ data }) => setSources(data)).catch(() => setSources([]));
  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    await api.delete(`/api/sources/${id}`);
    setSources((items) => items.filter((item) => item.id !== id));
  };

  const visibleSources = sources.filter((source) => {
    const text = `${source.title || ""} ${source.source_type || ""}`.toLowerCase();
    return text.includes(search.toLowerCase());
  });

  return (
    <Page>
      <Reveal className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <span className="chip mb-4"><Video className="h-3.5 w-3.5 text-blue-300" /> Knowledge library</span>
          <h1 className="text-3xl font-black tracking-tight md:text-4xl">Sources</h1>
          <p className="mt-3 text-slate-400">{search ? `Showing sources matching "${search}".` : "Browse every indexed recording, transcript, and YouTube video in your RAG workspace."}</p>
        </div>
        <Link to="/upload" className="btn-primary">Add source</Link>
      </Reveal>

      {visibleSources.length === 0 ? (
        <Reveal className="glass-panel grid min-h-[420px] place-items-center p-8 text-center">
          <div>
            <Video className="mx-auto h-14 w-14 text-blue-300" />
            <h2 className="mt-4 text-2xl font-bold">{sources.length ? "No matching sources" : "No sources yet"}</h2>
            <p className="mx-auto mt-2 max-w-md text-slate-400">{sources.length ? "Try another search from the top bar." : "Upload media or process a YouTube link to create your searchable AI library."}</p>
            <div className="mt-6 flex justify-center gap-3"><Link className="btn-primary" to="/upload">Upload</Link><Link className="btn-secondary" to="/youtube">YouTube</Link></div>
          </div>
        </Reveal>
      ) : (
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {visibleSources.map((source) => (
            <Card key={source.id} className="overflow-hidden p-0">
              <div className="hero-device relative aspect-video overflow-hidden p-5">
                <div className="absolute inset-x-5 bottom-5 flex h-14 items-end gap-1">
                  {Array.from({ length: 30 }).map((_, index) => (
                    <span key={index} className="flex-1 rounded-full bg-blue-100/25" style={{ height: `${20 + (index * 17) % 70}%` }} />
                  ))}
                </div>
                <div className="relative flex items-center justify-between">
                  <span className="chip">{source.source_type === "youtube" ? <Video className="h-3 w-3" /> : <Music2 className="h-3 w-3" />} {source.source_type}</span>
                  <span className={`rounded-xl border px-3 py-2 text-xs font-semibold ${
                    source.status === "ready"
                      ? "border-emerald-200/15 bg-emerald-300/10 text-emerald-100"
                      : source.status === "failed"
                        ? "border-red-200/20 bg-red-400/10 text-red-100"
                        : "border-amber-200/20 bg-amber-300/10 text-amber-100"
                  }`}>
                    {source.status || "ready"}
                  </span>
                </div>
                <div className="absolute left-5 top-1/2 grid h-14 w-14 -translate-y-1/2 place-items-center rounded-2xl bg-black/55 text-blue-100 backdrop-blur"><Play className="h-6 w-6" /></div>
              </div>
              <div className="p-5">
                <h2 className="line-clamp-2 min-h-[3rem] text-lg font-bold">{source.title}</h2>
                <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-slate-400">
                  <span className="chip"><Clock3 className="h-3 w-3" /> {formatDuration(source.duration)}</span>
                  <span className="chip"><MessageSquareText className="h-3 w-3" /> {source.chunks_count || 0} chunks</span>
                  <span className="chip"><Calendar className="h-3 w-3" /> recent</span>
                </div>
                {source.status === "failed" && source.error_message && (
                  <p className="mt-3 rounded-xl border border-red-300/20 bg-red-500/10 p-3 text-xs leading-5 text-red-100">{source.error_message}</p>
                )}
                <div className="mt-5 flex gap-2">
                  {source.status === "ready" && (source.chunks_count || 0) > 0 ? (
                    <Link to={`/chat?source_id=${source.id}`} className="btn-primary flex-1 py-2">Open chat</Link>
                  ) : (
                    <button className="btn-secondary flex-1 py-2" type="button" disabled>
                      {source.status === "failed" ? "Chat unavailable" : "Processing"}
                    </button>
                  )}
                  <button className="btn-secondary px-3 py-2" onClick={() => remove(source.id)} title="Delete source"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
            </Card>
          ))}
        </section>
      )}
    </Page>
  );
}
