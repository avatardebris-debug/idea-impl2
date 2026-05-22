"""MOBI exporter — converts a Manuscript to MOBI format via EPUB + calibre's ebook-convert."""

import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, Optional

from ..models import Manuscript
from .epub_exporter import EPUBExporter


class MOBIExporter:
    """Exports a Manuscript to MOBI format.

    Uses calibre's ebook-convert tool to convert from an intermediate EPUB.
    Falls back to producing an EPUB if calibre is not available.
    """

    def export(
        self,
        manuscript: Manuscript,
        output_path: str = "output.mobi",
        **options: Any,
    ) -> str:
        """Generate a MOBI file from the manuscript.

        Args:
            manuscript: The Manuscript to export.
            output_path: Path for the output .mobi file.
            **options: Passed through to EPUB export and ebook-convert.

        Returns:
            The path to the generated MOBI file (or EPUB if calibre unavailable).
        """
        # First, generate an intermediate EPUB
        epub_exporter = EPUBExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = os.path.join(tmpdir, "intermediate.epub")
            epub_exporter.export(manuscript, output_path=epub_path, **options)

            # Try calibre's ebook-convert
            mobi_path = self._convert_with_calibre(epub_path, output_path)
            if mobi_path:
                return mobi_path

            # Fallback: return the EPUB with .epub extension
            # (some Kindle devices accept EPUB files renamed to .mobi)
            # Use .epub extension to honestly reflect the file format
            fallback_path = output_path
            if fallback_path.endswith(".mobi"):
                fallback_path = fallback_path[:-5] + ".epub"
            shutil.copy2(epub_path, fallback_path)
            return fallback_path

    def _convert_with_calibre(
        self, epub_path: str, output_path: str
    ) -> Optional[str]:
        """Try to convert EPUB to MOBI using calibre's ebook-convert.

        Returns the output path on success, None on failure.
        """
        try:
            result = subprocess.run(
                ["ebook-convert", epub_path, output_path],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return output_path
            else:
                return None
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return None
