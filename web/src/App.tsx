import { useEffect, useState } from "react";

interface Health {
  status: string;
  version: string;
}

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main className="shell">
      <h1>Cover Letter Generator</h1>
      <p className="tagline">
        Local-first cover letters for international tech roles — BYO key + local AI.
      </p>
      <section className="status">
        {error && <span className="err">backend unreachable: {error}</span>}
        {health ? (
          <span className="ok">
            backend {health.status} · v{health.version}
          </span>
        ) : (
          !error && <span>connecting…</span>
        )}
      </section>
    </main>
  );
}
