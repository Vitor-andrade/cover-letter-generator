// Shared UI primitives: motion-aware panel, fields, toast, stepper, section editors.
import { AnimatePresence, motion } from "framer-motion";
import { Fragment, type ReactNode, useState } from "react";

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

export type TabDef = { key: string; label: string; filled: boolean };

// Sub-navigation across the profile sections, with a filled/empty dot per tab so
// the user sees at a glance which sections already have content.
export function SectionTabs({
  tabs,
  active,
  onSelect,
}: {
  tabs: TabDef[];
  active: string;
  onSelect: (key: string) => void;
}) {
  return (
    <nav className="section-tabs" aria-label="Profile sections">
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          className={`section-tab ${active === t.key ? "active" : ""}`}
          aria-current={active === t.key ? "true" : undefined}
          onClick={() => onSelect(t.key)}
        >
          <span className={`tab-dot ${t.filled ? "filled" : ""}`} />
          {t.label}
        </button>
      ))}
    </nav>
  );
}

// A tag editor backed by string[] — type + Enter (or blur) to add, click a chip
// to remove, Backspace on an empty input to pop the last.
export function ChipsInput({
  values,
  onChange,
  placeholder,
}: {
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}) {
  const [draft, setDraft] = useState("");
  function add() {
    const v = draft.trim();
    if (v && !values.includes(v)) onChange([...values, v]);
    setDraft("");
  }
  return (
    <div className="chips">
      {values.map((v, i) => (
        <button
          key={`${v}-${i}`}
          type="button"
          className="chip removable"
          onClick={() => onChange(values.filter((_, j) => j !== i))}
        >
          {v} ×
        </button>
      ))}
      <input
        className="chips-input"
        value={draft}
        placeholder={placeholder ?? "Add…"}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={add}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            add();
          } else if (e.key === "Backspace" && !draft && values.length) {
            onChange(values.slice(0, -1));
          }
        }}
      />
    </div>
  );
}

// Generic editor for a list of structured entries (experiences, projects, …):
// add a blank entry, remove, and reorder; the caller renders each entry's fields.
export function ListEditor<T>({
  items,
  onChange,
  blank,
  renderItem,
  addLabel,
}: {
  items: T[];
  onChange: (next: T[]) => void;
  blank: () => T;
  renderItem: (item: T, update: (patch: Partial<T>) => void) => ReactNode;
  addLabel: string;
}) {
  const update = (i: number, patch: Partial<T>) =>
    onChange(items.map((it, j) => (j === i ? { ...it, ...patch } : it)));
  const remove = (i: number) => onChange(items.filter((_, j) => j !== i));
  function move(i: number, dir: -1 | 1) {
    const j = i + dir;
    if (j < 0 || j >= items.length) return;
    const next = items.slice();
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  }
  return (
    <div className="list-editor">
      {items.map((item, i) => (
        <div key={i} className="entry-card">
          <div className="entry-controls">
            <button className="btn btn-ghost btn-xs" onClick={() => move(i, -1)} disabled={i === 0}>
              ↑
            </button>
            <button
              className="btn btn-ghost btn-xs"
              onClick={() => move(i, 1)}
              disabled={i === items.length - 1}
            >
              ↓
            </button>
            <button className="btn btn-ghost btn-xs" onClick={() => remove(i)}>
              Remove
            </button>
          </div>
          {renderItem(item, (patch) => update(i, patch))}
        </div>
      ))}
      <button className="btn btn-ghost" onClick={() => onChange([...items, blank()])}>
        {addLabel}
      </button>
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
