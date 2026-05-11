"""EPUB3 exporter — generates a valid EPUB3 package from a Manuscript."""

import os
import zipfile
import uuid
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


def _chapter_to_xhtml(chapter: Chapter, chapter_index: int) -> str:
    """Convert a Chapter to an XHTML string."""
    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        '<!DOCTYPE html PUBLIC "-////DTD XHTML 1.1//EN" '
        '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'
    )
    lines.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">')
    lines.append("<head>")
    lines.append(
        f'  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>'
    )
    lines.append(f'  <title>{_escape_html(chapter.title)}</title>')
    lines.append("</head>")
    lines.append("<body>")
    lines.append(f'  <h1>{_escape_html(chapter.title)}</h1>')

    for item in chapter.content:
        if isinstance(item, Heading):
            tag = f"h{min(max(item.level, 1), 6)}"
            lines.append(f'  <{tag}>{_escape_html(item.text)}</{tag}>')
        elif isinstance(item, Paragraph):
            lines.append(f"  <p>{_escape_html(item.text)}</p>")

    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines)


class EPUBExporter:
    """Exports a Manuscript to EPUB3 format."""

    def export(
        self,
        manuscript: Manuscript,
        output_path: str = "output.epub",
        **options: Any,
    ) -> str:
        """Generate a valid EPUB3 file.

        Args:
            manuscript: The Manuscript to export.
            output_path: Path for the output .epub file.
            **options: Ignored (reserved for future EPUB-specific options).

        Returns:
            The path to the generated EPUB file.
        """
        # Generate unique IDs for resources
        spine_id = str(uuid.uuid4())
        cover_id = str(uuid.uuid4())

        # Build chapter XHTML files
        chapter_xhtml: list[tuple[str, str]] = []  # (filename, xhtml_content)
        for i, chapter in enumerate(manuscript.chapters):
            filename = f"chapter_{i + 1}.xhtml"
            xhtml_content = _chapter_to_xhtml(chapter, i)
            chapter_xhtml.append((filename, xhtml_content))

        # Build OPF manifest entries
        manifest_entries = []
        spine_entries = []
        for i, (filename, _) in enumerate(chapter_xhtml):
            item_id = f"chapter_{i + 1}"
            manifest_entries.append(
                f'    <item id="{item_id}" href="{filename}" '
                f'media-type="application/xhtml+xml"/>'
            )
            spine_entries.append(f'    <itemref idref="{item_id}"/>')

        # Build content.opf
        opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="uid">{str(uuid.uuid4())}</dc:identifier>
    <dc:title>{_escape_html(manuscript.title)}</dc:title>
    <dc:language>en</dc:language>
    <dc:creator>{_escape_html(manuscript.author) if manuscript.author else "Unknown"}</dc:creator>
    <meta property="dcterms:modified">{_escape_html(_rfc3339_now())}</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="style" href="style.css" media-type="text/css"/>
{chr(10).join(manifest_entries)}
  </manifest>
  <spine>
{chr(10).join(spine_entries)}
  </spine>
</package>"""

        # Build nav.xhtml (EPUB3 navigation document)
        nav_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  <title>Navigation</title>
</head>
<body>
  <nav epub:type="toc">
    <h1>Table of Contents</h1>
    <ol>
{chr(10).join(f'      <li><a href="{fn}">{_escape_html(ch.title)}</a></li>' for fn, ch in zip([f"chapter_{i+1}.xhtml" for i in range(len(manuscript.chapters))], manuscript.chapters))}
    </ol>
  </nav>
</body>
</html>"""

        # Build style.css
        css_content = """html {
    font-family: serif;
    font-size: 1em;
    line-height: 1.6;
}
body {
    margin: 1em;
    text-align: justify;
}
h1 {
    page-break-before: always;
    margin-top: 2em;
}
p {
    margin-bottom: 0.5em;
    text-indent: 1em;
}
"""

        # Build META-INF/container.xml
        container_content = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        # Create the EPUB (which is a ZIP file)
        # mimetype must be first and uncompressed
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write mimetype first (uncompressed)
            zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

            # Write META-INF/container.xml
            zf.writestr("META-INF/container.xml", container_content)

            # Write content.opf
            zf.writestr("content.opf", opf_content)

            # Write nav.xhtml
            zf.writestr("nav.xhtml", nav_content)

            # Write style.css
            zf.writestr("style.css", css_content)

            # Write chapter files
            for filename, xhtml_content in chapter_xhtml:
                zf.writestr(filename, xhtml_content)

        return output_path


def _rfc3339_now() -> str:
    """Return current time in RFC 3339 format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
