---
goal: Build the Cover Letter Generator MVP — local-first Python app (FastAPI + React/Vite), pluggable LLM providers, local CV parsing, all 5 export formats
version: 1.0
date_created: 2026-05-30
last_updated: 2026-05-30
owner: Vitor
status: 'Completed'
tags: [architecture, feature, mvp]
---

# Introduction

![Status: Completed](https://img.shields.io/badge/status-Completed-brightgreen)

This plan implements the CLG MVP defined in
[`docs/clg-architecture-plan.md`](../docs/clg-architecture-plan.md). CLG is a
local-first, open-source application: a single Python process (FastAPI) serves a
JSON API and an embedded React/Vite UI on `127.0.0.1`, persists to SQLite, and
generates cover letters through a pluggable LLM provider abstraction (Ollama
default; BYO Gemini/Anthropic/OpenAI). v1 includes CV upload with local parsing,
manual background entry, AI-assisted ⇄ manual editing, multi-language output, and
export to PDF, HTML, Markdown, TXT, and DOCX.

## 1. Requirements & Constraints

- **REQ-001**: Run entirely locally; bind server to `127.0.0.1` only.
- **REQ-002**: One-command launch (`uvx clg`) that boots the server and opens the browser.
- **REQ-003**: Pluggable LLM providers (ollama/gemini/anthropic/openai) behind a single interface, selected by config.
- **REQ-004**: Ollama is the default, free, offline provider.
- **REQ-005**: CV ingestion via local parsing (pypdf/python-docx) + manual text entry; extracted text must be user-editable before generation.
- **REQ-006**: Export to all 5 formats: PDF, HTML, Markdown, TXT, DOCX.
- **REQ-007**: English-first UI and prompts; per-letter language override.
- **REQ-008**: Mobile-first responsive UI; AI-assist ⇄ manual editor toggle; real-time preview.
- **REQ-009**: Persist profiles, jobs, letters (with version history) in SQLite.
- **SEC-001**: API keys stored AES-256-GCM encrypted in a `0600` key file outside the repo; never in SQLite; never logged.
- **SEC-002**: Treat CV/job text as untrusted input; mitigate prompt injection (delimited sections, no tool use in v1).
- **SEC-003**: Validate upload type/size; harden DOCX/PDF parsing; no telemetry.
- **CON-001**: 100% OSS dependencies; no paid services in the stack.
- **CON-002**: No data leaves the machine unless the user explicitly selects a cloud provider.
- **GUD-001**: Document progress continuously in README.md (`create-readme` skill).
- **GUD-002**: Commit frequently, Conventional Commits, NO Co-Authored-By trailer.
- **PAT-001**: Modular monolith; dependencies point inward (UI → API → Core → data); core has no web-framework imports.
- **PAT-002**: Repository pattern for persistence (DB-swappable); registry/strategy for providers.

## 2. Implementation Steps

### Implementation Phase 1 — Project skeleton & tooling

- GOAL-001: Establish the modular Python project, tooling, and a runnable empty FastAPI app that serves a placeholder UI on localhost.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Init `uv` project: `pyproject.toml` (name `clg`, console_script `clg`), Python ≥3.11, ruff + mypy + pytest config | ✅ | 2026-05-30 |
| TASK-002 | Create package layout: `src/clg/{api,core,bootstrap}/` with `core/{ingestion,generation,providers,export,secrets,persistence,config}/` | ✅ | 2026-05-30 |
| TASK-003 | Add `bootstrap/launcher.py`: start uvicorn on `127.0.0.1`, pick free port, open browser; wire `clg` entrypoint | ✅ | 2026-05-30 |
| TASK-004 | Add `config/settings.py` using `pydantic-settings` with `CLG_` env prefix; resolve `~/.clg/` data dir (create with safe perms) | ✅ | 2026-05-30 |
| TASK-005 | Scaffold React+Vite+TS UI under `web/`; configure build output to `src/clg/api/static/`; FastAPI `StaticFiles` mount + SPA fallback | ✅ | 2026-05-30 |
| TASK-006 | Add import-linter (or ruff rules) enforcing PAT-001 dependency direction; add to CI | ✅ | 2026-05-30 |

### Implementation Phase 2 — Persistence & domain models

- GOAL-002: Implement the data model, SQLite storage, and repository interfaces.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Define SQLModel entities: `Profile`, `Job`, `CoverLetter`, `LetterVersion`, `Settings` (per ER in arch plan) | ✅ | 2026-05-30 |
| TASK-008 | Implement `persistence/db.py` (engine, session, migrations/`create_all`) targeting `~/.clg/clg.db` | ✅ | 2026-05-30 |
| TASK-009 | Implement repository classes (`ProfileRepo`, `JobRepo`, `LetterRepo`, `SettingsRepo`) behind protocols for DB-swappability (PAT-002) | ✅ | 2026-05-30 |
| TASK-010 | Define Pydantic DTOs for the API boundary; never expose ORM rows to the UI | ✅ | 2026-05-30 |

### Implementation Phase 3 — Secrets & provider abstraction

- GOAL-003: Implement encrypted key storage and the pluggable LLM provider layer.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-011 | Implement `secrets/store.py`: AES-256-GCM via `cryptography`; auto-generate key at `~/.clg/master.key` (0600); `~/.clg/keys.bin` (0600); get/set/delete provider keys | ✅ | 2026-05-30 |
| TASK-012 | Define `providers/base.py`: `LLMProvider` Protocol (`complete`, `health`) + `ProviderHealth`; provider registry keyed by name | ✅ | 2026-05-30 |
| TASK-013 | Implement `providers/ollama.py` (default, no key, localhost:11434) | ✅ | 2026-05-30 |
| TASK-014 | Implement `providers/{gemini,anthropic,openai}.py` using official SDKs; pull key from secrets store; map model from settings | ✅ | 2026-05-30 |
| TASK-015 | Implement `providers/fake.py` deterministic provider for tests | ✅ | 2026-05-30 |
| TASK-016 | Implement provider selection from settings/env (`CLG_AI_PROVIDER`, `CLG_<P>_API_KEY`, `CLG_<P>_MODEL`) | ✅ | 2026-05-30 |

### Implementation Phase 4 — Ingestion & generation

- GOAL-004: Implement CV parsing, manual input, and prompt-based letter generation.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-017 | Implement `ingestion/parse.py`: `extract_pdf` (pypdf), `extract_docx` (python-docx), `normalize_manual`; size/type guards (SEC-003); low-confidence/empty signal | ✅ | 2026-05-30 |
| TASK-018 | Implement `generation/prompt.py`: English-first templates with language override; delimit untrusted CV/job sections; injection-hardening instructions (SEC-002) | ✅ | 2026-05-30 |
| TASK-019 | Implement `generation/service.py`: orchestrate profile+job → prompt → provider.complete → persist `CoverLetter` + `LetterVersion(origin=ai)` | ✅ | 2026-05-30 |
| TASK-020 | Implement section/paragraph regeneration entry point (regenerate a part, append new `LetterVersion`) | ✅ | 2026-05-30 |

### Implementation Phase 5 — Export

- GOAL-005: Render a letter to all five export formats.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-021 | Implement `export/base.py` renderer interface + format registry | ✅ | 2026-05-30 |
| TASK-022 | Implement TXT + Markdown renderers (string templates) | ✅ | 2026-05-30 |
| TASK-023 | Implement HTML renderer (Jinja2 template, print-friendly CSS) | ✅ | 2026-05-30 |
| TASK-024 | Implement PDF renderer (weasyprint from the HTML template; document cairo/pango deps; reportlab fallback noted) | ✅ | 2026-05-30 |
| TASK-025 | Implement DOCX renderer (python-docx) | ✅ | 2026-05-30 |

### Implementation Phase 6 — API layer

- GOAL-006: Expose the domain through FastAPI routers (thin adapters).

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-026 | `profiles` router: create (manual or upload), get, list, update extracted text | ✅ | 2026-05-30 |
| TASK-027 | `jobs` router: create, get, list | ✅ | 2026-05-30 |
| TASK-028 | `generation` router: POST generate (profile_id, job_id, language, provider), POST regenerate-section | ✅ | 2026-05-30 |
| TASK-029 | `export` router: GET/POST export(letter_id, format) → file download with correct content-type | ✅ | 2026-05-30 |
| TASK-030 | `settings` router: get/set active provider+model+language; set/delete provider API key (writes to secrets store) | ✅ | 2026-05-30 |
| TASK-031 | App wiring: localhost bind, CORS locked to local origin, request size limits, error handling, health endpoint | ✅ | 2026-05-30 |

### Implementation Phase 7 — Web UI

- GOAL-007: Build the mobile-first React UI with AI-assist ⇄ manual editing and live preview.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-032 | API client + types (generated or hand-written from DTOs); app shell, routing, responsive layout | ✅ | 2026-05-30 |
| TASK-033 | Intake screens: job form + profile (manual entry and CV upload with editable extracted text) | ✅ | 2026-05-30 |
| TASK-034 | Editor: AI-assist ⇄ manual toggle, real-time preview, regenerate-section, language selector | ✅ | 2026-05-30 |
| TASK-035 | Settings screen: provider/model selection, API key entry, Ollama health indicator | ✅ | 2026-05-30 |
| TASK-036 | Export UI: pick format, trigger download; surface errors (e.g. missing PDF system deps) | ✅ | 2026-05-30 |

### Implementation Phase 8 — Tests, docs, packaging

- GOAL-008: Verify behavior, document, and make distributable.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-037 | Backend tests (pytest+httpx): ingestion, generation (fake provider), export (all 5), secrets round-trip, API happy/edge paths | ✅ | 2026-05-30 |
| TASK-038 | UI tests (Vitest+RTL) for intake, editor toggle, export flow | ✅ | 2026-05-30 |
| TASK-039 | Write public README via `create-readme` skill (install, `uvx clg`, providers, privacy) | ✅ | 2026-05-30 |
| TASK-040 | Validate `uvx clg` end-to-end on a clean environment; document Ollama + optional cloud setup | ✅ | 2026-05-30 |
| TASK-041 | Commit curated `agents/` and `skills/` folders; ensure `~/.clg/` and secrets are git-ignored | ✅ | 2026-05-30 |

## 3. Alternatives

- **ALT-001**: Go + single-binary (LPE stack) — rejected; weaker parsing/LLM ecosystem (ADR-001).
- **ALT-002**: LLM-based CV extraction — rejected; privacy/cost/determinism (ADR-004).
- **ALT-003**: LangChain/LiteLLM provider wrapper — deferred; unnecessary weight for 4 SDKs (ADR-003).
- **ALT-004**: reportlab for PDF instead of weasyprint — kept as fallback if system-dep friction is high.
- **ALT-005**: OS keychain for secrets — deferred to Phase B; AES-256-GCM file for v1 (ADR-005).

## 4. Dependencies

- **DEP-001**: Python ≥3.11, `uv`.
- **DEP-002**: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`.
- **DEP-003**: `sqlmodel` (SQLAlchemy + SQLite).
- **DEP-004**: `ollama`, `google-genai`, `anthropic`, `openai`.
- **DEP-005**: `pypdf`, `python-docx`.
- **DEP-006**: `weasyprint` (PDF; needs cairo/pango system libs), `jinja2`, `markdown`.
- **DEP-007**: `cryptography` (AES-256-GCM).
- **DEP-008**: Node + React 19 + Vite + TypeScript (UI build).
- **DEP-009**: Optional external: Ollama daemon (local) for the free default path.

## 5. Files

- **FILE-001**: `pyproject.toml` — package metadata, deps, `clg` entrypoint, tool config.
- **FILE-002**: `src/clg/bootstrap/launcher.py` — server boot + browser open.
- **FILE-003**: `src/clg/core/config/settings.py` — `CLG_`-prefixed settings, data dir.
- **FILE-004**: `src/clg/core/persistence/{models.py,db.py,repositories.py}` — data layer.
- **FILE-005**: `src/clg/core/secrets/store.py` — encrypted key storage.
- **FILE-006**: `src/clg/core/providers/{base,ollama,gemini,anthropic,openai,fake}.py` — provider layer.
- **FILE-007**: `src/clg/core/ingestion/parse.py` — CV parsing + manual normalization.
- **FILE-008**: `src/clg/core/generation/{prompt.py,service.py}` — generation logic.
- **FILE-009**: `src/clg/core/export/{base.py,txt.py,markdown.py,html.py,pdf.py,docx.py}` — exporters.
- **FILE-010**: `src/clg/api/routers/{profiles,jobs,generation,export,settings}.py` + `app.py`.
- **FILE-011**: `web/` — React/Vite UI; build output to `src/clg/api/static/`.
- **FILE-012**: `tests/` — backend + UI tests.
- **FILE-013**: `README.md` — public documentation.
- **FILE-014**: `.gitignore` — exclude `~/.clg/` artifacts, build output, secrets.

## 6. Testing

- **TEST-001**: Ingestion — PDF and DOCX extraction on sample files; empty/garbled → low-confidence signal; manual normalization.
- **TEST-002**: Secrets — encrypt→store→decrypt round-trip; file perms `0600`; wrong key fails authentication (GCM tag).
- **TEST-003**: Providers — fake provider deterministic output; registry selection by config; cloud providers mocked (no network).
- **TEST-004**: Generation — prompt builds with delimited untrusted sections; language override honored; version persisted.
- **TEST-005**: Export — all 5 renderers produce valid, non-empty output with correct content-type.
- **TEST-006**: API — happy paths + edge cases (missing profile/job, oversized upload, missing key for cloud provider) via httpx.
- **TEST-007**: Security — server binds `127.0.0.1` only; CORS rejects non-local origin; injection markers in CV do not alter system instructions (behavioral check vs fake provider).
- **TEST-008**: UI — intake submit, AI/manual toggle, export-download flow (Vitest+RTL).

## 7. Risks & Assumptions

- **RISK-001**: weasyprint system deps (cairo/pango) cause install friction → document; reportlab fallback (ALT-004).
- **RISK-002**: Scanned/image PDFs extract poorly → editable extracted text + warning; OCR deferred to Phase B.
- **RISK-003**: Provider SDK drift breaks generation → thin adapters, pinned versions, fake-provider tests.
- **RISK-004**: "All features in v1" risks slow MVP → strict phase ordering; stable interfaces let parts land independently.
- **RISK-005**: Prompt injection via CV/job text → SEC-002 mitigations; no tool use in v1.
- **ASSUMPTION-001**: Single user per install; no concurrency/auth needed at v1.
- **ASSUMPTION-002**: User can install Ollama for the free path, or has a cloud key.
- **ASSUMPTION-003**: Developer audience tolerates a Python runtime / `uvx` launch.

## 8. Related Specifications / Further Reading

- [Architecture Plan](../docs/clg-architecture-plan.md)
- [Interactive diagrams](../docs/clg-architecture-diagrams.html) · [Draw.io](../docs/clg-architecture.drawio)
- ADRs: [001](../docs/architecture/ADR-001-python-local-first.md) · [002](../docs/architecture/ADR-002-modular-monolith.md) · [003](../docs/architecture/ADR-003-provider-abstraction.md) · [004](../docs/architecture/ADR-004-local-cv-parsing.md) · [005](../docs/architecture/ADR-005-secret-storage.md)
- Reference project: `linkedin-post-executor` (provider + encrypted-key pattern)
