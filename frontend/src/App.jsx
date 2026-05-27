import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Profile from "./pages/Profile";
import Upload from "./pages/Upload";
import YouTube from "./pages/YouTube";
import Chat from "./pages/Chat";
import ChatHistory from "./pages/ChatHistory";
import Sources from "./pages/Sources";
import Layout from "./components/Layout";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Navigate to="/profile" replace />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/youtube" element={<YouTube />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/history" element={<ChatHistory />} />
          <Route path="/sources" element={<Sources />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
