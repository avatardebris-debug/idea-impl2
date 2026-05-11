"""Unit tests for ManuscriptParser."""

import os
import tempfile
import pytest

from audiobook_script_pipeline.parser.manuscript_parser import ManuscriptParser, ManuscriptParseError


@pytest.fixture
def parser():
    return ManuscriptParser()


# --- Happy path tests ---

def test_parse_with_hash_headings(parser):
    """Test parsing with '# ' Markdown-style headings."""
    text = "# Chapter One\n\nSome text here.\n\n# Chapter Two\n\nMore text."
    chapters = parser.parse(text)
    assert len(chapters) == 2
    assert chapters[0]["title"] == "Chapter One"
    assert "Some text here." in chapters[0]["body"]
    assert chapters[1]["title"] == "Chapter Two"
    assert "More text." in chapters[1]["body"]


def test_parse_with_chapter_headings(parser):
    """Test parsing with 'Chapter N' headings."""
    text = "Chapter 1: The Beginning\n\nSome text here.\n\nChapter 2: The Journey\n\nMore text."
    chapters = parser.parse(text)
    assert len(chapters) == 2
    assert chapters[0]["title"] == "Chapter 1: The Beginning"
    assert "Some text here." in chapters[0]["body"]
    assert chapters[1]["title"] == "Chapter 2: The Journey"
    assert "More text." in chapters[1]["body"]


def test_parse_with_mixed_headings(parser):
    """Test parsing with mixed heading styles (# and Chapter N)."""
    text = "# Introduction\n\nIntro text.\n\nChapter 2: Middle\n\nMiddle text.\n\n# Conclusion\n\nEnd text."
    chapters = parser.parse(text)
    assert len(chapters) == 3
    assert chapters[0]["title"] == "Introduction"
    assert chapters[1]["title"] == "Chapter 2: Middle"
    assert chapters[2]["title"] == "Conclusion"


def test_parse_no_headings_falls_back_to_untitled(parser):
    """Test that text with no chapter headings falls back to a single 'Untitled' chapter."""
    text = "This is a book with no chapters. It has multiple sentences. And more text."
    chapters = parser.parse(text)
    assert len(chapters) == 1
    assert chapters[0]["title"] == "Untitled"
    assert "This is a book with no chapters." in chapters[0]["body"]


# --- Edge case tests ---

def test_parse_empty_text(parser):
    """Test parsing empty text returns a single Untitled chapter."""
    text = ""
    chapters = parser.parse(text)
    assert len(chapters) == 1
    assert chapters[0]["title"] == "Untitled"


def test_parse_blank_lines_between_paragraphs(parser):
    """Test that blank lines between paragraphs are handled correctly."""
    text = "# Chapter One\n\nFirst paragraph.\n\n\nSecond paragraph.\n\n# Chapter Two\n\nThird paragraph."
    chapters = parser.parse(text)
    assert len(chapters) == 2
    assert "First paragraph." in chapters[0]["body"]
    assert "Second paragraph." in chapters[0]["body"]
    assert "Third paragraph." in chapters[1]["body"]


def test_parse_file_with_real_file(parser):
    """Test parse_file with a real file path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("# Test Chapter\n\nThis is test content.\n")
        f.flush()
        tmp_path = f.name
    try:
        chapters = parser.parse_file(tmp_path)
        assert len(chapters) == 1
        assert chapters[0]["title"] == "Test Chapter"
        assert "This is test content." in chapters[0]["body"]
    finally:
        os.unlink(tmp_path)


def test_parse_file_nonexistent_file(parser):
    """Test parse_file raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError, match="Manuscript file not found"):
        parser.parse_file("/nonexistent/path/to/manuscript.txt")


def test_parse_file_empty_file(parser):
    """Test parse_file raises ManuscriptParseError for empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("")
        f.flush()
        tmp_path = f.name
    try:
        with pytest.raises(ManuscriptParseError, match="Manuscript file is empty"):
            parser.parse_file(tmp_path)
    finally:
        os.unlink(tmp_path)


def test_parse_file_blank_file(parser):
    """Test parse_file raises ManuscriptParseError for file with only whitespace."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("   \n\n  \n")
        f.flush()
        tmp_path = f.name
    try:
        with pytest.raises(ManuscriptParseError, match="Manuscript file is empty"):
            parser.parse_file(tmp_path)
    finally:
        os.unlink(tmp_path)


def test_parse_chapter_without_subtitle(parser):
    """Test 'Chapter N' without a subtitle."""
    text = "Chapter 5\n\nJust the chapter number, no subtitle."
    chapters = parser.parse(text)
    assert len(chapters) == 1
    assert chapters[0]["title"] == "Chapter 5"


def test_parse_sentences_in_chapters(parser):
    """Test that sentences are correctly extracted."""
    text = "# Chapter One\n\nHello world. How are you? I am fine!"
    chapters = parser.parse(text)
    assert len(chapters[0]["sentences"]) >= 3
    assert "Hello world." in chapters[0]["sentences"]
    assert "How are you?" in chapters[0]["sentences"]
    assert "I am fine!" in chapters[0]["sentences"]
