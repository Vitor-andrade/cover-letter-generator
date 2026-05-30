"""Export: all five renderers produce well-formed, non-empty output."""

from __future__ import annotations

from clg.core.export.base import ExportError, LetterDocument, render

DOC = LetterDocument(
    content="Dear Hiring Manager,\n\nI am excited to apply.\n\nSincerely,\nVitor",
    title="Cover Letter",
    candidate_name="Vitor Cavalcante",
    language="en",
)


def test_text_formats():
    assert b"Dear Hiring Manager" in render(DOC, "txt")
    assert render(DOC, "markdown").startswith(b"# Vitor")
    assert b"<!doctype html>" in render(DOC, "html").lower()


def test_docx_is_a_zip():
    assert render(DOC, "docx")[:2] == b"PK"


def test_pdf_or_clear_error():
    """PDF renders when WeasyPrint libs exist; otherwise raises a clear error."""
    try:
        out = render(DOC, "pdf")
    except ExportError as exc:
        assert "WeasyPrint" in str(exc) or "PDF" in str(exc)
    else:
        assert out[:4] == b"%PDF"
