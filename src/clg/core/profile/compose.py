"""Compose structured profile sections into a labeled background document.

The structured ``sections`` are the editable source of truth; this pure function
renders them into the ``background_text`` that the generation prompt and exports
already consume — so the rest of the pipeline needs no changes. Output is
deterministic (stable section order, empty parts omitted) so letter generation
stays reproducible. Empty sections and empty subfields produce no output, matching
the prompt's "omit any detail that is absent; never invent one" rule.
"""

from __future__ import annotations

from typing import Any


def _s(value: Any) -> str:
    """Coerce to a trimmed string ('' for None)."""
    return str(value).strip() if value is not None else ""


def _join(parts: list[Any], sep: str) -> str:
    """Join the non-empty, trimmed parts with ``sep``."""
    return sep.join(p for p in (_s(x) for x in parts) if p)


def _csv(items: Any) -> str:
    return _join(list(items or []), ", ")


def _experience_block(entry: dict[str, Any]) -> list[str]:
    title = _join([entry.get("role"), entry.get("company")], " at ")
    head = "- " + (title or "Role")
    if _s(entry.get("period")):
        head += f" ({_s(entry.get('period'))})"
    if _s(entry.get("location")):
        head += f" — {_s(entry.get('location'))}"
    lines = [head]
    lines += [f"  - {_s(h)}" for h in (entry.get("highlights") or []) if _s(h)]
    return lines


def _project_block(entry: dict[str, Any]) -> list[str]:
    head = "- " + (_s(entry.get("name")) or "Project")
    if _s(entry.get("description")):
        head += f" — {_s(entry.get('description'))}"
    if _s(entry.get("link")):
        head += f" [{_s(entry.get('link'))}]"
    lines = [head]
    if _csv(entry.get("tech")):
        lines.append(f"  Tech: {_csv(entry.get('tech'))}")
    lines += [f"  - {_s(h)}" for h in (entry.get("highlights") or []) if _s(h)]
    return lines


def _education_block(entry: dict[str, Any]) -> list[str]:
    title = _join([entry.get("degree"), entry.get("institution")], ", ")
    head = "- " + (title or "Education")
    if _s(entry.get("period")):
        head += f" ({_s(entry.get('period'))})"
    lines = [head]
    if _s(entry.get("details")):
        lines.append(f"  {_s(entry.get('details'))}")
    return lines


def _certification_line(entry: dict[str, Any]) -> str:
    head = _s(entry.get("name"))
    if _s(entry.get("issuer")):
        head = _join([head, _s(entry.get("issuer"))], " — ")
    if _s(entry.get("year")):
        head += f" ({_s(entry.get('year'))})"
    return f"- {head}" if head else ""


def _language_line(entry: dict[str, Any]) -> str:
    pair = _join([entry.get("language"), entry.get("proficiency")], ": ")
    return f"- {pair}" if pair else ""


def compose_background_text(sections: dict[str, Any] | None) -> str:
    """Render structured sections into the labeled background document."""
    if not sections:
        return ""

    blocks: list[str] = []

    def add(title: str, body_lines: list[str]) -> None:
        body = [ln for ln in body_lines if ln]
        if body:
            blocks.append(f"## {title}\n" + "\n".join(body))

    contact = sections.get("contact") or {}
    contact_fields = (
        ("Email", "email"),
        ("Phone", "phone"),
        ("LinkedIn", "linkedin"),
        ("Location", "location"),
        ("Website", "website"),
    )
    contact_parts = [
        f"{label}: {_s(contact.get(key))}"
        for label, key in contact_fields
        if _s(contact.get(key))
    ]
    add("Contact", [_join(contact_parts, " · ")])
    add("Summary", [_s(sections.get("summary"))])
    add("Key Skills", [_csv(sections.get("key_skills"))])
    add("Skills", [_csv(sections.get("skills"))])

    exp: list[str] = []
    for e in sections.get("experiences") or []:
        exp += _experience_block(e)
    add("Experience", exp)

    proj: list[str] = []
    for e in sections.get("projects") or []:
        proj += _project_block(e)
    add("Projects", proj)

    edu: list[str] = []
    for e in sections.get("education") or []:
        edu += _education_block(e)
    add("Education", edu)

    add(
        "Certifications",
        [_certification_line(e) for e in (sections.get("certifications") or [])],
    )
    add("Languages", [_language_line(e) for e in (sections.get("languages") or [])])

    return "\n\n".join(blocks)
