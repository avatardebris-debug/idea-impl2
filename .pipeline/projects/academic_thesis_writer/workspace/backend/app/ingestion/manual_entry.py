"""Manual source entry."""

from __future__ import annotations

from typing import List, Optional

from ..models import Source


class ManualEntrySource:
    """Create a Source from manual input."""

    @staticmethod
    def create(
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        abstract: str = "",
        url: Optional[str] = None,
    ) -> Source:
        return Source(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            url=url,
            source_type="manual",
        )
