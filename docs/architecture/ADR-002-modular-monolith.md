# ADR-002: Modular monolith architecture

- **Status:** Accepted
- **Date:** 2026-05-30
- **Deciders:** Vitor (tech lead)

## Context

CLG runs as a single process on one user's machine. There is no independent
scaling pressure, no team-per-service split, no network boundary worth
introducing. Yet the user requires a **modular** codebase that is easy to
maintain, document, and (optionally) extend toward a hosted multi-user mode
later.

## Decision

Adopt a **modular monolith**: one FastAPI process, with the domain split into
framework-agnostic core modules (`ingestion`, `generation`, `providers`,
`export`, `secrets`, `persistence`, `config`). API routers are thin adapters
over the core; the core has **no FastAPI imports**.

## Rationale

- Single deployable unit matches a single-user local app — zero operational
  overhead.
- Clear module boundaries give the maintainability the user demands and keep
  the door open to a future service split (Phase C) without a rewrite.
- Framework-agnostic core means the same logic could later be driven by a CLI,
  a different web framework, or a hosted API.

## Consequences

- **Positive:** Simple to run, test, and reason about; enforced boundaries
  prevent the UI/web layer from leaking into domain logic.
- **Negative:** Requires discipline (dependency direction must point inward).
  Enforced via import-linting and code review.

## Alternatives considered

- **Unstructured monolith:** faster to start, but fails the maintainability and
  future-extensibility requirements. Rejected.
- **Microservices / serverless:** absurd operational overhead for a local
  single-user tool. Rejected.
