"""Export renderer abstraction.

A :class:`LetterDocument` (the rendered text plus light metadata) is turned into
bytes by a format-specific :class:`Renderer`. The registry maps an
:class:`ExportFormat` to its renderer; heavy renderers (PDF/DOCX) are imported
lazily so they don't slow process startup.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class ExportFormat(StrEnum):
    txt = "txt"
    markdown = "markdown"
    html = "html"
    pdf = "pdf"
    docx = "docx"


@dataclass(frozen=True)
class LetterDocument:
    """The content and metadata needed to render a cover letter."""

    content: str
    title: str = "Cover Letter"
    candidate_name: str = ""
    language: str = "en"


@runtime_checkable
class Renderer(Protocol):
    fmt: ExportFormat
    media_type: str
    extension: str

    def render(self, doc: LetterDocument) -> bytes: ...


class ExportError(RuntimeError):
    """Raised when a renderer cannot produce output (e.g. missing system deps)."""


def split_name_header(content: str) -> tuple[str, str]:
    """Split a structured letter into its name header and the remaining body.

    The generation format places the candidate's full name on the first line;
    styled renderers (HTML/PDF/DOCX/Markdown) emphasize it as a heading. Returns
    ``("", "")`` for empty content, or ``(name, body)`` otherwise.
    """
    name, _, body = content.lstrip("\n").partition("\n")
    return name.strip(), body


def available_formats() -> list[str]:
    return [f.value for f in ExportFormat]


def get_renderer(fmt: ExportFormat | str) -> Renderer:
    """Return the renderer for ``fmt`` (lazy-importing the implementation)."""
    fmt = ExportFormat(fmt)
    if fmt is ExportFormat.txt:
        from clg.core.export.txt import TxtRenderer

        return TxtRenderer()
    if fmt is ExportFormat.markdown:
        from clg.core.export.markdown import MarkdownRenderer

        return MarkdownRenderer()
    if fmt is ExportFormat.html:
        from clg.core.export.html import HtmlRenderer

        return HtmlRenderer()
    if fmt is ExportFormat.pdf:
        from clg.core.export.pdf import PdfRenderer

        return PdfRenderer()
    if fmt is ExportFormat.docx:
        from clg.core.export.docx import DocxRenderer

        return DocxRenderer()
    raise ExportError(f"No renderer for format: {fmt}")  # pragma: no cover


def render(doc: LetterDocument, fmt: ExportFormat | str) -> bytes:
    return get_renderer(fmt).render(doc)
