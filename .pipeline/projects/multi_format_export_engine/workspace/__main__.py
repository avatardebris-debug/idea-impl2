"""CLI entry point for the Multi-Format Export Engine.

Usage:
    python -m multi_format_export_engine input.txt --format epub
    python -m multi_format_export_engine input.txt --format pdf --margins top=1in right=1in bottom=1in left=1in
    python -m multi_format_export_engine input.txt --format mobi
"""

import argparse
import os
import sys

from multi_format_export_engine import ExportEngine, Manuscript
from multi_format_export_engine.exporters.epub_exporter import EPUBExporter
from multi_format_export_engine.exporters.pdf_exporter import PDFExporter
from multi_format_export_engine.exporters.mobi_exporter import MOBIExporter


def _parse_manuscript_text(text: str) -> Manuscript:
    """Parse a plain-text manuscript into a Manuscript object.

    Simple format:
    - Lines starting with '# ' are chapter titles.
    - Lines starting with '## ' are sub-headings.
    - Blank lines separate paragraphs.
    - All other lines are paragraph content.
    """
    manuscript = Manuscript(title="Untitled")
    current_chapter = None
    current_paragraph_lines: list[str] = []

    def _flush_paragraph():
        nonlocal current_paragraph_lines
        if current_paragraph_lines:
            text = " ".join(line.strip() for line in current_paragraph_lines if line.strip())
            if text and current_chapter:
                current_chapter.add_paragraph(text)
            current_paragraph_lines = []

    lines = text.split("\n")
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            _flush_paragraph()
            title = line[2:].strip()
            current_chapter = manuscript.add_chapter_title(title)
        elif line.startswith("## "):
            _flush_paragraph()
            if current_chapter:
                current_chapter.add_heading(line[3:].strip(), level=2)
        elif line.strip() == "":
            _flush_paragraph()
        else:
            current_paragraph_lines.append(line)

    _flush_paragraph()

    if not manuscript.chapters:
        # If no chapters detected, put everything in one chapter
        chapter = manuscript.add_chapter_title("Chapter 1")
        if current_paragraph_lines:
            text = " ".join(line.strip() for line in current_paragraph_lines if line.strip())
            if text:
                chapter.add_paragraph(text)

    return manuscript


def _parse_margins(margin_str: str) -> dict:
    """Parse margin string like 'top=1in right=1in bottom=1in left=1in'."""
    margins = {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"}
    if not margin_str:
        return margins
    for part in margin_str.split():
        if "=" in part:
            key, value = part.split("=", 1)
            if key in margins:
                margins[key] = value
            else:
                print(f"Warning: unrecognized margin key '{key}' ignored (valid keys: top, right, bottom, left)", file=sys.stderr)
    return margins


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="multi_format_export_engine",
        description="Export manuscripts to EPUB, PDF, or MOBI formats.",
    )
    parser.add_argument(
        "input",
        help="Path to the input manuscript file (plain text).",
    )
    parser.add_argument(
        "--format",
        "-f",
        dest="fmt",
        choices=["epub", "pdf", "mobi"],
        default="epub",
        help="Export format (default: epub).",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        default=None,
        help="Output file path (default: <title>.<format>).",
    )
    parser.add_argument(
        "--title",
        "-t",
        dest="title",
        default=None,
        help="Manuscript title (overrides filename).",
    )
    parser.add_argument(
        "--author",
        "-a",
        dest="author",
        default="",
        help="Author name.",
    )
    parser.add_argument(
        "--margins",
        dest="margins",
        default=None,
        help="PDF margins: 'top=1in right=1in bottom=1in left=1in'.",
    )
    parser.add_argument(
        "--font-family",
        dest="font_family",
        default="serif",
        help="PDF font family (default: serif).",
    )
    parser.add_argument(
        "--font-size",
        dest="font_size",
        default="12pt",
        help="PDF font size (default: 12pt).",
    )
    parser.add_argument(
        "--page-size",
        dest="page_size",
        default="A4",
        help="PDF page size (default: A4).",
    )

    args = parser.parse_args()

    # Read input file
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    # Build manuscript
    manuscript = _parse_manuscript_text(text)
    if args.title:
        manuscript.title = args.title
    if args.author:
        manuscript.author = args.author

    # Build export engine and register exporters
    engine = ExportEngine()
    engine.register_exporter("epub", EPUBExporter())
    engine.register_exporter("pdf", PDFExporter())
    engine.register_exporter("mobi", MOBIExporter())

    # Build export options
    export_options = {}
    if args.fmt == "pdf":
        export_options["margins"] = _parse_margins(args.margins)
        export_options["font_family"] = args.font_family
        export_options["font_size"] = args.font_size
        export_options["page_size"] = args.page_size

    # Export
    output_path = engine.export(
        args.fmt,
        manuscript,
        output_path=args.output,
        **export_options,
    )
    print(f"Exported to: {output_path}")


if __name__ == "__main__":
    main()
