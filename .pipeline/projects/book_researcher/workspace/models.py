"""Core data models for book researcher."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Gap:
    """A content gap identified in existing material."""
    text: str
    topic: str
    source: str
    helpful_votes: int = 0
    confidence: float = 0.5


@dataclass
class NicheProfile:
    """A profile of an underserved niche area."""
    topic: str
    gaps: List[Gap]
    score: float
    description: str


@dataclass
class Section:
    """A section within a chapter."""
    title: str
    content_hint: str
    estimated_pages: int = 5


@dataclass
class Chapter:
    """A chapter in the book."""
    title: str
    niche: Optional[NicheProfile] = None
    sections: List[Section] = field(default_factory=list)


@dataclass
class BookOutline:
    """The complete book outline."""
    title: str
    chapters: List[Chapter]
    target_audience: str
    book_length: str
    niche_count: int
