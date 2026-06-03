"""HTML renderer — print-friendly, self-contained document (Jinja2)."""

from __future__ import annotations

from jinja2 import Template

from clg.core.export.base import ExportFormat, LetterDocument

_TEMPLATE = Template(
    """<!doctype html>
<html lang="{{ language }}">
<head>
<meta charset="utf-8" />
<title>{{ title }}</title>
<style>
  @page { size: A4; margin: 2.5cm; }
  body { font-family: Georgia, 'Times New Roman', serif; font-size: 12pt;
         line-height: 1.5; color: #1a1a1a; max-width: 70ch; margin: 2rem auto; }
  h1 { font-size: 16pt; margin-bottom: 1.2rem; }
  p { margin: 0 0 1rem; white-space: pre-wrap; }
</style>
</head>
<body>
{% for para in paragraphs %}<p>{{ para }}</p>
{% endfor %}</body>
</html>
""".strip()
)


def build_html(doc: LetterDocument) -> str:
    paragraphs = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
    return _TEMPLATE.render(
        language=doc.language,
        title=doc.title,
        paragraphs=paragraphs,
    )


class HtmlRenderer:
    fmt = ExportFormat.html
    media_type = "text/html"
    extension = "html"

    def render(self, doc: LetterDocument) -> bytes:
        return build_html(doc).encode("utf-8")
