"""Local CV/background ingestion (ADR-004).

Extracts plain text from uploaded PDF/DOCX files locally — no LLM, no network —
or normalizes manually-entered text. The extracted text is meant to be shown
back to the user for editing before it is ever sent to a provider.

Security (SEC-003): callers must enforce an upload size cap before handing bytes
here; ``MAX_INPUT_BYTES`` is the hard ceiling this module will process.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from clg.core.persistence.models import ProfileSource

MAX_INPUT_BYTES = 10 * 1024 * 1024  # 10 MiB hard cap on uploaded files
_LOW_CONFIDENCE_CHARS = 40  # below this, extraction is probably empty/scanned


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


def _assess(text: str, source: ProfileSource) -> ExtractedText:
    cleaned = text.strip()
    low = len(cleaned) < _LOW_CONFIDENCE_CHARS
    detail = (
        "Little or no text extracted — the file may be scanned/image-based; "
        "edit the text manually." if low else ""
    )
    return ExtractedText(text=cleaned, source=source, low_confidence=low, detail=detail)


def extract_pdf(data: bytes) -> ExtractedText:
    _check_size(data)
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # noqa: BLE001 - normalize parser errors
        raise IngestionError(f"Could not parse PDF: {exc}") from exc
    return _assess("\n".join(pages), ProfileSource.upload)


def extract_docx(data: bytes) -> ExtractedText:
    _check_size(data)
    try:
        import docx

        document = docx.Document(io.BytesIO(data))
        paragraphs = [p.text for p in document.paragraphs]
    except Exception as exc:  # noqa: BLE001 - normalize parser errors
        raise IngestionError(f"Could not parse DOCX: {exc}") from exc
    return _assess("\n".join(paragraphs), ProfileSource.upload)


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
