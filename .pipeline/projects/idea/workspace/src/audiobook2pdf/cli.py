"""CLI entry point for audiobook2pdf."""

import argparse
import sys

from audiobook2pdf.extractor import extract_metadata
from audiobook2pdf.pdf_generator import generate_pdf


def main():
    """Main CLI entry point.

    Usage:
        python -m audiobook2pdf input.m4b output.pdf
    """
    parser = argparse.ArgumentParser(
        description="Convert Amazon audiobook (m4b/mp4) to PDF with metadata."
    )
    parser.add_argument("input", help="Path to the input audiobook file (m4b/mp4)")
    parser.add_argument("output", help="Path to the output PDF file")
    args = parser.parse_args()

    print(f"Extracting metadata from: {args.input}")
    metadata = extract_metadata(args.input)
    print(f"  Title: {metadata['title']}")
    print(f"  Author: {metadata['author']}")
    print(f"  Narrator: {metadata['narrator']}")
    print(f"  Duration: {_format_duration(metadata['duration'])}")
    print(f"  Chapters: {len(metadata['chapters'])}")

    print(f"Generating PDF: {args.output}")
    generate_pdf(metadata, args.output)
    print("Done.")


def _format_duration(seconds):
    """Format seconds into HH:MM:SS."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


if __name__ == "__main__":
    main()
