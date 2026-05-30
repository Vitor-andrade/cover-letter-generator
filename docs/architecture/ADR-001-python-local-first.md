# ADR-001: Python, local-first application (not hosted, not Go)

- **Status:** Accepted
- **Date:** 2026-05-30
- **Deciders:** Vitor (tech lead)

## Context

CLG helps developers generate cover letters for international tech roles. The
product core is **CV parsing (PDF/DOCX) + LLM orchestration** with a
**bring-your-own-key / local-AI** model. The sister project
`linkedin-post-executor` (Go + `go:embed` single binary) is the reference for
the AI-provider pattern, raising the question of language and distribution.

## Decision

Build CLG as a **local-first Python application**: a package that boots a local
web server (FastAPI + embedded React build) on `127.0.0.1` and opens the
browser. **Not** a hosted SaaS. Distribution via `uv`/`uvx`.

## Rationale

- The dominant complexity is document parsing + multi-provider LLM calls, where
  Python's ecosystem (official SDKs for all four providers, `pypdf`,
  `python-docx`) is materially stronger than Go's.
- Local-first satisfies the non-negotiables: 100% free, full privacy (data and
  keys never leave the machine by default), works offline with Ollama.
- The user is indifferent to single-binary distribution and explicitly prefers
  Python when there is no hard tradeoff.

## Consequences

- **Positive:** Best-in-class parsing/LLM libraries; fast iteration; trivial
  privacy story; zero hosting cost.
- **Negative:** No `go:embed`-style single binary. Mitigated by `uvx clg`
  (one command, no manual venv) and a documented install path.
- Python runtime must be present (or shipped); acceptable for a developer
  audience.

## Alternatives considered

- **Go + single binary (like LPE):** best distribution, weaker parsing/LLM
  ecosystem. Rejected — distribution was not a priority; core fit wins.
- **Hosted web app:** breaks the free + privacy + BYO-key principles and adds
  infra cost. Rejected.
