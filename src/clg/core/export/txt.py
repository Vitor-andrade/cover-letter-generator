"""Plain-text renderer."""

from __future__ import annotations

from clg.core.export.base import ExportFormat, LetterDocument


class TxtRenderer:
    fmt = ExportFormat.txt
    media_type = "text/plain"
    extension = "txt"

    def render(self, doc: LetterDocument) -> bytes:
        header = f"{doc.candidate_name}\n\n" if doc.candidate_name else ""
        return (header + doc.content.strip() + "\n").encode("utf-8")
