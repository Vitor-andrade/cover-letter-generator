# ADR-004: Local CV parsing, not LLM-based extraction

- **Status:** Accepted
- **Date:** 2026-05-30
- **Deciders:** Vitor (tech lead)

## Context

Users provide their background either by uploading a CV (PDF/DOCX) or typing it
manually. The background text feeds the generation prompt. There are two ways to
turn an uploaded file into usable text: parse locally, or send the raw file to
an LLM to extract/structure fields.

## Decision

**Parse CVs locally** with `pdfplumber` (PDF, layout-aware, MIT-licensed) and
`python-docx` (DOCX — body paragraphs **plus tables, headers and footers**),
plus a manual text-entry path. Extracted text is whitespace-normalized for
readability. The extracted/typed text is passed to the LLM **only at generation
time**, inside a sanitized prompt. No separate LLM extraction step.

> **Update (2026-06-03):** PDF parsing moved from `pypdf` to `pdfplumber`
> (layout-aware, far more faithful on columns/tables; MIT — `pymupdf` was
> rejected for its AGPL license). DOCX extraction was extended beyond paragraphs
> to include tables/headers/footers, which CV templates commonly use and which
> the original paragraphs-only pass silently dropped. Optional LLM-assisted
> reading for cloud users remains a future, opt-in possibility (see "Alternatives").

## Rationale

- **Privacy:** CV content never leaves the machine for parsing — aligns with the
  local-first, privacy-by-default principle.
- **Cost:** Zero token spend for ingestion.
- **Determinism:** Parsing is reproducible and debuggable; no hallucinated
  fields.

## Consequences

- **Positive:** Free, private, deterministic ingestion.
- **Negative:** Poorly structured / scanned-image PDFs extract badly. Mitigated
  by: (a) always allowing manual edit of extracted text before generation,
  (b) clear UI feedback when extraction is low-confidence/empty. OCR is out of
  scope for v1 (possible Phase B addition).

## Alternatives considered

- **LLM-based extraction of raw CV:** more robust to messy layouts, but leaks
  content to the provider, costs tokens, and is non-deterministic. Rejected.
- **Third-party résumé-parsing API:** violates the free + privacy principles.
  Rejected.
