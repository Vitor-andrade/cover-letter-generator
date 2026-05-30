"""DOCX renderer — builds a Word document with python-docx."""

from __future__ import annotations

import io

from clg.core.export.base import ExportError, ExportFormat, LetterDocument


class DocxRenderer:
    fmt = ExportFormat.docx
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    extension = "docx"

    def render(self, doc: LetterDocument) -> bytes:
        try:
            import docx

            document = docx.Document()
            if doc.candidate_name:
                document.add_heading(doc.candidate_name, level=1)
            for para in (p.strip() for p in doc.content.split("\n\n")):
                if para:
                    document.add_paragraph(para)
            buffer = io.BytesIO()
            document.save(buffer)
        except Exception as exc:  # noqa: BLE001 - normalize docx errors
            raise ExportError(f"DOCX rendering failed: {exc}") from exc
        return buffer.getvalue()
