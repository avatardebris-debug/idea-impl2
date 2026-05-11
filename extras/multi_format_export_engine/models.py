"""Core data models: Paragraph, Heading, Chapter, and Manuscript."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Paragraph:
    """A paragraph of text with an optional style."""
    text: str
    style: str = "normal"


@dataclass
class Heading:
    """A heading with a level (1-6) and text."""
    text: str
    level: int = 1


@dataclass
class Chapter:
    """A chapter containing headings and paragraphs."""
    title: str
    content: List[Any] = field(default_factory=list)

    def add_heading(self, text: str, level: int = 1) -> Heading:
        """Add a heading to this chapter."""
        h = Heading(text=text, level=level)
        self.content.append(h)
        return h

    def add_paragraph(self, text: str, style: str = "normal") -> Paragraph:
        """Add a paragraph to this chapter."""
        p = Paragraph(text=text, style=style)
        self.content.append(p)
        return p


@dataclass
class Manuscript:
    """A complete manuscript with title, author, chapters, and metadata."""
    title: str
    author: str = ""
    chapters: List[Chapter] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the manuscript."""
        self.chapters.append(chapter)

    def add_chapter_title(self, title: str) -> Chapter:
        """Create and add a new chapter, returning it."""
        ch = Chapter(title=title)
        self.chapters.append(ch)
        return ch
