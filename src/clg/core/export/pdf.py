"""PDF renderer — renders the HTML document via WeasyPrint.

WeasyPrint needs native libraries (cairo, pango). When those are missing the
import fails; we surface a clear, actionable :class:`ExportError` rather than a
raw ImportError (RISK-001). ``reportlab`` is the documented fallback.
"""

from __future__ import annotations

from clg.core.export.base import ExportError, ExportFormat, LetterDocument
from clg.core.export.html import build_html


class PdfRenderer:
    fmt = ExportFormat.pdf
    media_type = "application/pdf"
    extension = "pdf"

    def render(self, doc: LetterDocument) -> bytes:
        try:
            from weasyprint import HTML
        except OSError as exc:  # missing cairo/pango native libs
            raise ExportError(
                "PDF export needs the WeasyPrint system libraries (cairo, pango). "
                "Install them, or export to DOCX/HTML instead."
            ) from exc
        try:
            pdf = HTML(string=build_html(doc)).write_pdf()
        except Exception as exc:  # noqa: BLE001 - normalize rendering errors
            raise ExportError(f"PDF rendering failed: {exc}") from exc
        if pdf is None:  # pragma: no cover - defensive
            raise ExportError("PDF rendering produced no output")
        return bytes(pdf)
