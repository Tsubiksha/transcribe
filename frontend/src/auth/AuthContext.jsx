import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(token));

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const loadUser = async () => {
    if (!localStorage.getItem("token")) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/api/auth/me");
      setUser(data);
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
    window.addEventListener("auth:logout", logout);
    return () => window.removeEventListener("auth:logout", logout);
  }, []);

  const login = async (email, password, mode = "login") => {
    const { data } = await api.post(`/api/auth/${mode}`, { email, password });
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    await loadUser();
  };

  const value = useMemo(() => ({ token, user, loading, login, logout, loadUser }), [token, user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
