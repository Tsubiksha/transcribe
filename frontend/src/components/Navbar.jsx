import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, Moon, Search, Sun } from "lucide-react";
import { motion } from "framer-motion";
import { useTheme } from "../theme/ThemeContext";

export default function Navbar({ onMenu }) {
  const [model, setModel] = useState("llama3.2:3b");
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    setModel(localStorage.getItem("aiModelPreference") || "llama3.2:3b");
  }, []);

  const updateModel = (value) => {
    setModel(value);
    localStorage.setItem("aiModelPreference", value);
  };

  const submitSearch = (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed) navigate(`/sources?search=${encodeURIComponent(trimmed)}`);
  };

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-30 border-b px-4 py-3 backdrop-blur-2xl md:px-6"
      style={{ borderColor: "var(--line)", background: "color-mix(in srgb, var(--shell) 78%, transparent)" }}
    >
      <div className="flex items-center gap-3">
        <button type="button" className="btn-secondary px-3 py-2 md:hidden" onClick={onMenu} title="Open navigation">
          <Menu className="h-5 w-5" />
        </button>
        <form onSubmit={submitSearch} className="min-w-0 flex-1 items-center gap-3 rounded-2xl px-4 py-3 shadow-inner sm:flex" style={{ border: "1px solid var(--line)", background: "var(--field)", color: "var(--muted)" }}>
          <Search className="h-4 w-4 shrink-0" style={{ color: "var(--accent-b)" }} />
          <input className="w-full bg-transparent text-sm outline-none placeholder:text-slate-500" placeholder="Search sources, chats, transcripts..." value={query} onChange={(event) => setQuery(event.target.value)} />
        </form>
        <select
          className="hidden rounded-2xl px-3 py-3 text-sm outline-none md:block"
          style={{ border: "1px solid var(--line)", background: "var(--field)", color: "var(--text)" }}
          value={model}
          onChange={(event) => updateModel(event.target.value)}
          title="Local AI model preference"
        >
          <option>llama3.2:3b</option>
          <option>phi3:mini</option>
          <option>qwen2.5-coder:3b</option>
        </select>
        <button type="button" className="btn-secondary px-3 py-3" onClick={toggleTheme} title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
      </div>
    </motion.header>
  );
}
