"""IEEE citation formatter."""

from __future__ import annotations

from typing import List, Optional

from ..models import BibliographyEntry, CitationStyle, Source


class IEEEFormatter:
    """Format bibliography entries in IEEE style."""

    STYLE = CitationStyle.IEEE

    def __init__(self):
        self._ref_num = 0

    def format(self, source: Source, ref_num: Optional[int] = None) -> BibliographyEntry:
        """Format a single source in IEEE style."""
        self._ref_num = ref_num or (self._ref_num + 1)
        formatted = IEEEFormatter._format_entry(source, self._ref_num)
        return BibliographyEntry(
            citation_key=f"[{self._ref_num}]",
            source_id=source.id,
            style=IEEEFormatter.STYLE,
            formatted=formatted,
        )

    def format_inline(self, ref_num: int) -> str:
        """Return an IEEE inline citation."""
        return f"[{ref_num}]"

    @staticmethod
    def _format_entry(source: Source, ref_num: int) -> str:
        """Format a full IEEE bibliography entry."""
        # Authors: Initials. Last for each author
        authors_str = IEEEFormatter._format_authors(source.authors)

        # Title
        title = source.title or "Untitled"

        # Publication info
        pub_info = ""
        if source.journal:
            pub_info = f" *{source.journal}*, "
        elif source.publisher:
            pub_info = f" *{source.publisher}*, "

        # Year
        year = source.year or "n.d."

        # Pages
        pages = ""
        if source.pages:
            pages = f", pp. {source.pages}."
        else:
            pages = "."

        # DOI/URL
        doi_part = ""
        if source.doi:
            doi_part = f" DOI: {source.doi}."
        elif source.url:
            doi_part = f" [Online]. Available: {source.url}."

        # Build the entry
        return f"[{ref_num}] {authors_str}, \"{title}\"{pub_info}{year}{pages}{doi_part}"

    @staticmethod
    def _format_authors(authors: List[str]) -> str:
        """Format authors as 'A. B. Last, C. D. Last'."""
        if not authors:
            return "A. B. Unknown"
        formatted = []
        for author in authors[:6]:  # IEEE lists up to 6 authors
            parts = author.strip().split()
            if len(parts) >= 2:
                last = parts[-1]
                initials = ".".join(p[0] + "." for p in parts[:-1] if p)
                formatted.append(f"{initials} {last}")
            else:
                formatted.append(f"A. {author}")
        if len(formatted) <= 2:
            return ", ".join(formatted)
        # IEEE: list all up to 6, then "et al." for more
        return ", ".join(formatted[:6]) + ", et al." if len(formatted) > 6 else ", ".join(formatted)
