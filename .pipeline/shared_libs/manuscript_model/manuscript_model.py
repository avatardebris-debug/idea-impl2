"""Reusable manuscript data model.

Extracted from multi_format_export_engine.
Provides Manuscript, Chapter, Heading, and Paragraph dataclasses.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Paragraph:
    """A single paragraph of text content."""
    text: str
    style: str = "normal"  # normal, bold, italic, etc.


@dataclass
class Heading:
    """A heading within a chapter."""
    text: str
    level: int = 1  # h1 through h6


@dataclass
class Chapter:
    """A chapter containing headings and paragraphs."""
    title: str
    content: List[Heading | Paragraph] = field(default_factory=list)

    def add_heading(self, text: str, level: int = 1) -> None:
        self.content.append(Heading(text=text, level=level))

    def add_paragraph(self, text: str, style: str = "normal") -> None:
        self.content.append(Paragraph(text=text, style=style))


@dataclass
class Manuscript:
    """A complete manuscript composed of chapters."""
    title: str
    author: str = ""
    chapters: List[Chapter] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_chapter(self, chapter: Chapter) -> None:
        self.chapters.append(chapter)

    def add_chapter_title(self, title: str) -> Chapter:
        chapter = Chapter(title=title)
        self.add_chapter(chapter)
        return chapter
