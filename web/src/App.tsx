import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  api,
  type ExportFormat,
  type Letter,
  type Settings,
} from "./api";
import { Field, Panel, Toast } from "./ui";

const EXPORTS: ExportFormat[] = ["pdf", "docx", "html", "markdown", "txt"];

// Fixed set of supported output languages — a button group, so the user can
// never type a value the model has to guess at.
const LANGUAGES: { code: string; label: string }[] = [
  { code: "en", label: "English" },
  { code: "pt", label: "Português" },
  { code: "es", label: "Español" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
];

type ProfileMode = "manual" | "upload";
type EditMode = "ai" | "manual";

export function App() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [toast, setToast] = useState<{ msg: string; kind: "ok" | "err" } | null>(null);

  // intake
  const [name, setName] = useState("");
  const [profileMode, setProfileMode] = useState<ProfileMode>("manual");
  const [background, setBackground] = useState("");
  const [fileName, setFileName] = useState("");
  // The profile we're currently editing. When set, saves PATCH this row instead
  // of creating a new one — so generating repeatedly no longer spawns duplicates.
  const [currentProfileId, setCurrentProfileId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDesc, setJobDesc] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  // generation / editor
  const [letter, setLetter] = useState<Letter | null>(null);
  const [content, setContent] = useState("");
  const [editMode, setEditMode] = useState<EditMode>("ai");
  const [language, setLanguage] = useState("en");
  const [instruction, setInstruction] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .getSettings()
      .then((s) => {
        setSettings(s);
        setLanguage(s.default_language);
      })
      .catch((e) => flash(e.message ?? "Could not load settings", "err"));
  }, []);

  // Prefill from the most recent saved profile so the user doesn't re-enter
  // name + CV on every run. Picks the highest id (autoincrement = newest).
  useEffect(() => {
    api
      .listProfiles()
      .then((profiles) => {
        if (!profiles.length) return;
        const latest = profiles.reduce((a, b) => (b.id > a.id ? b : a));
        setCurrentProfileId(latest.id);
        setName(latest.name);
        setBackground(latest.background_text);
        setProfileMode(latest.source);
        flash(`Loaded your saved profile “${latest.name}”.`, "ok");
      })
      .catch(() => {
        /* no saved profile yet — start blank */
      });
  }, []);

  function flash(msg: string, kind: "ok" | "err") {
    setToast({ msg, kind });
    window.setTimeout(() => setToast(null), 3200);
  }

  function providerUsable(p: string): boolean {
    return p === "ollama" || (settings?.providers_with_keys.includes(p) ?? false);
  }

  async function selectProvider(p: string) {
    if (!settings || settings.ai_provider === p) return;
    try {
      const updated = await api.updateSettings({ ai_provider: p });
      setSettings(updated);
      flash(`AI provider set to ${p}.`, "ok");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Could not change provider", "err");
    }
  }

  async function uploadCV(file: File) {
    setFileName(file.name);
    try {
      const profile = await api.uploadProfile(name || "My profile", file);
      // The uploaded profile becomes the one we're editing, so later saves
      // PATCH it instead of piling up new rows.
      setCurrentProfileId(profile.id);
      setProfileMode("upload");
      setBackground(profile.background_text);
      if (!profile.background_text.trim()) {
        flash("Little text extracted — the file may be scanned. Edit it below.", "err");
      } else {
        flash("CV text extracted — review and edit below.", "ok");
      }
    } catch (e) {
      flash(e instanceof Error ? e.message : "Upload failed", "err");
    }
  }

  const canGenerate = name.trim() && background.trim() && title.trim() && jobDesc.trim() && !busy;

  // Persist the background to the current profile (PATCH), or create one the
  // first time (POST). Returns the profile id to generate against.
  async function saveProfile(): Promise<number> {
    const body = {
      name: name.trim(),
      background_text: background.trim(),
      source: profileMode,
    };
    const profile = currentProfileId
      ? await api.updateProfile(currentProfileId, body)
      : await api.createProfile(body);
    setCurrentProfileId(profile.id);
    return profile.id;
  }

  // Start a fresh profile — the next save creates a new row instead of editing.
  function newProfile() {
    setCurrentProfileId(null);
    setName("");
    setBackground("");
    setFileName("");
    setProfileMode("manual");
    flash("Started a new profile.", "ok");
  }

  async function generate() {
    setBusy(true);
    try {
      const profileId = await saveProfile();
      const job = await api.createJob({
        title: title.trim(),
        company: company.trim() || null,
        description: jobDesc.trim(),
      });
      const result = await api.generate({
        profile_id: profileId,
        job_id: job.id,
        language,
        provider: settings?.ai_provider,
      });
      setLetter(result);
      setContent(result.latest_version?.content ?? "");
      setEditMode("ai");
      flash("Cover letter generated.", "ok");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Generation failed", "err");
    } finally {
      setBusy(false);
    }
  }

  async function regenerate() {
    if (!letter || !instruction.trim()) return;
    setBusy(true);
    try {
      const version = await api.regenerate({
        letter_id: letter.id,
        instruction: instruction.trim(),
        language,
      });
      setContent(version.content);
      setEditMode("ai");
      setInstruction("");
      flash("Revised.", "ok");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Revision failed", "err");
    } finally {
      setBusy(false);
    }
  }

  function download(fmt: ExportFormat) {
    if (!letter) return;
    window.open(api.exportUrl(letter.id, fmt), "_blank");
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>Cover Letter Generator</h1>
          <span>local-first · BYO key + local AI</span>
        </div>
        {settings && (
          <div className="toggle providers" role="group" aria-label="AI provider">
            {settings.available_providers.map((p) => {
              const usable = providerUsable(p);
              return (
                <button
                  key={p}
                  type="button"
                  aria-pressed={settings.ai_provider === p}
                  onClick={() => selectProvider(p)}
                  title={
                    usable
                      ? `Use ${p}`
                      : `Set CLG_${p.toUpperCase()}_API_KEY in your .env to use ${p}`
                  }
                >
                  <span className={`dot ${usable ? "ok" : "err"}`} />
                  {p}
                  {p === "ollama" ? " · local" : ""}
                </button>
              );
            })}
          </div>
        )}
      </header>

      <div className="workspace">
        {/* ---- Intake ---- */}
        <div>
          <Panel title="Your background" hint="Upload a CV or paste it — text stays on your machine.">
            <div className="toolbar" style={{ marginBottom: "0.6rem" }}>
              <span className="hint">
                {currentProfileId ? "Editing your saved profile" : "New profile"}
              </span>
              <button className="btn btn-ghost" onClick={newProfile} disabled={!currentProfileId && !name && !background}>
                New profile
              </button>
            </div>
            <Field label="Your name">
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Developer" />
            </Field>

            <div className="toggle" role="group" aria-label="Background source" style={{ marginBottom: "0.9rem" }}>
              <button aria-pressed={profileMode === "manual"} onClick={() => setProfileMode("manual")}>
                Paste text
              </button>
              <button aria-pressed={profileMode === "upload"} onClick={() => setProfileMode("upload")}>
                Upload CV
              </button>
            </div>

            {profileMode === "upload" && (
              <div style={{ marginBottom: "0.9rem" }}>
                <input
                  ref={fileInput}
                  type="file"
                  accept=".pdf,.docx"
                  hidden
                  onChange={(e) => e.target.files?.[0] && uploadCV(e.target.files[0])}
                />
                <button className="btn btn-ghost" onClick={() => fileInput.current?.click()}>
                  Choose PDF or DOCX
                </button>
                {fileName && <span className="chip" style={{ marginLeft: "0.6rem" }}>{fileName}</span>}
              </div>
            )}

            <Field label="Background (experience, education, projects, achievements)">
              <textarea
                className="textarea"
                value={background}
                onChange={(e) => setBackground(e.target.value)}
                placeholder="10 years building backend systems in Go and Python; led a team of 6; shipped…"
              />
            </Field>
          </Panel>

          <Panel title="The job" hint="What role are you applying for?">
            <div className="row">
              <Field label="Job title">
                <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Staff Engineer" />
              </Field>
              <Field label="Company (optional)">
                <input className="input" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Acme" />
              </Field>
            </div>
            <Field label="Job description">
              <textarea className="textarea" value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} placeholder="Paste the job posting…" />
            </Field>
            <Field label="Letter language">
              <div className="toggle wrap" role="group" aria-label="Letter language">
                {LANGUAGES.map((l) => (
                  <button
                    key={l.code}
                    type="button"
                    aria-pressed={language === l.code}
                    onClick={() => setLanguage(l.code)}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </Field>
            <button className="btn btn-primary" onClick={generate} disabled={!canGenerate} style={{ width: "100%" }}>
              {busy && !letter ? "Generating…" : "Generate cover letter"}
            </button>
          </Panel>
        </div>

        {/* ---- Editor ---- */}
        <Panel title="Your letter" hint="Switch between the AI draft and manual editing.">
          <div className="toolbar">
            <div className="toggle" role="group" aria-label="Edit mode">
              <button aria-pressed={editMode === "ai"} onClick={() => setEditMode("ai")} disabled={!letter}>
                AI draft
              </button>
              <button aria-pressed={editMode === "manual"} onClick={() => setEditMode("manual")}>
                Edit manually
              </button>
            </div>
            <div className="exports">
              {EXPORTS.map((fmt) => (
                <button key={fmt} className="btn btn-ghost" onClick={() => download(fmt)} disabled={!letter}>
                  {fmt.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <AnimatePresence mode="wait">
            {editMode === "manual" ? (
              <motion.textarea
                key="edit"
                className="textarea"
                style={{ minHeight: 320, fontFamily: "var(--font-serif)" }}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              />
            ) : !letter ? (
              <motion.div key="empty" className="preview empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                Your generated cover letter will appear here.
              </motion.div>
            ) : (
              <motion.div key="view" className="preview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {content}
              </motion.div>
            )}
          </AnimatePresence>

          {letter && (
            <div className="row" style={{ marginTop: "1rem", alignItems: "flex-end" }}>
              <Field label="Ask the AI to revise (e.g. “make it more concise”)">
                <input
                  className="input"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && regenerate()}
                  placeholder="make it shorter and warmer"
                />
              </Field>
              <button className="btn btn-primary" onClick={regenerate} disabled={busy || !instruction.trim()} style={{ flex: "0 0 auto" }}>
                {busy ? "Revising…" : "Revise"}
              </button>
            </div>
          )}
          {editMode === "manual" && (
            <p className="hint" style={{ marginTop: "0.6rem" }}>
              {letter
                ? "Note: exports use the latest AI-generated version; manual edits here are for your reference."
                : "Generate a letter first to export — text typed here isn’t saved or exported yet."}
            </p>
          )}
        </Panel>
      </div>

      <Toast message={toast?.msg ?? null} kind={toast?.kind ?? "ok"} />
    </div>
  );
}
