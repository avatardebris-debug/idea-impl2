"""EPUB exporter — generates EPUB3 files from a Manuscript."""

import os
import zipfile
from typing import Any, Dict, List, Optional

from ..models import Chapter, Heading, Manuscript, Paragraph


def _escape_xml(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _generate_css(**options: Any) -> str:
    """Generate CSS styles for the EPUB."""
    font_family = options.get("font_family", "serif")
    font_size = options.get("font_size", "1em")
    line_height = options.get("line_height", "1.6")
    margin_top = options.get("margin_top", "1in")
    margin_right = options.get("margin_right", "1in")
    margin_bottom = options.get("margin_bottom", "1in")
    margin_left = options.get("margin_left", "1in")

    return f"""
body {{
    font-family: {font_family};
    font-size: {font_size};
    line-height: {line_height};
    margin: {margin_top} {margin_right} {margin_bottom} {margin_left};
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
"""


def _generate_chapter_xhtml(chapter: Chapter, chapter_id: str) -> str:
    """Generate XHTML content for a single chapter."""
    items = []
    for item in chapter.content:
        if isinstance(item, Heading):
            level = min(max(item.level, 1), 6)
            items.append(f"<h{level}>{_escape_xml(item.text)}</h{level}>")
        elif isinstance(item, Paragraph):
            items.append(f"<p>{_escape_xml(item.text)}</p>")

    return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  <title>{_escape_xml(chapter.title)}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <div class="chapter">
    <h1>{_escape_xml(chapter.title)}</h1>
    {''.join(items)}
  </div>
</body>
</html>"""


class EPUBExporter:
    """Exports a Manuscript to EPUB3 format."""

    def export(
        self,
        manuscript: Manuscript,
        output_path: str = "output.epub",
        **options: Any,
    ) -> str:
        """Generate an EPUB file from the manuscript.

        Args:
            manuscript: The Manuscript to export.
            output_path: Path for the output .epub file.
            **options: Passed through to CSS generation.

        Returns:
            The path to the generated EPUB file.
        """
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFIATED) as zf:
            # mimetype — must be first and uncompressed
            zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

            # META-INF/container.xml
            container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
            zf.writestr("META-INF/container.xml", container_xml)

            # Generate chapter XHTML files
            chapter_files = []
            for i, chapter in enumerate(manuscript.chapters):
                chapter_id = f"chapter_{i + 1}"
                xhtml_content = _generate_chapter_xhtml(chapter, chapter_id)
                xhtml_filename = f"{chapter_id}.xhtml"
                zf.writestr(xhtml_filename, xhtml_content)
                chapter_files.append((chapter_id, xhtml_filename))

            # Generate content.opf
            opf_items = []
            spine_items = []
            for i, (chapter_id, xhtml_filename) in enumerate(chapter_files):
                opf_items.append(f'  <item id="{chapter_id}" href="{xhtml_filename}" media-type="application/xhtml+xml"/>')
                spine_items.append(f'  <itemref idref="{chapter_id}"/>')

            opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="uid">urn:uuid:{_generate_uuid()}</dc:identifier>
    <dc:title>{_escape_xml(manuscript.title)}</dc:title>
    <dc:creator>{_escape_xml(manuscript.author)}</dc:creator>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="style" href="style.css" media-type="text/css"/>
    {'\n    '.join(opf_items)}
  </manifest>
  <spine>
    {'\n    '.join(spine_items)}
  </spine>
</package>"""
            zf.writestr("content.opf", opf_content)

            # Generate nav.xhtml (TOC)
            nav_entries = []
            for i, (chapter_id, xhtml_filename) in enumerate(chapter_files):
                nav_entries.append(f'      <li><a href="{xhtml_filename}">{_escape_xml(manuscript.chapters[i].title)}</a></li>')

            nav_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  <title>Table of Contents</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc" id="toc">
    <ol>
      {'\n      '.join(nav_entries)}
    </ol>
  </nav>
</body>
</html>"""
            zf.writestr("nav.xhtml", nav_content)

            # Generate style.css
            css = _generate_css(**options)
            zf.writestr("style.css", css)

        return output_path


def _generate_uuid() -> str:
    """Generate a simple UUID-like string."""
    import uuid
    return str(uuid.uuid4())
