"""Local CV/background ingestion (ADR-004).

Extracts plain text from uploaded PDF/DOCX files locally — no LLM, no network —
or normalizes manually-entered text. The extracted text is meant to be shown
back to the user for editing before it is ever sent to a provider.

PDF text is extracted with ``pdfplumber`` (MIT), which is layout-aware and far
more faithful than a naive stream dump. DOCX extraction walks the document body
in order and includes **tables, headers and footers** — CV templates routinely
put contact details and skills grids in tables, which a paragraphs-only pass
would silently drop. Extracted text is whitespace-normalized so it reads cleanly
in the editor instead of arriving as a ragged wall of spacing.

Security (SEC-003): callers must enforce an upload size cap before handing bytes
here; ``MAX_INPUT_BYTES`` is the hard ceiling this module will process.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from clg.core.persistence.models import ProfileSource

if TYPE_CHECKING:
    from docx.document import Document as DocxDocument

MAX_INPUT_BYTES = 10 * 1024 * 1024  # 10 MiB hard cap on uploaded files
_LOW_CONFIDENCE_CHARS = 40  # below this, extraction is probably empty/scanned

_INLINE_WS = re.compile(r"[ \t\f\v]+")
_BLANK_RUNS = re.compile(r"\n{3,}")


class IngestionError(ValueError):
    """Raised for unsupported types or oversized/corrupt inputs."""


@dataclass(frozen=True)
class ExtractedText:
    """Result of an ingestion call."""

    text: str
    source: ProfileSource
    low_confidence: bool
    detail: str = ""


def _check_size(data: bytes) -> None:
    if len(data) > MAX_INPUT_BYTES:
        raise IngestionError(
            f"File exceeds the {MAX_INPUT_BYTES // (1024 * 1024)} MiB limit"
        )


def _clean(text: str) -> str:
    """Collapse runs of inline whitespace and excess blank lines.

    Layout extraction tends to emit ragged spacing (column gaps, padded cells);
    this keeps line structure but makes the result readable for editing.
    """
    lines = [_INLINE_WS.sub(" ", line).strip() for line in text.splitlines()]
    return _BLANK_RUNS.sub("\n\n", "\n".join(lines)).strip()


def _assess(text: str, source: ProfileSource) -> ExtractedText:
    cleaned = _clean(text)
    low = len(cleaned) < _LOW_CONFIDENCE_CHARS
    detail = (
        "Little or no text extracted — the file may be scanned/image-based; "
        "edit the text manually." if low else ""
    )
    return ExtractedText(text=cleaned, source=source, low_confidence=low, detail=detail)


def extract_pdf(data: bytes) -> ExtractedText:
    _check_size(data)
    try:
        import pdfplumber

        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
    except Exception as exc:  # noqa: BLE001 - normalize parser errors
        raise IngestionError(f"Could not parse PDF: {exc}") from exc
    return _assess("\n\n".join(pages), ProfileSource.upload)


def _dedupe_row(cells: list[str]) -> str:
    """Join a table row's cells, dropping the repeats merged cells produce."""
    out: list[str] = []
    for cell in cells:
        text = cell.strip()
        if text and (not out or out[-1] != text):
            out.append(text)
    return " | ".join(out)


def _docx_body_lines(document: DocxDocument) -> list[str]:
    """Text from body paragraphs and tables, in document order."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    lines: list[str] = []
    for child in document.element.body.iterchildren():
        tag = str(child.tag)
        if tag.endswith("}p"):
            lines.append(Paragraph(child, document).text)
        elif tag.endswith("}tbl"):
            for row in Table(child, document).rows:
                lines.append(_dedupe_row([cell.text for cell in row.cells]))
    return lines


def _docx_hf_lines(document: DocxDocument, which: str) -> list[str]:
    """Unique header or footer lines (CVs often place contact info here)."""
    seen: set[str] = set()
    out: list[str] = []
    for section in document.sections:
        part = section.header if which == "header" else section.footer
        for paragraph in part.paragraphs:
            text = paragraph.text.strip()
            if text and text not in seen:
                seen.add(text)
                out.append(text)
    return out


def extract_docx(data: bytes) -> ExtractedText:
    _check_size(data)
    try:
        import docx

        document = docx.Document(io.BytesIO(data))
        lines = [
            *_docx_hf_lines(document, "header"),
            *_docx_body_lines(document),
            *_docx_hf_lines(document, "footer"),
        ]
    except Exception as exc:  # noqa: BLE001 - normalize parser errors
        raise IngestionError(f"Could not parse DOCX: {exc}") from exc
    return _assess("\n".join(lines), ProfileSource.upload)


def extract_upload(filename: str, data: bytes) -> ExtractedText:
    """Dispatch on file extension. Supported: .pdf, .docx."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_pdf(data)
    if lower.endswith(".docx"):
        return extract_docx(data)
    raise IngestionError("Unsupported file type — upload a .pdf or .docx, or paste text manually")


def normalize_manual(text: str) -> ExtractedText:
    """Normalize manually-entered background text."""
    return _assess(text, ProfileSource.manual)
