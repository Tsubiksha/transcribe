import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Bot, Clock3, MessageSquareText, ShieldCheck, Sparkles } from "lucide-react";

export default function AuthShell({ title, subtitle, onSubmit, children, footer }) {
  return (
    <main className="app-shell relative grid min-h-screen overflow-hidden lg:grid-cols-[1fr_0.9fr]">
      <div className="page-atmosphere atmos-landing atmos-grid" />
      <section className="relative hidden items-center justify-center p-10 lg:flex">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="cinema-panel animated-border ambient-sheen relative max-w-xl p-8">
          <Link to="/" className="mb-8 inline-flex items-center gap-3 text-sm font-bold text-white">
            <span className="grid h-11 w-11 place-items-center rounded-2xl text-white" style={{ background: "linear-gradient(135deg, var(--accent-a), var(--accent-b))" }}><Sparkles className="h-5 w-5" /></span>
            AI RAG Studio
          </Link>
          <h1 className="text-5xl font-black tracking-tight">Timestamp intelligence for every recording.</h1>
          <p className="mt-5 text-lg leading-8 text-slate-300">Turn long media into searchable, conversational knowledge with local AI.</p>
          <div className="mt-8 grid gap-3">
            {[
              [MessageSquareText, "Chat with uploaded content"],
              [Clock3, "Jump to exact transcript timestamps"],
              [Bot, "Use local Ollama models"],
              [ShieldCheck, "Keep your media workspace private"]
            ].map(([Icon, text]) => (
              <div key={text} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.05] p-4">
                <Icon className="h-5 w-5 text-blue-200" />
                <span className="text-sm font-medium text-slate-200">{text}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </section>
      <section className="relative grid place-items-center px-5 py-10">
        <motion.form
          initial={{ opacity: 0, y: 18, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.45 }}
          className="glass-panel relative z-10 w-full max-w-md p-6 md:p-8"
          onSubmit={onSubmit}
        >
          <Link to="/" className="mb-8 flex items-center gap-3 text-sm font-bold text-white lg:hidden">
            <span className="grid h-10 w-10 place-items-center rounded-2xl text-white" style={{ background: "linear-gradient(135deg, var(--accent-a), var(--accent-b))" }}><Sparkles className="h-4 w-4" /></span>
            AI RAG Studio
          </Link>
          <h2 className="text-3xl font-black tracking-tight text-white">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">{subtitle}</p>
          <div className="mt-6">{children}</div>
          {footer}
        </motion.form>
      </section>
    </main>
  );
}
