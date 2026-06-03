"""Export: all five renderers produce well-formed, non-empty output."""

from __future__ import annotations

from clg.core.export.base import ExportError, LetterDocument, render

DOC = LetterDocument(
    content=(
        "Vitor Cavalcante\n"
        "vitor@example.com · +55 61 99999-0000 · linkedin.com/in/vitor · Brasília, Brazil\n"
        "RE: Senior Engineer\n"
        "Dear Hiring Manager,\n\n"
        "I am excited to apply.\n\n"
        "Sincerely,\nVitor Cavalcante"
    ),
    title="Cover Letter",
    candidate_name="Vitor Cavalcante",
    language="en",
)


def test_text_formats():
    txt = render(DOC, "txt").decode()
    assert b"Dear Hiring Manager" in render(DOC, "txt")
    # Content is the single source of the header — the name is not duplicated.
    assert txt.count("vitor@example.com") == 1
    assert txt.startswith("Vitor Cavalcante\nvitor@example.com")

    md = render(DOC, "markdown").decode()
    assert not md.startswith("#")  # no synthetic name heading injected
    assert "vitor@example.com" in md

    html = render(DOC, "html").lower()
    assert b"<!doctype html>" in html
    assert b"<h1>" not in html  # name comes from content, not a rendered heading


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
