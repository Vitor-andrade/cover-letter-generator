"""Markdown renderer."""

from __future__ import annotations

from clg.core.export.base import ExportFormat, LetterDocument


class MarkdownRenderer:
    fmt = ExportFormat.markdown
    media_type = "text/markdown"
    extension = "md"

    def render(self, doc: LetterDocument) -> bytes:
        # The letter content already carries its header and signature.
        return (doc.content.strip() + "\n").encode("utf-8")
