import React from "react";
import { Link } from "react-router-dom";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { ArrowRight, Bot, Clock3, FileSearch, MessageSquareText, Moon, Play, Radio, Sparkles, Sun, Video, Waves } from "lucide-react";
import { Card, Page, Reveal } from "../components/Motion";
import { useTheme } from "../theme/ThemeContext";

const features = [
  [MessageSquareText, "Media-native AI chat", "Questions stay grounded in transcript chunks, source context, and conversation memory."],
  [Clock3, "Glowing timestamp jumps", "Every answer can become a cinematic navigation point back into the original moment."],
  [Video, "YouTube to source memory", "Process public videos into your private, searchable RAG library."],
  [FileSearch, "Transcript intelligence", "Search retrieved passages and keep the media player, transcript, and chat synchronized."],
  [Bot, "Local model workflow", "Run Ollama and Whisper locally for a portfolio-ready private AI stack."],
  [Radio, "Command-center experience", "Designed around media decisions, learning, lectures, and long-form research."]
];

function HeroPreview({ x, y }) {
  const rotateX = useTransform(y, [0, 1], [5, -5]);
  const rotateY = useTransform(x, [0, 1], [-8, 8]);

  return (
    <motion.div style={{ rotateX, rotateY, transformPerspective: 900 }} className="relative mx-auto max-w-xl">
      <div className="cinema-panel animated-border ambient-sheen relative overflow-hidden p-4">
        <div className="aspect-video rounded-[1.25rem] border border-white/10 bg-black p-3">
          <div className="hero-device flex h-full flex-col justify-between rounded-2xl p-4">
            <div className="flex items-center justify-between">
              <span className="chip"><Play className="h-3 w-3" /> Lecture.mp4</span>
              <motion.span className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs text-slate-100" animate={{ opacity: [0.78, 1, 0.78] }} transition={{ duration: 2.8, repeat: Infinity }}>12:20</motion.span>
            </div>
            <div className="space-y-3">
              <div className="h-2 w-5/6 rounded-full bg-white/20" />
              <div className="h-2 w-2/3 rounded-full bg-white/10" />
              <div className="h-1.5 rounded-full bg-white/10">
                <motion.div className="h-1.5 rounded-full bg-[linear-gradient(90deg,#8f9cff,#4bb7f0,#a985ff)]" initial={{ width: "12%" }} animate={{ width: "72%" }} transition={{ repeat: Infinity, repeatType: "reverse", duration: 3.4, ease: "easeInOut" }} />
              </div>
            </div>
          </div>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_0.8fr]">
          <div className="rounded-2xl border border-white/10 bg-white/[0.07] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><Bot className="h-4 w-4 text-blue-200" /> AI answer</div>
            <motion.p className="text-sm leading-6 text-slate-300" initial={{ opacity: 0.72 }} animate={{ opacity: 1 }} transition={{ repeat: Infinity, repeatType: "reverse", duration: 1.8 }}>
              The speaker maps vector retrieval to transcript chunks, then ties the answer back to exact media timestamps.
            </motion.p>
          </div>
          <div className="space-y-3">
            {["12:20 to 15:40", "18:04 to 19:12"].map((item, index) => (
              <motion.div key={item} className="rounded-2xl border border-white/10 bg-white/[0.06] p-3 text-sm font-semibold text-blue-100" animate={{ y: [0, index ? 4 : -4, 0] }} transition={{ duration: 5.5, repeat: Infinity, delay: index * 0.4, ease: "easeInOut" }}>
                {item}
                <p className="mt-1 text-xs font-normal text-slate-400">Jump to timestamp</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function Landing() {
  const { theme, toggleTheme } = useTheme();
  const mouseX = useMotionValue(0.5);
  const mouseY = useMotionValue(0.5);
  const springX = useSpring(mouseX, { stiffness: 80, damping: 18 });
  const springY = useSpring(mouseY, { stiffness: 80, damping: 18 });
  const scrollToDemo = () => document.getElementById("demo-chat")?.scrollIntoView({ behavior: "smooth" });

  const handleMouseMove = (event) => {
    mouseX.set(event.clientX / window.innerWidth);
    mouseY.set(event.clientY / window.innerHeight);
  };

  return (
    <main className="app-shell relative overflow-hidden" onMouseMove={handleMouseMove}>
      <div className="page-atmosphere atmos-landing atmos-grid" />
      <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-5">
        <Link to="/" className="flex items-center gap-3 font-bold">
          <span className="grid h-11 w-11 place-items-center rounded-2xl text-white shadow-lg" style={{ background: "linear-gradient(135deg, var(--accent-a), var(--accent-b), var(--accent-c))" }}><Sparkles className="h-5 w-5" /></span>
          AI Audio/Video RAG
        </Link>
        <div className="flex items-center gap-3">
          <button type="button" className="btn-secondary hidden px-3 sm:inline-flex" onClick={toggleTheme} title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <Link className="btn-secondary hidden sm:inline-flex" to="/login">Login</Link>
          <Link className="btn-primary" to="/signup">Get Started</Link>
        </div>
      </nav>

      <Page className="relative z-10 mx-auto max-w-7xl px-5 pb-12 pt-8 md:pt-16">
        <section className="grid items-center gap-12 lg:grid-cols-[1fr_0.9fr]">
          <Reveal>
            <span className="chip mb-5"><Waves className="h-3.5 w-3.5 text-emerald-200" /> Cinematic AI media intelligence</span>
            <h1 className="max-w-4xl text-5xl font-black tracking-tight md:text-7xl">
              Turn every recording into an <span className="gradient-text">interactive AI memory</span>
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              Upload videos, lectures, podcasts, or YouTube links and ask questions with timestamp-aware answers, live transcript context, and a futuristic media workspace.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/signup" className="btn-primary">Get Started <ArrowRight className="h-4 w-4" /></Link>
              <button className="btn-secondary" type="button" onClick={scrollToDemo}><Play className="h-4 w-4" /> Watch Demo</button>
            </div>
          </Reveal>
          <HeroPreview x={springX} y={springY} />
        </section>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map(([Icon, title, text], index) => (
            <Card key={title} className="ambient-sheen bg-white/[0.055]">
              <Icon className="mb-5 h-7 w-7 text-blue-200" />
              <h3 className="text-lg font-bold text-white">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
            </Card>
          ))}
        </section>

        <section className="cinema-panel animated-border p-6 md:p-8">
          <h2 className="section-title">Workflow</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-4">
            {["Upload", "Transcribe", "Ask", "Jump to timestamp"].map((step, index) => (
              <motion.div key={step} className="relative rounded-2xl border border-white/10 bg-white/[0.06] p-5" whileHover={{ y: -5 }}>
                <span className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-[linear-gradient(135deg,#8f9cff,#4bb7f0)] text-sm font-bold text-white">{index + 1}</span>
                <p className="font-semibold">{step}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <section id="demo-chat" className="grid gap-5 lg:grid-cols-[0.8fr_1fr]">
          <Reveal className="cinema-panel p-6">
            <h2 className="section-title">Demo Chat</h2>
            <p className="mt-3 text-slate-400">A cinematic conversation grounded in uploaded media and timestamp retrieval.</p>
          </Reveal>
          <Reveal className="cinema-panel space-y-4 p-5">
            <div className="ml-auto max-w-xl rounded-2xl bg-[linear-gradient(110deg,#8f9cff,#4bb7f0,#a985ff)] px-4 py-3 text-sm font-medium text-white">Where does the speaker explain embeddings?</div>
            <div className="max-w-xl rounded-2xl border border-white/10 bg-white/[0.07] px-4 py-3 text-sm leading-6 text-slate-200">
              Embeddings are introduced when the speaker describes converting transcript chunks into searchable vectors.
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="chip">12:20 to 15:40</span>
                <span className="chip">Confidence 0.87</span>
              </div>
            </div>
          </Reveal>
        </section>
      </Page>
    </main>
  );
}
