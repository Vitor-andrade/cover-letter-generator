# ADR-005: Encrypted local secret storage

- **Status:** Superseded (2026-06-02) — keys are now configured via env/`.env`
  (`CLG_<PROVIDER>_API_KEY`). The encrypted secret store, its UI paste flow, and
  the `/api/settings/keys` endpoints were removed. See the **Supersession** note
  at the bottom.
- **Date:** 2026-05-30
- **Deciders:** Vitor (tech lead)

## Context

BYO cloud providers require API keys. These must be stored on the user's machine
without plaintext exposure, mirroring the `linkedin-post-executor` approach.

## Decision

Store provider API keys in an **encrypted key file** (e.g. `~/.clg/key.bin`),
**not** in SQLite. Encrypt with **AES-256-GCM** via the `cryptography` library.
The encryption key is auto-generated on first run, kept in a separate file
outside the repo, and all secret files are created with `0600` permissions.
Keys are decrypted in-memory only when a cloud provider call is made.

## Rationale

- Keeps secrets out of the application database and out of any export/backup of
  letters.
- AES-256-GCM gives authenticated encryption (tamper detection).
- `0600` + outside-repo placement prevents accidental commit/leak.

## Consequences

- **Positive:** No plaintext keys at rest; clear separation from app data.
- **Negative:** The local encryption key itself sits on disk (necessary for an
  unattended local tool). Documented as a known limitation; OS keychain
  integration is a possible Phase B hardening.

## Alternatives considered

- **OS keychain (Keychain/DPAPI/Secret Service):** stronger, but cross-platform
  complexity for v1. Deferred to Phase B.
- **Plaintext env/config file:** unacceptable leak risk. Rejected.
- **Keys in SQLite:** mixes secrets with exportable app data. Rejected.

## Supersession (2026-06-02)

The in-app "paste your API key" flow was removed. Letting users paste secrets
into a browser form (then encrypting them at rest) added a moving-parts secret
store — master key on disk, encrypted blob, AES-GCM (de)serialization, a UI form,
and two API endpoints — for a single-user local tool whose process already reads
its config from the environment.

Keys are now provided **only** via env vars / `.env`
(`CLG_GEMINI_API_KEY`, `CLG_ANTHROPIC_API_KEY`, `CLG_OPENAI_API_KEY`). This is the
standard 12-factor approach, keeps secrets out of the app DB and any letter
export (the original goal), and removes the attack surface of accepting secrets
over HTTP. The `.env` file is git-ignored and never returned by the API — the
settings endpoint still only exposes *which* providers have a key configured,
never the values.

**Trade-off accepted:** secrets now live in plaintext in `.env` rather than an
encrypted blob. For a local-first, single-user tool this matches how the user
already stores other dev credentials, and the `.env` sits outside the repo's
tracked files. OS-keychain integration remains a possible future hardening if
the tool ever becomes multi-user or hosted.
