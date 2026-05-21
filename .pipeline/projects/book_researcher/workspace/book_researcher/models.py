"""Core data models for the book researcher."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BookReview:
    """A single review of a book."""
    book_id: str
    text: str
    rating: float
    source: str  # e.g. "amazon", "goodreads"
    reviewer: str = ""
    helpful_votes: int = 0


@dataclass
class Gap:
    """A content gap identified from a review."""
    text: str
    source_review: str
    topic: str
    confidence: float = 0.0


@dataclass
class NicheProfile:
    """Profile of an underserved niche derived from grouped gaps."""
    top_gap_topics: List[str]
    gap_count: int
    recommended_focus: str
    gap_details: List[Gap] = field(default_factory=list)


@dataclass
class Chapter:
    """A single chapter in the table of contents."""
    title: str
    subtopics: List[str] = field(default_factory=list)


# Alias for compatibility
TOCChapter = Chapter


@dataclass
class TableOfContents:
    """A structured table of contents for a new book."""
    title: str
    chapters: List[Chapter]
    niche_focus: str = ""
