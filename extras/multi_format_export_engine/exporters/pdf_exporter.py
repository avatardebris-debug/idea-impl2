"""PDF exporter — converts a Manuscript to PDF via HTML + weasyprint."""

import os
import subprocess
import tempfile
from typing import Any, Dict, Optional

from ..models import Chapter, Heading, Manuscript, Paragraph


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _manuscript_to_html(
    manuscript: Manuscript,
    margins: Optional[Dict[str, str]] = None,
    font_size: str = "12pt",
    font_family: str = "serif",
    line_height: str = "1.6",
    page_size: str = "A4",
) -> str:
    """Convert a Manuscript to an HTML string suitable for PDF rendering."""
    margin_top = margins.get("top", "1in") if margins else "1in"
    margin_right = margins.get("right", "1in") if margins else "1in"
    margin_bottom = margins.get("bottom", "1in") if margins else "1in"
    margin_left = margins.get("left", "1in") if margins else "1in"

    chapters_html = []
    for i, chapter in enumerate(manuscript.chapters):
        chapter_items = []
        for item in chapter.content:
            if isinstance(item, Heading):
                level = min(max(item.level, 1), 6)
                chapter_items.append(f"<h{level}>{_escape_html(item.text)}</h{level}>")
            elif isinstance(item, Paragraph):
                chapter_items.append(f"<p>{_escape_html(item.text)}</p>")

        chapters_html.append(
            f'<div class="chapter">\n'
            f"  <h1>{_escape_html(chapter.title)}</h1>\n"
            f"  {''.join(chapter_items)}\n"
            f"</div>"
        )

    html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8"/>
  <title>{_escape_html(manuscript.title)}</title>
  <style>
    @page {{
      size: {page_size};
      margin: {margin_top} {margin_right} {margin_bottom} {margin_left};
    }}
    body {{
      font-family: {font_family};
      font-size: {font_size};
      line-height: {line_height};
    }}
    h1 {{
      page-break-before: always;
      margin-top: 2em;
    }}
    h1:first-of-type {{
      page-break-before: avoid;
    }}
    h2 {{
      page-break-before: always;
      margin-top: 1.5em;
    }}
    h3 {{
      page-break-before: always;
      margin-top: 1.2em;
    }}
    p {{
      margin-bottom: 0.5em;
      text-indent: 1em;
    }}
    .chapter {{
      page-break-before: always;
    }}
    .chapter:first-of-type {{
      page-break-before: avoid;
    }}
  </style>
</head>
<body>
  <h1>{_escape_html(manuscript.title)}</h1>
  {''.join(chapters_html)}
</body>
</html>"""
    return html


class PDFExporter:
    """Exports a Manuscript to PDF format using weasyprint."""

    def export(
        self,
        manuscript: Manuscript,
        output_path: str = "output.pdf",
        **options: Any,
    ) -> str:
        """Generate a PDF file from the manuscript.

        Args:
            manuscript: The Manuscript to export.
            output_path: Path for the output .pdf file.
            **options: margins, font_size, font_family, line_height, page_size.

        Returns:
            The path to the generated PDF file.
        """
        # Generate HTML
        html = _manuscript_to_html(manuscript, **options)

        # Try weasyprint first
        try:
            from weasyprint import HTML
            HTML(string=html).write_pdf(output_path)
            return output_path
        except ImportError:
            pass

        # Fallback: use wkhtmltopdf if available
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                f.write(html)
                html_path = f.name
            try:
                subprocess.run(
                    ["wkhtmltopdf", html_path, output_path],
                    check=True,
                    capture_output=True,
                )
                return output_path
            finally:
                os.unlink(html_path)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        # Last resort: raise a helpful error
        raise RuntimeError(
            "No PDF engine available. Install weasyprint (`pip install weasyprint`) "
            "or wkhtmltopdf to enable PDF export."
        )
