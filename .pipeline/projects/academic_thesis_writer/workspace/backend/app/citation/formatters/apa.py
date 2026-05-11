"""APA 7th edition citation formatter."""

from __future__ import annotations

from typing import List, Optional

from ..models import BibliographyEntry, CitationStyle, Source


class APAFormatter:
    """Format bibliography entries in APA 7th style."""

    STYLE = CitationStyle.APA

    @staticmethod
    def format(source: Source, citation_key: str) -> BibliographyEntry:
        """Format a single source in APA 7th style."""
        formatted = APAFormatter._format_entry(source)
        return BibliographyEntry(
            citation_key=citation_key,
            source_id=source.id,
            style=APAFormatter.STYLE,
            formatted=formatted,
        )

    @staticmethod
    def format_inline(source: Source, page: Optional[str] = None) -> str:
        """Return an APA inline citation."""
        author = source.authors[0].split()[-1] if source.authors else "Unknown"
        year = source.year or "n.d."
        if page:
            return f"({author}, {year}, p. {page})"
        return f"({author}, {year})"

    @staticmethod
    def _format_entry(source: Source) -> str:
        """Format a full APA bibliography entry."""
        # Authors: Last, Initial. for multiple authors
        authors_str = APAFormatter._format_authors(source.authors)

        # Year
        year = f"({source.year or 'n.d.'})"

        # Title: italicize if it's a book/report; sentence case for articles
        title = source.title or "Untitled"
        title = APAFormatter._sentence_case(title)

        # Determine if it's a journal article, book, or web source
        if source.url and "doi.org" in source.url:
            # Journal article with DOI
            parts = [f"{authors_str}. {year}. {title}. "]
            # DOI is extracted from URL
            doi = source.url.split("doi.org/")[-1] if "doi.org" in source.url else ""
            parts.append(f"{doi}")
            return "".join(parts)
        elif source.url:
            # Web source
            parts = [f"{authors_str}. {year}. {title}. "]
            if source.url:
                parts.append(f"Retrieved from {source.url}")
            return "".join(parts)
        else:
            # Default: book/report style
            return f"{authors_str}. {year}. {title}."

    @staticmethod
    def _format_authors(authors: List[str]) -> str:
        """Format authors as 'Last, I., & Last, I.'"""
        if not authors:
            return "Unknown, A."
        formatted = []
        for author in authors[:20]:  # APA limits to 20 authors
            parts = author.strip().split()
            if len(parts) >= 2:
                last = parts[-1]
                initials = ".".join(p[0] + "." for p in parts[:-1] if p)
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(f"{author}, A.")
        if len(formatted) == 1:
            return formatted[0]
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]

    @staticmethod
    def _sentence_case(title: str) -> str:
        """Convert title to sentence case."""
        if not title:
            return ""
        words = title.split()
        if not words:
            return ""
        # Capitalize first word, lowercase the rest (unless it's a proper noun)
        result = [words[0].capitalize()]
        for word in words[1:]:
            # Keep words of length <= 3 lowercase (APA rule for short words)
            if word.lower() in ("a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by"):
                result.append(word.lower())
            else:
                result.append(word.capitalize())
        return " ".join(result)
