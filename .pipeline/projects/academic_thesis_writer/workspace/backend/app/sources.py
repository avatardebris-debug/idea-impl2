"""Unified source management for the thesis writer.

Provides a high-level SourceManager that coordinates ingestion from
manual entry, URL fetching, and PDF extraction, and persists sources
via the database layer.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .config import settings
from .database import Database
from .ingestion import ManualEntrySource, PDFExtractor, URLFetcher
from .models import Source

logger = logging.getLogger(__name__)


class SourceManager:
    """Manages source lifecycle: add, retrieve, remove, and persist."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database(settings.db_path)

    # ── Add sources ──────────────────────────────────────────────

    def add_manual(
        self,
        project_id: str,
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        abstract: str = "",
        url: Optional[str] = None,
    ) -> Source:
        """Add a manually-entered source."""
        source = ManualEntrySource.create(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            url=url,
        )
        self.db.add_source_to_project(project_id, source)
        logger.info("Added manual source: %s", title)
        return source

    def add_from_url(self, project_id: str, url: str) -> Source:
        """Fetch metadata from a URL and add as a source."""
        source = URLFetcher.fetch(url)
        source.url = url
        source.source_type = "url"
        self.db.add_source_to_project(project_id, source)
        logger.info("Added URL source: %s", source.title)
        return source

    def add_from_pdf(self, project_id: str, file_path: str, url: Optional[str] = None) -> Source:
        """Extract text from a PDF and add as a source."""
        source = PDFExtractor.extract(file_path, url=url)
        source.source_type = "pdf"
        self.db.add_source_to_project(project_id, source)
        logger.info("Added PDF source: %s", source.title or "Untitled")
        return source

    # ── Retrieve sources ─────────────────────────────────────────

    def get_sources(self, project_id: str) -> List[Source]:
        """Return all sources for a project."""
        return self.db.get_sources_for_project(project_id)

    def get_source_by_title(self, project_id: str, title: str) -> Optional[Source]:
        """Return a single source by title."""
        sources = self.get_sources(project_id)
        for s in sources:
            if s.title == title:
                return s
        return None

    # ── Remove sources ───────────────────────────────────────────

    def remove_source(self, project_id: str, title: str) -> bool:
        """Remove a source by title. Returns True if removed."""
        return self.db.remove_source_from_project(project_id, title)

    # ── Bulk operations ──────────────────────────────────────────

    def add_sources(self, project_id: str, sources: List[Source]) -> None:
        """Add multiple sources to a project."""
        self.db.add_sources_to_project(project_id, sources)

    def clear_sources(self, project_id: str) -> None:
        """Remove all sources from a project."""
        self.db.clear_sources_for_project(project_id)
