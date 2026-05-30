// Settings modal: active provider + language, BYO API keys.
import { motion } from "framer-motion";
import { useState } from "react";
import { api, type Settings } from "./api";
import { Field } from "./ui";

const NEEDS_KEY = new Set(["gemini", "anthropic", "openai"]);

export function SettingsModal({
  settings,
  onClose,
  onSaved,
  onError,
}: {
  settings: Settings;
  onClose: () => void;
  onSaved: (s: Settings) => void;
  onError: (msg: string) => void;
}) {
  const [provider, setProvider] = useState(settings.ai_provider);
  const [language, setLanguage] = useState(settings.default_language);
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);

  const needsKey = NEEDS_KEY.has(provider);
  const hasKey = settings.providers_with_keys.includes(provider);

  async function save() {
    setBusy(true);
    try {
      if (needsKey && apiKey.trim()) {
        await api.setProviderKey(provider, apiKey.trim());
      }
      const updated = await api.updateSettings({
        ai_provider: provider,
        default_language: language,
      });
      onSaved(updated);
    } catch (e) {
      onError(e instanceof Error ? e.message : "Failed to save settings");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="scrim" onClick={onClose}>
      <motion.div
        className="panel modal"
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.94, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94 }}
        transition={{ type: "spring", stiffness: 260, damping: 24 }}
        role="dialog"
        aria-label="Settings"
      >
        <h2>Settings</h2>
        <p className="hint">Choose your AI provider. Ollama runs locally and is free.</p>

        <Field label="AI provider">
          <select className="select" value={provider} onChange={(e) => setProvider(e.target.value)}>
            {settings.available_providers.map((p) => (
              <option key={p} value={p}>
                {p}
                {p === "ollama" ? " (local, free)" : ""}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Default letter language">
          <input
            className="input"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            placeholder="en"
          />
        </Field>

        {needsKey && (
          <Field label={`API key for ${provider}${hasKey ? " (stored — leave blank to keep)" : ""}`}>
            <input
              className="input"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={hasKey ? "••••••••" : "paste your key"}
              autoComplete="off"
            />
          </Field>
        )}

        <div className="row" style={{ marginTop: "0.5rem" }}>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={save} disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
