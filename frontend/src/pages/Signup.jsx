import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Sparkles } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import AuthShell from "../components/AuthShell";

export default function Signup() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.email, form.password, "signup");
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Create your workspace"
      subtitle="Start chatting with videos, podcasts, lectures, and YouTube links."
      onSubmit={submit}
      footer={<p className="mt-6 text-center text-sm text-slate-400">Already have an account? <Link className="font-semibold text-blue-300" to="/login">Log in</Link></p>}
    >
      {error && <p className="alert alert-error mb-4">{error}</p>}
      <div className="space-y-4">
        <input className="field" type="email" placeholder="Email address" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <div className="relative">
          <input className="field pr-12" minLength="6" type={showPassword ? "text" : "password"} placeholder="Create password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" onClick={() => setShowPassword((value) => !value)} title={showPassword ? "Hide password" : "Show password"}>
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        <button className="btn-primary w-full" disabled={loading}>{loading ? "Creating..." : "Create account"} <Sparkles className="h-4 w-4" /></button>
      </div>
    </AuthShell>
  );
}
