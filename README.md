# Cover Letter Generator

Craft personalized, professional cover letters for international tech roles — **on your own machine**. Bring your own AI key, or run fully offline and free with [Ollama](https://ollama.com). Your CV and job details never leave your computer unless you choose a cloud provider.

- 🔒 **Local-first & private** — runs at `127.0.0.1`; no telemetry, no hosted backend.
- 🆓 **Free by default** — Ollama runs locally at zero cost; cloud providers are optional and pay-per-use with your own key.
- 🧩 **Structured background** — organize your profile into sections (summary, skills, experience, projects, education, certifications, languages, …). Upload a CV and it's split into those sections locally. Your profile is saved between runs, so you fill it once.
- 🪜 **Guided flow** — a three-step wizard: background → generate → review.
- ✍️ **AI-assist ⇄ manual** — generate a tailored, one-page draft, then refine it by prompt or edit it yourself.
- 🌍 **Multi-language** — English-first, with a per-letter language picker (English, Português, Español, Français, Deutsch).
- 📄 **Export anywhere** — PDF, DOCX, HTML, Markdown, and TXT (your name is emphasized in the letter header).

## How it works

A three-step guided flow walks you from **background → generate → review**. You fill in your background in structured sections (or upload a PDF/DOCX CV, which is parsed and split into sections locally), then the job details. The app composes your sections into a tailored prompt and asks your chosen model to draft a one-page cover letter, which you can revise or edit before exporting. Your profile is saved locally and pre-loaded on the next run.

```
Browser (localhost) ─▶ FastAPI ─▶ generation ─▶ provider (Ollama / Gemini / Anthropic / OpenAI)
                                       │                         ▲
                                   SQLite (~/.clg)        keys from .env (CLG_*_API_KEY)
```

See [`docs/clg-architecture-plan.md`](docs/clg-architecture-plan.md) for the full architecture, diagrams, and decision records.

## Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| [Python](https://www.python.org/) | ≥ 3.11 | backend runtime |
| [uv](https://docs.astral.sh/uv/) | latest | dependency management & launcher |
| [Node.js](https://nodejs.org/) + npm | ≥ 18 | building the web UI from source |
| [Ollama](https://ollama.com) | latest | *optional* — free local AI (default provider) |

Install `uv` if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# then restart your shell, or: source $HOME/.local/bin/env
```

## Run it (from source)

> [!IMPORTANT]
> The web UI must be **built once** before the app can serve it. A fresh clone has no
> pre-built UI — skipping the build step shows only a JSON placeholder at `/`.

```bash
# 1. Clone
git clone https://github.com/Vitor-andrade/cover-letter-generator.git
cd cover-letter-generator

# 2. Install backend dependencies
uv sync

# 3. Configure (optional for Ollama) — copy the example and add your key
cp .env.example .env   # then edit .env if you use a cloud provider

# 4. Build the web UI (outputs into src/clg/api/static/)
cd web && npm install && npm run build && cd ..

# 5. Launch — starts the local server and opens your browser
uv run clg
```

That's it. On first run the app creates `~/.clg/` (owner-only) for its SQLite database. Provider API keys live in your `.env` (git-ignored), never in the database.

> [!TIP]
> To run on a fixed port without auto-opening the browser:
> ```bash
> CLG_PORT=8000 CLG_OPEN_BROWSER=false uv run clg
> ```

## Configure your AI provider

The app works out of the box with **Ollama** (local, free). To use it, install Ollama and pull a model:

```bash
ollama pull llama3.1
```

To use a cloud provider instead, add its API key to your `.env` and select the provider from the **header** in the app. Keys are read **only** from the environment/`.env` — the app never accepts a pasted key over HTTP, and never stores or returns key values. The header shows a green dot for any provider whose key is configured (Ollama is always available); switching providers is one click.

```dotenv
# .env
CLG_AI_PROVIDER=anthropic
CLG_ANTHROPIC_API_KEY=sk-ant-...
```

All settings can be passed as environment variables (prefix `CLG_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `CLG_AI_PROVIDER` | `ollama` | `ollama` \| `gemini` \| `anthropic` \| `openai` |
| `CLG_DEFAULT_LANGUAGE` | `en` | default letter language |
| `CLG_GEMINI_API_KEY` | _(unset)_ | API key for Gemini (required to use it) |
| `CLG_ANTHROPIC_API_KEY` | _(unset)_ | API key for Anthropic (required to use it) |
| `CLG_OPENAI_API_KEY` | _(unset)_ | API key for OpenAI (required to use it) |
| `CLG_HOST` | `127.0.0.1` | bind address (keep local) |
| `CLG_PORT` | `0` (random free port) | server port |
| `CLG_OPEN_BROWSER` | `true` | auto-open the browser on launch |
| `CLG_DATA_DIR` | `~/.clg` | where the SQLite DB lives |

> [!TIP]
> Gemini's free tier is a good no-cost cloud option if you don't want to run a local model.

## Exporting to PDF

PDF export uses [WeasyPrint](https://weasyprint.org), which needs native libraries (cairo, pango). DOCX, HTML, Markdown, and TXT need **no** extra system dependencies.

On **macOS**, install the libraries with Homebrew — the launcher then finds them automatically (it adds Homebrew's lib dir to the dynamic-linker path and re-execs once, so `uv run clg` "just works"):

```bash
brew install pango   # pulls in cairo and the rest
```

> [!NOTE]
> On other platforms, or if PDF export still reports missing libraries, install
> them per the
> [WeasyPrint install guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)
> and restart the app. You can also point the dynamic linker at the libs
> yourself, e.g. `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run clg`.

## Development

```bash
# Backend
uv sync --extra dev
uv run pytest              # tests
uv run ruff check .        # lint
uv run mypy                # types
uv run lint-imports        # architecture boundaries

# Frontend (in web/)
cd web
npm install
npm run dev                # Vite dev server with hot reload (proxies /api to :8000)
npm test                   # Vitest + React Testing Library
npm run typecheck          # tsc
npm run build              # build into ../src/clg/api/static/
```

**Dev workflow with hot reload:** run the backend on a fixed port and the Vite dev server alongside it:

```bash
# terminal 1 — backend API
CLG_PORT=8000 CLG_OPEN_BROWSER=false uv run clg

# terminal 2 — UI with hot reload at http://localhost:5173
cd web && npm run dev
```

### Project layout

```
src/clg/
  bootstrap/     # launcher (uv run clg / uvx clg)
  api/           # FastAPI routers + DTOs (thin adapters)
  core/          # framework-agnostic domain
    ingestion/   # local CV parsing + heuristic sectionizing (pdfplumber / python-docx)
    profile/     # compose structured sections → background text
    generation/  # prompt building + orchestration
    providers/   # ollama / gemini / anthropic / openai + registry
    export/      # pdf / docx / html / markdown / txt renderers
    persistence/ # SQLModel entities + repositories
    config/      # CLG_-prefixed settings
web/             # React + Vite UI (built into src/clg/api/static/)
docs/            # architecture plan, ADRs, diagrams
plan/            # implementation plan
```

## Privacy

By default, everything stays on your machine. Your CV is parsed locally, the database is a local SQLite file, and provider API keys are read only from your git-ignored `.env` — never stored in the database, never exposed by the API. Content is sent to a third party **only** when you explicitly select a cloud provider for generation. There is no telemetry.
