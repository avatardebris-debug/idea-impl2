"""MLA 9th edition citation formatter."""

from __future__ import annotations

from typing import List, Optional

from ..models import BibliographyEntry, CitationStyle, Source


class MLAFormatter:
    """Format bibliography entries in MLA 9th style."""

    STYLE = CitationStyle.MLA

    @staticmethod
    def format(source: Source, citation_key: str) -> BibliographyEntry:
        """Format a single source in MLA 9th style."""
        formatted = MLAFormatter._format_entry(source)
        return BibliographyEntry(
            citation_key=citation_key,
            source_id=source.id,
            style=MLAFormatter.STYLE,
            formatted=formatted,
        )

    @staticmethod
    def format_inline(source: Source, page: Optional[str] = None) -> str:
        """Return an MLA inline citation."""
        author = source.authors[0].split()[-1] if source.authors else "Unknown"
        if page:
            return f"({author} {page})"
        return f"({author})"

    @staticmethod
    def _format_entry(source: Source) -> str:
        """Format a full MLA bibliography entry."""
        # Authors: Last, First. for multiple authors
        authors_str = MLAFormatter._format_authors(source.authors)

        # Title: italicize if it's a book/report; quote if it's an article
        title = source.title or "Untitled"
        if source.url and "doi.org" in source.url:
            # Journal article
            title_formatted = f'"{title}."'
        else:
            # Book or web source
            title_formatted = f"*{title}*."

        # Container (journal/book title)
        container = ""
        if source.journal:
            container = f" {source.journal}, "
        elif source.publisher:
            container = f" {source.publisher}, "

        # Year
        year = source.year or "n.d."

        # URL
        url_part = ""
        if source.url:
            url_part = f" {source.url}."

        # Build the entry
        parts = [f"{authors_str} {title_formatted}"]
        if container:
            parts.append(container.rstrip(", "))
        parts.append(f"{year}.")
        if url_part:
            parts.append(url_part)

        return " ".join(parts)

    @staticmethod
    def _format_authors(authors: List[str]) -> str:
        """Format authors as 'Last, First, and Last, First.'"""
        if not authors:
            return "Unknown, First."
        formatted = []
        for author in authors[:3]:  # MLA lists up to 3 authors
            parts = author.strip().split()
            if len(parts) >= 2:
                last = parts[-1]
                first = " ".join(parts[:-1])
                formatted.append(f"{last}, {first}")
            else:
                formatted.append(f"{author}, First")
        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]} and {formatted[1]}"
        else:
            return f"{', '.join(formatted[:-1])}, and {formatted[-1]}"
