// Shared UI primitives: motion-aware panel, fields, toast.
import { AnimatePresence, motion } from "framer-motion";
import type { ReactNode } from "react";

export const panelMotion = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { type: "spring" as const, stiffness: 220, damping: 26 },
};

export function Panel({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <motion.section className="panel" {...panelMotion}>
      <h2>{title}</h2>
      {hint && <p className="hint">{hint}</p>}
      {children}
    </motion.section>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      {children}
    </div>
  );
}

export function Toast({ message, kind }: { message: string | null; kind: "ok" | "err" }) {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          className={`toast ${kind}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          role="status"
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
