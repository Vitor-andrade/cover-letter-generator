"""Markdown renderer."""

from __future__ import annotations

from clg.core.export.base import ExportFormat, LetterDocument, split_name_header


class MarkdownRenderer:
    fmt = ExportFormat.markdown
    media_type = "text/markdown"
    extension = "md"

    def render(self, doc: LetterDocument) -> bytes:
        # The letter content already carries its header and signature. Promote
        # the first line (the candidate's name) to an H1 so it renders large and
        # bold; the rest of the letter follows verbatim.
        name, body = split_name_header(doc.content)
        out = (f"# {name}\n\n" if name else "") + body.strip() + "\n"
        return out.encode("utf-8")
