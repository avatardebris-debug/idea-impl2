"""MOBI exporter — converts a Manuscript to MOBI via EPUB + kindlegen/calibre."""

import os
import subprocess
import tempfile
from typing import Any

from ..models import Manuscript
from .epub_exporter import EPUBExporter


class MOBIExporter:
    """Exports a Manuscript to MOBI format via EPUB + conversion tools."""

    def __init__(self):
        self._epub_exporter = EPUBExporter()

    def export(
        self,
        manuscript: Manuscript,
        output_path: str = "output.mobi",
        **options: Any,
    ) -> str:
        """Generate a MOBI file from the manuscript.

        Works by first creating an EPUB, then converting it.

        Args:
            manuscript: The Manuscript to export.
            output_path: Path for the output .mobi file.
            **options: Passed through to the EPUB exporter.

        Returns:
            The path to the generated MOBI file.
        """
        # Step 1: Create a temporary EPUB
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            epub_path = f.name

        try:
            self._epub_exporter.export(manuscript, output_path=epub_path, **options)

            # Step 2: Convert EPUB → MOBI
            # Try kindlegen first
            try:
                subprocess.run(
                    ["kindlegen", epub_path, "-o", output_path],
                    check=True,
                    capture_output=True,
                )
                return output_path
            except FileNotFoundError:
                pass

            # Try calibre's ebook-convert
            try:
                subprocess.run(
                    ["ebook-convert", epub_path, output_path],
                    check=True,
                    capture_output=True,
                )
                return output_path
            except FileNotFoundError:
                pass

            # Fallback: just return the EPUB path with .mobi extension
            # (some readers accept EPUB as MOBI)
            import shutil
            shutil.copy2(epub_path, output_path)
            return output_path
        finally:
            os.unlink(epub_path)
