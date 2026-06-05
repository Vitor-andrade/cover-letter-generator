"""Heuristic, LOCAL splitting of extracted CV text into structured sections.

ADR-004 compliant: pure regex/string work — no network, no LLM. The CV never
leaves the machine to be parsed.

Honest limitation: the heuristic reliably buckets lines under the right section
header and splits a section into entry blocks, but it does NOT decompose an
experience/education block into discrete role/company/period fields — that needs
semantic parsing we deliberately forgo. So for list sections the raw lines are
preserved (in ``highlights``/``details``) and the structured subfields are left
blank for the user to refine. Nothing is invented; nothing is lost.
"""

from __future__ import annotations

import re
from typing import Any

_LOW_CONFIDENCE_CHARS = 40

# Canonical section -> header aliases (full-line, anchored). Order matters:
# more specific headers (key skills) are listed before their generic cousins.
_HEADERS: list[tuple[str, str]] = [
    ("summary", r"summary|profile|about(?: me)?|objective|professional summary|bio"),
    ("key_skills", r"key skills|core (?:skills|competenc\w*)|highlights|top skills"),
    ("skills", r"skills|technical skills|technolog(?:y|ies)|tech stack|competencies"),
    ("experiences", r"experience|work experience|employment(?: history)?|"
                    r"professional experience|work history|career"),
    ("projects", r"projects|personal projects|side projects|selected projects|notable projects"),
    ("education", r"education|academic(?: background)?|qualifications|studies"),
    ("certifications", r"certifications?|licen[cs]es?|courses|awards"),
    ("languages", r"languages?|language skills"),
]
_COMPILED = [(key, re.compile(rf"^(?:{alias})$", re.IGNORECASE)) for key, alias in _HEADERS]

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w%-]+", re.IGNORECASE)
_URL = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\d)(\+?\d[\d\s().\-]{7,}\d)(?!\d)")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def _empty_sections() -> dict[str, Any]:
    return {
        "contact": {"email": "", "phone": "", "linkedin": "", "location": "", "website": ""},
        "summary": "",
        "key_skills": [],
        "skills": [],
        "experiences": [],
        "projects": [],
        "education": [],
        "certifications": [],
        "languages": [],
    }


def _match_header(line: str) -> str | None:
    norm = line.strip().strip("•·-*#").strip().rstrip(":").strip()
    if not norm or len(norm) > 40:
        return None
    for key, rx in _COMPILED:
        if rx.match(norm):
            return key
    return None


def _blocks(lines: list[str]) -> list[list[str]]:
    """Split lines into entry blocks separated by blank lines."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _split_skills(lines: list[str]) -> list[str]:
    parts = re.split(r"[,\n•·|]+|\s[-–]\s", "\n".join(lines))
    return [p.strip(" \t-•·") for p in parts if p.strip(" \t-•·")]


def _is_contact_line(line: str) -> bool:
    return bool(
        _EMAIL.search(line) or _LINKEDIN.search(line) or _URL.search(line) or _PHONE.search(line)
    )


def _extract_contact(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """Pull contact details out of the preamble; return (contact, remainder)."""
    text = "\n".join(lines)
    contact = {"email": "", "phone": "", "linkedin": "", "location": "", "website": ""}
    if m := _EMAIL.search(text):
        contact["email"] = m.group(0)
    if m := _LINKEDIN.search(text):
        contact["linkedin"] = m.group(0)
    for m in _URL.finditer(text):
        if "linkedin.com" not in m.group(0).lower():
            contact["website"] = m.group(0)
            break
    if m := _PHONE.search(text):
        contact["phone"] = m.group(1).strip()
    # Lines that are purely contact info shouldn't bleed into the summary.
    remainder = [line for line in lines if line.strip() and not _is_contact_line(line)]
    return contact, remainder


def _certification_entry(line: str) -> dict[str, str]:
    m = _YEAR.search(line)
    return {"name": line.strip(), "issuer": "", "year": m.group(0) if m else ""}


def sectionize(text: str) -> tuple[dict[str, Any], bool]:
    """Bucket extracted CV text into the structured sections schema.

    Returns ``(sections, low_confidence)``. ``low_confidence`` is True when no
    section headers were found (everything fell into the summary) or the text is
    too short to be a real CV.
    """
    buckets: dict[str, list[str]] = {key: [] for key, _ in _HEADERS}
    preamble: list[str] = []
    current: str | None = None
    for raw in text.split("\n"):
        if key := _match_header(raw):
            current = key
            continue
        (buckets[current] if current else preamble).append(raw)

    contact, preamble_summary = _extract_contact(preamble)

    sections = _empty_sections()
    sections["contact"] = contact
    summary_lines = preamble_summary + [ln for ln in buckets["summary"] if ln.strip()]
    sections["summary"] = "\n".join(summary_lines).strip()
    sections["key_skills"] = _split_skills(buckets["key_skills"])
    sections["skills"] = _split_skills(buckets["skills"])
    sections["experiences"] = [
        {"role": "", "company": "", "period": "", "location": "", "highlights": block}
        for block in _blocks(buckets["experiences"])
    ]
    sections["projects"] = [
        {
            "name": "",
            "description": "",
            "tech": [],
            "highlights": block,
            "link": next((u.group(0) for u in [_URL.search(" ".join(block))] if u), ""),
        }
        for block in _blocks(buckets["projects"])
    ]
    sections["education"] = [
        {"degree": "", "institution": "", "period": "", "details": " ".join(block)}
        for block in _blocks(buckets["education"])
    ]
    sections["certifications"] = [
        _certification_entry(line) for line in buckets["certifications"] if line.strip()
    ]
    sections["languages"] = [_language_entry(line) for line in buckets["languages"] if line.strip()]

    found_headers = any(buckets[key] for key, _ in _HEADERS)
    low_confidence = not found_headers or len(text.strip()) < _LOW_CONFIDENCE_CHARS
    return sections, low_confidence


def _language_entry(line: str) -> dict[str, str]:
    parts = re.split(r"\s*[:\-–(]\s*", line.strip(), maxsplit=1)
    proficiency = parts[1].strip().rstrip(")") if len(parts) > 1 else ""
    return {"language": parts[0].strip(), "proficiency": proficiency}
