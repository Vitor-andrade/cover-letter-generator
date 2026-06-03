"""Plain-text renderer."""

from __future__ import annotations

from clg.core.export.base import ExportFormat, LetterDocument


class TxtRenderer:
    fmt = ExportFormat.txt
    media_type = "text/plain"
    extension = "txt"

    def render(self, doc: LetterDocument) -> bytes:
        # The generated letter already contains its own header (name + contact)
        # and signature, so the content is rendered verbatim.
        return (doc.content.strip() + "\n").encode("utf-8")
