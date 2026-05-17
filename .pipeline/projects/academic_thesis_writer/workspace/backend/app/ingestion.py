"""Ingestion helpers for source metadata extraction.

Provides factory classes for creating Source objects from different
input types: manual entry, URL fetching, and PDF extraction.
"""

from __future__ import annotations

from typing import List, Optional

from .models import Source


class ManualEntrySource:
    """Factory for manually-entered sources."""

    @staticmethod
    def create(
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        abstract: str = "",
        url: Optional[str] = None,
    ) -> Source:
        """Create a Source from manual entry data."""
        return Source(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            url=url,
            source_type="manual",
        )


class URLFetcher:
    """Fetch metadata from a URL."""

    @staticmethod
    def fetch(url: str) -> Source:
        """Fetch source metadata from a URL.

        In production, this would use a service like Crossref or OpenAlex.
        For now, returns a placeholder Source.
        """
        return Source(
            title="Untitled",
            authors=[],
            url=url,
            source_type="url",
        )


class PDFExtractor:
    """Extract text and metadata from a PDF file."""

    @staticmethod
    def extract(file_path: str, url: Optional[str] = None) -> Source:
        """Extract metadata from a PDF file.

        In production, this would use a PDF parsing library.
        For now, returns a placeholder Source.
        """
        return Source(
            title="Untitled",
            authors=[],
            url=url,
            source_type="pdf",
        )
