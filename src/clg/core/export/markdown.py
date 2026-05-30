"""Markdown renderer."""

from __future__ import annotations

from clg.core.export.base import ExportFormat, LetterDocument


class MarkdownRenderer:
    fmt = ExportFormat.markdown
    media_type = "text/markdown"
    extension = "md"

    def render(self, doc: LetterDocument) -> bytes:
        parts: list[str] = []
        if doc.candidate_name:
            parts.append(f"# {doc.candidate_name}\n")
        parts.append(doc.content.strip() + "\n")
        return "\n".join(parts).encode("utf-8")
