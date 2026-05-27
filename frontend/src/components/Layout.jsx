import React, { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { pathname } = useLocation();
  const atmosphere = pathname.startsWith("/chat")
    ? "atmos-chat"
    : pathname.startsWith("/youtube")
      ? "atmos-youtube"
      : pathname.startsWith("/profile") || pathname.startsWith("/settings")
        ? "atmos-profile"
        : "atmos-dashboard";

  return (
    <div className="app-shell relative overflow-hidden">
      <div className={`page-atmosphere atmos-grid fixed ${atmosphere}`} />
      <div className="relative z-10 flex gap-4 p-3 md:p-4">
        <Sidebar />
        <div className="theme-surface min-w-0 flex-1 overflow-hidden rounded-3xl">
          <Navbar onMenu={() => setMobileOpen(true)} />
          <main className="mx-auto w-full max-w-[1560px] p-4 md:p-6">
            <Outlet />
          </main>
        </div>
      </div>
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="fixed inset-0 z-50 bg-black/60 p-3 backdrop-blur-sm md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileOpen(false)}
          >
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              onClick={(event) => event.stopPropagation()}
              className="h-full w-80 max-w-[92vw]"
            >
              <Sidebar mobile onNavigate={() => setMobileOpen(false)} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
