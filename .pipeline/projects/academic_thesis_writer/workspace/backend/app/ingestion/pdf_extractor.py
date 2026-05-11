"""PDF text extraction."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import pdfplumber
import requests

from ..models import Source


class PDFExtractor:
    """Extract text from a PDF file."""

    @staticmethod
    def extract(file_path: str, url: Optional[str] = None) -> Source:
        """Extract text from a PDF file."""
        full_text = PDFExtractor._read_pdf(file_path)
        return Source(
            title="",  # Will be filled by LLM later
            authors=[],
            year=None,
            abstract="",
            url=url,
            pdf_path=file_path,
            full_text=full_text[:50000],  # Cap at 50k chars
            source_type="pdf",
        )

    @staticmethod
    def _read_pdf(file_path: str) -> str:
        """Read text from a PDF file using pdfplumber."""
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    @staticmethod
    def extract_from_url(url: str) -> Source:
        """Download a PDF from a URL and extract text."""
        headers = {"User-Agent": "Mozilla/5.0 (AcademicThesisWriter/1.0)"}
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        try:
            return PDFExtractor.extract(tmp_path, url=url)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
