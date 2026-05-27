import React, { useEffect, useState } from "react";
import { Bell, Bot, Database, LogOut, Save, SlidersHorizontal, Upload, UserRound } from "lucide-react";
import api from "../api/axios";
import { useAuth } from "../auth/AuthContext";
import { Card, Page, Reveal } from "../components/Motion";
import { useTheme } from "../theme/ThemeContext";

function Toggle({ checked, onChange }) {
  return (
    <button type="button" onClick={() => onChange(!checked)} className={`h-7 w-12 rounded-full p-1 transition ${checked ? "bg-[linear-gradient(110deg,#8f9cff,#4bb7f0)]" : "bg-black/70"}`}>
      <span className={`block h-5 w-5 rounded-full bg-white transition ${checked ? "translate-x-5" : ""}`} />
    </button>
  );
}

export default function Profile() {
  const { user, loadUser, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [form, setForm] = useState({ email: "", name: "", bio: "", profile_image_url: "", notification_enabled: true });
  const [message, setMessage] = useState("");
  const [imageError, setImageError] = useState("");
  const [saveHistory, setSaveHistory] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("chatSettings") || "{}");
    setSaveHistory(stored.saveHistory ?? true);
    setShowTimestamps(stored.showTimestamps ?? true);
    setAutoScroll(stored.autoScroll ?? true);
  }, []);

  const updateChatSetting = (key, value) => {
    const next = { saveHistory, showTimestamps, autoScroll, [key]: value };
    setSaveHistory(next.saveHistory);
    setShowTimestamps(next.showTimestamps);
    setAutoScroll(next.autoScroll);
    localStorage.setItem("chatSettings", JSON.stringify(next));
  };

  useEffect(() => {
    setForm({
      email: user?.email || "",
      name: user?.profile?.name || "",
      bio: user?.profile?.bio || "",
      profile_image_url: user?.profile?.profile_image_url || "",
      notification_enabled: user?.profile?.notification_enabled ?? true
    });
  }, [user]);

  const submit = async (e) => {
    e.preventDefault();
    await api.put("/api/profile", form);
    await loadUser();
    setMessage("Profile and settings saved");
  };

  const handleProfileImage = (event) => {
    const file = event.target.files?.[0];
    setImageError("");
    if (!file) return;
    if (!["image/png", "image/jpeg"].includes(file.type)) {
      setImageError("Upload a PNG, JPG, or JPEG image.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setForm((current) => ({ ...current, profile_image_url: String(reader.result || "") }));
    reader.readAsDataURL(file);
  };

  return (
    <Page>
      <Reveal className="lux-panel animated-border overflow-hidden">
        <div className="h-36 bg-[linear-gradient(115deg,rgba(143,156,255,0.28),rgba(255,255,255,0.08)_45%,rgba(230,160,111,0.2))]" />
        <div className="-mt-12 flex flex-col gap-4 p-6 md:flex-row md:items-end md:justify-between">
          <div className="flex items-end gap-4">
            <div className="grid h-24 w-24 overflow-hidden rounded-3xl border border-white/15 bg-black/55 text-blue-100 shadow-[0_18px_44px_rgba(20,24,36,0.24)]">
              {form.profile_image_url ? <img className="h-full w-full object-cover" src={form.profile_image_url} alt="Profile preview" /> : <UserRound className="m-auto h-10 w-10" />}
            </div>
            <div>
              <h1 className="text-3xl font-black">{form.name || "Workspace user"}</h1>
              <p className="text-slate-400">{form.email || "Signed in user"}</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            {["12 sources", "48 answers", "6.4 GB"].map((item) => <span key={item} className="rounded-2xl border border-white/10 bg-white/[0.05] px-4 py-3 text-sm font-semibold">{item}</span>)}
          </div>
        </div>
      </Reveal>

      <form onSubmit={submit} className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <div className="space-y-5">
          <Card>
            <div className="mb-5 flex items-center gap-3"><UserRound className="h-5 w-5 text-blue-300" /><h2 className="text-lg font-bold">Personal Information</h2></div>
            {message && <p className="alert alert-success mb-4">{message}</p>}
            <div className="grid gap-4 md:grid-cols-2">
              <input className="field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Display name" />
              <input className="field" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" />
              <label className="flex cursor-pointer items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/[0.055] px-4 py-3 text-sm text-slate-300 transition hover:border-blue-300/40 hover:bg-blue-400/[0.06] md:col-span-2">
                <Upload className="h-4 w-4" />
                Upload profile image (PNG, JPG, JPEG)
                <input className="sr-only" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" onChange={handleProfileImage} />
              </label>
              {imageError && <p className="alert alert-error md:col-span-2">{imageError}</p>}
              <textarea className="field min-h-28 md:col-span-2" value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} placeholder="Bio" />
            </div>
          </Card>

          <Card>
            <div className="mb-5 flex items-center gap-3"><Bot className="h-5 w-5 text-blue-300" /><h2 className="text-lg font-bold">AI Settings</h2></div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/[0.055] p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Local model</p>
                <p className="mt-2 font-semibold">llama3.2:3b</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.055] p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Whisper mode</p>
                <p className="mt-2 font-semibold">tiny / CPU optimized</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <div className="mb-5 flex items-center gap-3"><SlidersHorizontal className="h-5 w-5 text-blue-300" /><h2 className="text-lg font-bold">Appearance</h2></div>
            <div className="grid grid-cols-2 gap-3">
              {["light", "dark"].map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setTheme(mode)}
                  className={`rounded-2xl border p-4 text-left text-sm font-semibold capitalize transition hover:-translate-y-0.5 ${theme === mode ? "border-transparent text-white" : "border-white/10"}`}
                  style={theme === mode ? { background: "linear-gradient(110deg, var(--accent-a), var(--accent-b), var(--accent-c))" } : { background: "var(--field)", color: "var(--text)" }}
                >
                  {mode} mode
                  <span className="mt-1 block text-xs font-normal opacity-75">{mode === "light" ? "Clean silver workspace" : "Restrained cinematic depth"}</span>
                </button>
              ))}
            </div>
          </Card>
          <Card>
            <div className="mb-5 flex items-center gap-3"><SlidersHorizontal className="h-5 w-5 text-blue-300" /><h2 className="text-lg font-bold">Chat Settings</h2></div>
            <div className="space-y-4">
              {[["Save chat history", "saveHistory", saveHistory], ["Show timestamps", "showTimestamps", showTimestamps], ["Auto-scroll", "autoScroll", autoScroll]].map(([label, key, value]) => (
                <div key={label} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] p-4"><span className="text-sm">{label}</span><Toggle checked={value} onChange={(next) => updateChatSetting(key, next)} /></div>
              ))}
            </div>
          </Card>
          <Card>
            <div className="mb-5 flex items-center gap-3"><Bell className="h-5 w-5 text-violet-300" /><h2 className="text-lg font-bold">Notifications</h2></div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] p-4"><span className="text-sm">Upload complete alerts</span><Toggle checked={form.notification_enabled} onChange={(value) => setForm({ ...form, notification_enabled: value })} /></div>
          </Card>
          <Card>
            <div className="mb-5 flex items-center gap-3"><Database className="h-5 w-5 text-emerald-200" /><h2 className="text-lg font-bold">Storage Usage</h2></div>
            <div className="mb-3 flex justify-between text-sm"><span className="text-slate-400">Media library</span><span>6.4 GB / 20 GB</span></div>
            <div className="h-3 rounded-full bg-black/65"><div className="h-3 w-[32%] rounded-full bg-[linear-gradient(90deg,#8f9cff,#4bb7f0,#a985ff)]" /></div>
          </Card>
          <button type="button" className="btn-secondary w-full justify-start" onClick={logout}><LogOut className="h-4 w-4" /> Logout</button>
          <button className="btn-primary w-full"><Save className="h-4 w-4" /> Save changes</button>
        </div>
      </form>
    </Page>
  );
}
