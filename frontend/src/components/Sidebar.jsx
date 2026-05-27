import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Bot,
  ChevronLeft,
  Clapperboard,
  Clock3,
  Home,
  LogOut,
  MessageSquareText,
  Plus,
  Settings,
  Sparkles,
  UploadCloud,
  User,
  Video
} from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from "../auth/AuthContext";

const links = [
  ["/dashboard", Home, "Dashboard"],
  ["/upload", UploadCloud, "Upload"],
  ["/youtube", Video, "YouTube"],
  ["/chat", MessageSquareText, "Chat"],
  ["/history", Clock3, "History"],
  ["/sources", Clapperboard, "Sources"],
  ["/profile", Settings, "Profile & Settings"]
];

export default function Sidebar({ mobile = false, onNavigate }) {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const startNewChat = () => {
    navigate(`/chat?new=${Date.now()}`);
    onNavigate?.();
  };

  return (
    <motion.aside
      initial={{ opacity: 0, x: -18 }}
      animate={{ opacity: 1, x: 0 }}
      className={`${mobile ? "h-full" : "sticky top-4 hidden h-[calc(100vh-2rem)] md:flex"} ${
        collapsed ? "w-24" : "w-72"
      } shrink-0 flex-col rounded-[1.5rem] p-4 backdrop-blur transition-all duration-300`}
      style={{ border: "1px solid var(--line)", background: "var(--sidebar)", boxShadow: "0 24px 80px var(--shadow)" }}
    >
      <div className="mb-6 flex items-center justify-between gap-3">
        <NavLink to="/dashboard" onClick={onNavigate} className="flex min-w-0 items-center gap-3">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl text-white shadow-lg" style={{ background: "linear-gradient(135deg, var(--accent-a), var(--accent-b))" }}>
            <Bot size={22} />
          </span>
          {!collapsed && (
            <span className="min-w-0">
              <span className="block truncate text-sm font-bold text-white">AI RAG Studio</span>
              <span className="block truncate text-xs text-slate-400">Timestamp Q&A</span>
            </span>
          )}
        </NavLink>
        {!mobile && (
          <button
            type="button"
            className="rounded-xl border border-white/10 bg-white/[0.05] p-2 text-blue-100 transition hover:border-blue-200/30 hover:bg-blue-400/[0.1]"
            onClick={() => setCollapsed((value) => !value)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronLeft className={`h-4 w-4 transition ${collapsed ? "rotate-180" : ""}`} />
          </button>
        )}
      </div>

      <nav className="space-y-2">
        <button
          type="button"
          onClick={startNewChat}
          className="group relative flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5"
          style={{ background: "linear-gradient(110deg, var(--accent-a), var(--accent-b), var(--accent-c))" }}
          title={collapsed ? "New Chat" : undefined}
        >
          <Plus className="h-5 w-5 shrink-0" />
          {!collapsed && <span className="truncate">New Chat</span>}
        </button>
        {links.map(([to, Icon, label]) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition ${
                isActive
                  ? "text-white shadow-lg"
                  : "text-slate-400 hover:bg-white/[0.08]"
              }`
            }
            style={({ isActive }) => isActive ? { background: "linear-gradient(110deg, var(--accent-a), var(--accent-b))" } : undefined}
            title={collapsed ? label : undefined}
          >
            {({ isActive }) => (
              <>
                {isActive && <span className="absolute left-0 h-7 w-1 rounded-r-full bg-gradient-to-b from-blue-200 to-violet-300" />}
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span className="truncate">{label}</span>}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-3">
        <div className="rounded-2xl p-4" style={{ border: "1px solid var(--line)", background: "var(--accent-soft)" }}>
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold" style={{ color: "var(--accent-b)" }}>
            <Sparkles className="h-4 w-4" />
            {!collapsed && "AI model online"}
          </div>
          {!collapsed && <p className="text-xs leading-5 text-slate-400">llama3.2:3b with timestamp retrieval ready for grounded answers.</p>}
        </div>
        <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-3">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-blue-400/10 text-blue-100">
            <User className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-white">{user?.profile?.name || "Workspace user"}</p>
              <p className="truncate text-xs text-slate-400">{user?.email || "Signed in"}</p>
            </div>
          )}
          <button type="button" onClick={logout} className="rounded-xl p-2 text-slate-400 transition hover:bg-red-500/15 hover:text-red-200" title="Logout">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
