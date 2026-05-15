"""PDF exporter — generates print-ready PDF from a Manuscript using WeasyPrint."""

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


def _manuscript_to_html(manuscript: Manuscript, **options: Any) -> str:
    """Convert a Manuscript to a complete HTML document for PDF rendering."""
    # Extract options with defaults
    margins = options.get("margins", {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"})
    # Ensure all individual margin keys have defaults to avoid KeyError
    for key in ("top", "right", "bottom", "left"):
        margins.setdefault(key, "1in")
    font_family = options.get("font_family", "serif")
    font_size = options.get("font_size", "12pt")
    line_height = options.get("line_height", "1.6")
    page_size = options.get("page_size", "A4")

    # Build chapter content
    chapter_bodies = []
    for chapter in manuscript.chapters:
        items = []
        for item in chapter.content:
            if isinstance(item, Heading):
                tag = f"h{min(max(item.level, 1), 6)}"
                items.append(f"<{tag}>{_escape_html(item.text)}</{tag}>")
            elif isinstance(item, Paragraph):
                items.append(f"<p>{_escape_html(item.text)}</p>")
        chapter_bodies.append(
            f'<div class="chapter">'
            f"<h1>{_escape_html(chapter.title)}</h1>"
            f"{''.join(items)}"
            f"</div>"
        )

    body_content = "\n".join(chapter_bodies)

    html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  <title>{_escape_html(manuscript.title)}</title>
  <style>
    @page {{
        size: {page_size};
        margin: {margins['top']} {margins['right']} {margins['bottom']} {margins['left']};
    }}
    body {{
        font-family: {font_family};
        font-size: {font_size};
        line-height: {line_height};
        text-align: justify;
    }}
    h1 {{
        page-break-before: always;
        margin-top: 2em;
        font-size: 1.8em;
    }}
    h1:first-of-type {{
        page-break-before: avoid;
    }}
    h2 {{
        page-break-before: always;
        margin-top: 1.5em;
        font-size: 1.4em;
    }}
    h3 {{
        page-break-before: always;
        margin-top: 1.2em;
        font-size: 1.2em;
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
  {''.join(chapter_bodies)}
</body>
</html>"""
    return html


class PDFExporter:
    """Exports a Manuscript to PDF format using xhtml2pdf."""
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
            **options:
                margins (dict): Page margins with keys top/right/bottom/left.
                font_family (str): CSS font family.
                font_size (str): CSS font size.
                line_height (float): Line height multiplier.
                page_size (str): CSS page size (e.g., 'A4', 'Letter').

        Returns:
            The path to the generated PDF file.
        """
        html_content = _manuscript_to_html(manuscript, **options)

        try:
            from xhtml2pdf import pisa
            with open(output_path, "wb") as f:
                pisa_status = pisa.CreatePDF(html_content, dest=f)
                if pisa_status.err:
                    raise RuntimeError(f"Error generating PDF: {pisa_status.err}")
        except ImportError:
            raise RuntimeError(
                "xhtml2pdf is required for PDF export. "
                "Install it with: pip install xhtml2pdf"
            )

        return output_path
