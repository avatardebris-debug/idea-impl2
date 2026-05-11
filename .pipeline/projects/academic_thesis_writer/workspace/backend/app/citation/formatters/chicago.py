"""Chicago Manual of Style (17th ed.) citation formatter."""

from __future__ import annotations

from typing import List, Optional

from ..models import BibliographyEntry, CitationStyle, Source


class ChicagoFormatter:
    """Format bibliography entries in Chicago style (Notes-Bibliography)."""

    STYLE = CitationStyle.CHICAGO

    @staticmethod
    def format(source: Source, citation_key: str) -> BibliographyEntry:
        """Format a single source in Chicago style."""
        formatted = ChicagoFormatter._format_entry(source)
        return BibliographyEntry(
            citation_key=citation_key,
            source_id=source.id,
            style=ChicagoFormatter.STYLE,
            formatted=formatted,
        )

    @staticmethod
    def format_inline(source: Source, page: Optional[str] = None) -> str:
        """Return a Chicago footnote-style inline citation marker."""
        # Chicago uses superscript numbers; we return a placeholder
        return "¹"

    @staticmethod
    def _format_entry(source: Source) -> str:
        """Format a full Chicago bibliography entry."""
        # Authors: Last, First for first author; First Last for subsequent
        authors_str = ChicagoFormatter._format_authors(source.authors)

        # Title
        title = source.title or "Untitled"
        title_formatted = f"*{title}*."

        # Publication info
        pub_info = ""
        if source.publisher:
            pub_info = f" {source.publisher}, "
        if source.year:
            pub_info += f"{source.year}."
        elif source.journal:
            pub_info = f" {source.journal}, "
            if source.year:
                pub_info += f"{source.year}."

        # URL
        url_part = ""
        if source.url:
            url_part = f" {source.url}."

        # Build the entry
        parts = [f"{authors_str} {title_formatted}"]
        if pub_info:
            parts.append(pub_info.rstrip())
        if url_part:
            parts.append(url_part)

        return " ".join(parts)

    @staticmethod
    def _format_authors(authors: List[str]) -> str:
        """Format authors for Chicago style."""
        if not authors:
            return "Unknown, First."
        formatted = []
        for i, author in enumerate(authors[:3]):  # Chicago lists up to 3 authors
            parts = author.strip().split()
            if len(parts) >= 2:
                last = parts[-1]
                first = " ".join(parts[:-1])
                if i == 0:
                    formatted.append(f"{last}, {first}")
                else:
                    formatted.append(f"{first} {last}")
            else:
                formatted.append(author)
        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]} and {formatted[1]}"
        else:
            return f"{', '.join(formatted[:-1])}, and {formatted[-1]}"
