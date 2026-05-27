import { Navigate, Outlet } from "react-router-dom";
import React from "react";
import { useAuth } from "./AuthContext";
import LoadingSpinner from "../components/LoadingSpinner";

export default function ProtectedRoute() {
  const { token, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center"><LoadingSpinner /></div>;
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}
