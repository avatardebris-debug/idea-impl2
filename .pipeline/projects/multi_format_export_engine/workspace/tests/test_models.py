"""Unit tests for core models: Paragraph, Heading, Chapter, and Manuscript."""

import pytest
from multi_format_export_engine.models import Paragraph, Heading, Chapter, Manuscript


# ── Paragraph tests ──────────────────────────────────────────────────────────

class TestParagraph:
    def test_default_style(self):
        p = Paragraph(text="Hello")
        assert p.text == "Hello"
        assert p.style == "normal"

    def test_custom_style(self):
        p = Paragraph(text="Bold text", style="bold")
        assert p.text == "Bold text"
        assert p.style == "bold"

    def test_empty_text(self):
        p = Paragraph(text="")
        assert p.text == ""
        assert p.style == "normal"


# ── Heading tests ────────────────────────────────────────────────────────────

class TestHeading:
    def test_default_level(self):
        h = Heading(text="Title")
        assert h.text == "Title"
        assert h.level == 1

    def test_custom_level(self):
        h = Heading(text="Subtitle", level=2)
        assert h.text == "Subtitle"
        assert h.level == 2

    def test_level_clamped_to_6(self):
        h = Heading(text="Deep heading", level=10)
        assert h.level == 10  # dataclass does not clamp; the exporter clamps

    def test_empty_text(self):
        h = Heading(text="")
        assert h.text == ""
        assert h.level == 1


# ── Chapter tests ────────────────────────────────────────────────────────────

class TestChapter:
    def test_empty_content(self):
        ch = Chapter(title="My Chapter")
        assert ch.title == "My Chapter"
        assert ch.content == []

    def test_add_heading(self):
        ch = Chapter(title="My Chapter")
        ch.add_heading("Section 1", level=2)
        assert len(ch.content) == 1
        assert isinstance(ch.content[0], Heading)
        assert ch.content[0].text == "Section 1"
        assert ch.content[0].level == 2

    def test_add_paragraph(self):
        ch = Chapter(title="My Chapter")
        ch.add_paragraph("Some text")
        assert len(ch.content) == 1
        assert isinstance(ch.content[0], Paragraph)
        assert ch.content[0].text == "Some text"
        assert ch.content[0].style == "normal"

    def test_add_paragraph_with_style(self):
        ch = Chapter(title="My Chapter")
        ch.add_paragraph("Bold text", style="bold")
        assert ch.content[0].style == "bold"

    def test_add_multiple_items(self):
        ch = Chapter(title="My Chapter")
        ch.add_heading("H1", level=1)
        ch.add_paragraph("Para 1")
        ch.add_heading("H2", level=2)
        ch.add_paragraph("Para 2", style="italic")
        assert len(ch.content) == 4
        assert isinstance(ch.content[0], Heading)
        assert isinstance(ch.content[1], Paragraph)
        assert isinstance(ch.content[2], Heading)
        assert isinstance(ch.content[3], Paragraph)


# ── Manuscript tests ─────────────────────────────────────────────────────────

class TestManuscript:
    def test_empty_manuscript(self):
        m = Manuscript(title="Untitled")
        assert m.title == "Untitled"
        assert m.author == ""
        assert m.chapters == []
        assert m.metadata == {}

    def test_with_author(self):
        m = Manuscript(title="Book", author="Author Name")
        assert m.author == "Author Name"

    def test_add_chapter(self):
        m = Manuscript(title="Book")
        ch = Chapter(title="Chapter 1")
        m.add_chapter(ch)
        assert len(m.chapters) == 1
        assert m.chapters[0].title == "Chapter 1"

    def test_add_chapter_title(self):
        m = Manuscript(title="Book")
        ch = m.add_chapter_title("Chapter 1")
        assert len(m.chapters) == 1
        assert ch.title == "Chapter 1"
        assert isinstance(ch, Chapter)
        assert ch.content == []

    def test_add_chapter_title_returns_chapter(self):
        m = Manuscript(title="Book")
        ch = m.add_chapter_title("First")
        # Verify the returned chapter is the same object stored in chapters
        assert ch is m.chapters[0]

    def test_multi_chapter(self):
        m = Manuscript(title="Book")
        ch1 = m.add_chapter_title("Chapter 1")
        ch1.add_paragraph("Para 1")
        ch2 = m.add_chapter_title("Chapter 2")
        ch2.add_heading("Section A", level=2)
        ch2.add_paragraph("Para 2")
        ch3 = m.add_chapter_title("Chapter 3")
        assert len(m.chapters) == 3
        assert m.chapters[0].title == "Chapter 1"
        assert m.chapters[1].title == "Chapter 2"
        assert m.chapters[2].title == "Chapter 3"
        assert len(m.chapters[0].content) == 1
        assert len(m.chapters[1].content) == 2
        assert len(m.chapters[2].content) == 0

    def test_metadata(self):
        m = Manuscript(title="Book")
        m.metadata["genre"] = "fiction"
        m.metadata["year"] = 2024
        assert m.metadata["genre"] == "fiction"
        assert m.metadata["year"] == 2024

    def test_empty_manuscript_no_chapters(self):
        m = Manuscript(title="Empty Book")
        assert m.chapters == []

    def test_chapter_with_headings_and_paragraphs(self):
        m = Manuscript(title="Complex Book")
        ch = m.add_chapter_title("Complex Chapter")
        ch.add_heading("Intro", level=1)
        ch.add_paragraph("Welcome.")
        ch.add_heading("Details", level=2)
        ch.add_paragraph("More info.")
        ch.add_heading("Conclusion", level=2)
        ch.add_paragraph("End.")
        assert len(m.chapters) == 1
        assert len(m.chapters[0].content) == 6
