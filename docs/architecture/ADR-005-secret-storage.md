# ADR-005: Encrypted local secret storage

- **Status:** Accepted
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
