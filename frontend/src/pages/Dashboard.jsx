import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Clock3, FileVideo, MessageSquareText, UploadCloud, Video, Waves } from "lucide-react";
import api from "../api/axios";
import { Page, Reveal } from "../components/Motion";

const quickActions = [
  ["/upload", UploadCloud, "Upload media", "Turn local files into searchable memory"],
  ["/youtube", Video, "Process YouTube", "Capture public videos as timestamped sources"],
  ["/chat", MessageSquareText, "Ask a source", "Open the immersive transcript chat"]
];

function durationLabel(seconds) {
  if (!seconds) return "0m";
  const minutes = Math.round(seconds / 60);
  return minutes < 60 ? `${minutes}m` : `${(minutes / 60).toFixed(1)}h`;
}

export default function Dashboard() {
  const [sources, setSources] = useState([]);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api.get("/api/sources").then(({ data }) => setSources(data)).catch(() => setSources([]));
    api.get("/api/chat/history").then(({ data }) => setHistory(data)).catch(() => setHistory([]));
  }, []);

  const totals = useMemo(() => {
    const seconds = sources.reduce((sum, source) => sum + (source.duration || 0), 0);
    const answers = history.reduce((sum, session) => sum + (session.messages?.length || 0), 0);
    return { seconds, answers };
  }, [sources, history]);

  return (
    <Page className="space-y-8">
      <Reveal className="studio-panel animated-border ambient-sheen relative overflow-hidden p-6 md:p-9">
        <div className="absolute right-0 top-0 hidden h-full w-1/3 border-l border-white/10 bg-[linear-gradient(135deg,rgba(143,156,255,0.16),rgba(75,183,240,0.08))] md:block" />
        <div className="relative max-w-3xl">
          <span className="chip mb-5"><Waves className="h-3.5 w-3.5 text-blue-200" /> AI media command center</span>
          <h1 className="text-4xl font-black tracking-tight md:text-6xl">Your recordings, transformed into living knowledge.</h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-400">A focused workspace for processing media, reading transcript context, and asking timestamp-aware questions without dashboard clutter.</p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link className="btn-primary" to="/youtube">Process a YouTube link <ArrowUpRight className="h-4 w-4" /></Link>
            <Link className="btn-secondary" to="/upload">Upload media</Link>
          </div>
        </div>
      </Reveal>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          [FileVideo, "Sources", sources.length],
          [Clock3, "Media indexed", durationLabel(totals.seconds)],
          [MessageSquareText, "AI answers", totals.answers]
        ].map(([Icon, label, value]) => (
          <Reveal key={label} className="premium-panel p-5 transition duration-300 hover:-translate-y-0.5">
            <Icon className="mb-5 h-6 w-6 text-blue-400" />
            <p className="text-sm text-slate-400">{label}</p>
            <p className="mt-2 text-3xl font-black">{value}</p>
          </Reveal>
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1fr_0.9fr]">
        <Reveal className="studio-panel p-5">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-xl font-bold">Continue from recent sources</h2>
            <Link className="text-sm font-semibold text-blue-300" to="/sources">View all</Link>
          </div>
          <div className="space-y-3">
            {(sources.length ? sources.slice(0, 5) : [{ title: "No sources yet", source_type: "Start by uploading media", duration: 0 }]).map((source, index) => (
              <Link key={source.id || index} to="/chat" className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.055] p-4 transition duration-300 hover:-translate-y-0.5 hover:border-blue-300/30 hover:bg-white/[0.09]">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-400/10 text-blue-200"><FileVideo className="h-5 w-5" /></span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-semibold">{source.title}</span>
                  <span className="text-sm text-slate-500">{source.source_type} {source.duration ? `- ${durationLabel(source.duration)}` : ""}</span>
                </span>
                <ArrowUpRight className="h-4 w-4 text-slate-500 transition group-hover:text-blue-300" />
              </Link>
            ))}
          </div>
        </Reveal>

        <Reveal className="premium-panel p-5">
          <h2 className="mb-5 text-xl font-bold">Quick launch</h2>
          <div className="grid gap-3">
            {quickActions.map(([to, Icon, title, text]) => (
              <Link key={to} to={to} className="group rounded-2xl border border-white/10 bg-white/[0.055] p-5 transition duration-300 hover:-translate-y-0.5 hover:border-blue-300/30 hover:bg-white/[0.09]">
                <div className="flex items-center gap-4">
                  <span className="grid h-12 w-12 place-items-center rounded-2xl bg-[linear-gradient(135deg,rgba(143,156,255,0.18),rgba(75,183,240,0.12))]"><Icon className="h-5 w-5 text-blue-200" /></span>
                  <span>
                    <span className="block font-bold">{title}</span>
                    <span className="text-sm text-slate-500">{text}</span>
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </Reveal>
      </section>
    </Page>
  );
}
