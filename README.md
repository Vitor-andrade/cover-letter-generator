# Cover Letter Generator

Craft personalized, professional cover letters for international tech roles — **on your own machine**. Bring your own AI key, or run fully offline and free with [Ollama](https://ollama.com). Your CV and job details never leave your computer unless you choose a cloud provider.

- 🔒 **Local-first & private** — runs at `127.0.0.1`; no telemetry, no hosted backend.
- 🆓 **Free by default** — Ollama runs locally at zero cost; cloud providers are optional and pay-per-use with your own key.
- ✍️ **AI-assist ⇄ manual** — generate a tailored draft, then refine it by prompt or edit it yourself.
- 🌍 **Multi-language** — English-first, with a per-letter language override.
- 📄 **Export anywhere** — PDF, DOCX, HTML, Markdown, and TXT.

## How it works

You provide your background (paste it or upload a PDF/DOCX CV — parsed locally) and the job description. The app builds a tailored prompt and asks your chosen model to draft a cover letter, which you can revise or edit before exporting.

```
Browser (localhost) ─▶ FastAPI ─▶ generation ─▶ provider (Ollama / Gemini / Anthropic / OpenAI)
                                       │
                                   SQLite + encrypted key file (~/.clg)
```

See [`docs/clg-architecture-plan.md`](docs/clg-architecture-plan.md) for the full architecture, diagrams, and decision records.

## Quick start

> [!NOTE]
> Requires Python ≥ 3.11. [`uv`](https://docs.astral.sh/uv/) is the recommended launcher.

```bash
# Run without installing anything permanent:
uvx clg
```

This boots a local server and opens your browser. On first run it creates `~/.clg/` (owner-only) for the database and your encrypted API keys.

### Use the free local model (Ollama)

```bash
# Install Ollama (see https://ollama.com), then pull a model:
ollama pull llama3.1
```

Ollama is the default provider — no key required. Open **Settings** in the app to pick a different model.

### Use a cloud provider (bring your own key)

Open **Settings**, choose `gemini`, `anthropic`, or `openai`, and paste your API key. Keys are encrypted at rest (AES-256-GCM) and never sent anywhere except the provider you selected.

You can also configure via environment variables (prefix `CLG_`):

```bash
export CLG_AI_PROVIDER=anthropic
export CLG_ANTHROPIC_API_KEY=sk-...
export CLG_ANTHROPIC_MODEL=claude-sonnet-4-6
```

> [!TIP]
> Gemini's free tier is a good no-cost cloud option if you don't want to run a local model.

## Exporting to PDF

PDF export uses [WeasyPrint](https://weasyprint.org), which needs native libraries (cairo, pango).

> [!IMPORTANT]
> If PDF export reports missing libraries, install them per the [WeasyPrint install guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation). DOCX, HTML, Markdown, and TXT work without any extra system dependencies.

## Development

```bash
# Backend
uv sync --extra dev
uv run pytest              # tests
uv run ruff check .        # lint
uv run mypy                # types
uv run lint-imports        # architecture boundaries

# Frontend (web/)
cd web
npm install
npm run dev                # Vite dev server (proxies /api to :8000)
npm test                   # Vitest + React Testing Library
npm run build              # builds into src/clg/api/static/

# Run the assembled app
uv run clg
```

### Project layout

```
src/clg/
  bootstrap/     # launcher (uvx clg)
  api/           # FastAPI routers + DTOs (thin adapters)
  core/          # framework-agnostic domain
    ingestion/   # local CV parsing (pypdf / python-docx)
    generation/  # prompt building + orchestration
    providers/   # ollama / gemini / anthropic / openai + registry
    export/      # pdf / docx / html / markdown / txt renderers
    secrets/     # AES-256-GCM key store
    persistence/ # SQLModel entities + repositories
    config/      # CLG_-prefixed settings
web/             # React + Vite UI
```

## Privacy

By default, everything stays on your machine. Your CV is parsed locally, the database is a local SQLite file, and API keys are stored encrypted under `~/.clg/`. Content is sent to a third party **only** when you explicitly select a cloud provider for generation.
