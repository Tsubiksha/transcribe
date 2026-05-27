import React from "react";
import { motion } from "framer-motion";

export const fadeUp = {
  hidden: { opacity: 0, y: 16, filter: "blur(6px)" },
  show: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } }
};

export const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } }
};

export function Page({ children, className = "" }) {
  return (
    <motion.div
      className={`space-y-6 ${className}`}
      initial="hidden"
      animate="show"
      variants={stagger}
    >
      {children}
    </motion.div>
  );
}

export function Reveal({ children, className = "" }) {
  return (
    <motion.div variants={fadeUp} className={className}>
      {children}
    </motion.div>
  );
}

export function Card({ children, className = "" }) {
  return (
    <motion.div
      variants={fadeUp}
      whileHover={{ y: -3 }}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
      className={`card ${className}`}
    >
      {children}
    </motion.div>
  );
}
