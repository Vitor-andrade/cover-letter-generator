# ADR-006: Structured, sectioned profile background

- **Status:** Accepted
- **Date:** 2026-06-05
- **Deciders:** Vitor (tech lead)

## Context

A Profile originally held a single freeform `background_text` string. The
generation prompt then had to infer what was a skill vs. an experience vs.
education from an unstructured blob, which hurt letter quality and gave the user
no structured way to edit their background. We want the background split into
rich, structured sections.

## Decision

Add a nullable **`sections` JSON column** to `Profile` holding nine sections
(contact, summary, key_skills, skills, experiences, projects, education,
certifications, languages); list sections carry structured entries (e.g. an
experience is `{role, company, period, location, highlights[]}`). The shape is
validated at the API boundary by `SectionsModel` (`api/schemas.py`); SQLite
stores it as JSON/TEXT.

`background_text` is **kept as a derived field**: whenever sections are written,
the server composes them into a labeled markdown document
(`core/profile/compose.py`) and stores that as `background_text`. Generation,
prompt, and export keep reading `background_text` and need **no changes**.

`sections = NULL` is the **legacy sentinel** for profiles created before this
feature; they keep working unchanged until the user opts in to structuring.

Schema migration is a single guarded `ALTER TABLE profile ADD COLUMN sections`
in `init_db` (`core/persistence/db.py`) — `create_all` never alters existing
tables. No Alembic: one local, single-user SQLite file does not warrant a
migration framework.

CV upload is split into sections **locally** by a heuristic
(`core/ingestion/sectionize.py`): full-line header regex + preamble contact
extraction. **No LLM at ingestion** — this *reinforces* [ADR-004], it does not
conflict with it.

## Rationale

- **Low blast radius:** one JSON column + a derived `background_text` means the
  whole generation/export pipeline is untouched; only the profile read/write
  path and the frontend editor change.
- **Backward compatible:** existing rows get `NULL` and behave exactly as before.
- **Privacy preserved:** sectionizing stays local (ADR-004 upheld).
- **Better letters:** the model receives labeled, organized sections instead of a
  ragged blob, and contact details compose into the exact ` · `-separated form
  the prompt already expects.

## Consequences

- **Positive:** structured editing UI, higher-quality prompts, no pipeline churn.
- **Negative / limitations:**
  - The heuristic sectionizer buckets text and splits entry blocks but **does
    not** decompose an experience/education block into discrete
    role/company/period fields — raw lines are preserved in `highlights`/
    `details` and the user refines. Nothing is invented; nothing is lost.
  - SQLAlchemy's JSON column is **not mutation-tracked** — code must reassign the
    whole `profile.sections` object, never mutate it in place. Guarded by the
    PATCH-recompose round-trip test in `tests/test_api.py`.

## Alternatives considered

- **Per-section relational tables + Alembic:** normalization buys nothing for a
  single-user local store and multiplies blast radius. Rejected.
- **LLM auto-split of the CV into sections:** best UX, but sends CV content to a
  provider — rejected to uphold [ADR-004]; remains a possible future opt-in for
  cloud users.
- **Replace `background_text` entirely with sections:** would force changes
  across generation/prompt/export and break legacy rows. Rejected in favor of the
  derived-field approach.

[ADR-004]: ADR-004-local-cv-parsing.md
