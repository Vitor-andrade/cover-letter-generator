// Shared UI primitives: motion-aware panel, fields, toast, stepper.
import { AnimatePresence, motion } from "framer-motion";
import { Fragment, type ReactNode } from "react";

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

export type StepDef = { key: string; label: string };

// A linear progress indicator. Earlier (completed) steps and the current one
// render filled; a step is clickable only when `isEnabled` allows it, so the
// user can jump back freely but can't skip ahead past an unmet gate.
export function Stepper({
  steps,
  current,
  isEnabled,
  onSelect,
}: {
  steps: StepDef[];
  current: string;
  isEnabled: (key: string) => boolean;
  onSelect: (key: string) => void;
}) {
  const currentIndex = steps.findIndex((s) => s.key === current);
  return (
    <nav className="stepper" aria-label="Progress">
      {steps.map((s, i) => {
        const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "todo";
        const enabled = isEnabled(s.key);
        return (
          <Fragment key={s.key}>
            {i > 0 && <span className={`stepper-line ${i <= currentIndex ? "filled" : ""}`} />}
            <button
              type="button"
              className={`stepper-step ${state}`}
              aria-current={state === "current" ? "step" : undefined}
              disabled={!enabled}
              onClick={() => enabled && onSelect(s.key)}
            >
              <span className="stepper-index">{state === "done" ? "✓" : i + 1}</span>
              <span className="stepper-label">{s.label}</span>
            </button>
          </Fragment>
        );
      })}
    </nav>
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
