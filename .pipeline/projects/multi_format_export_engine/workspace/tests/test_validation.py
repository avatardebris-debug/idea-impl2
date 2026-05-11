"""Tests for the validation module."""

import pytest

from multi_format_export_engine.models import Manuscript
from multi_format_export_engine.validation import validate_manuscript, validate_export_options


class TestValidateManuscript:
    """Tests for validate_manuscript."""

    def test_valid_manuscript(self):
        """Test that a valid manuscript passes validation."""
        m = Manuscript(title="Valid Book", author="Author")
        m.add_chapter_title("Ch1").add_paragraph("Text")
        assert validate_manuscript(m) is True

    def test_empty_title_raises(self):
        """Test that an empty title raises ValueError."""
        m = Manuscript(title="", author="Author")
        m.add_chapter_title("Ch1").add_paragraph("Text")
        with pytest.raises(ValueError, match="title"):
            validate_manuscript(m)

    def test_no_chapters_raises(self):
        """Test that no chapters raises ValueError."""
        m = Manuscript(title="No Chapters")
        with pytest.raises(ValueError, match="chapter"):
            validate_manuscript(m)

    def test_chapter_without_content_attr_raises(self):
        """Test that a chapter without content attribute raises ValueError."""
        m = Manuscript(title="Bad Ch")
        # Create a chapter-like object without content attribute
        class FakeChapter:
            title = "Fake"
        m.chapters = [FakeChapter()]
        with pytest.raises(ValueError, match="content"):
            validate_manuscript(m)

    def test_invalid_chapter_type_raises(self):
        """Test that an invalid chapter type raises ValueError."""
        m = Manuscript(title="Bad Ch")
        m.add_chapter_title("Ch1").add_paragraph("Text")
        m.chapters.append("not a chapter")
        # The first invalid chapter (index 1) lacks 'content' attribute
        with pytest.raises(ValueError, match="content"):
            validate_manuscript(m)

    def test_invalid_content_item_raises(self):
        """Test that an invalid content item raises ValueError."""
        m = Manuscript(title="Bad Item")
        ch = m.add_chapter_title("Ch1")
        ch.add_paragraph("Text")
        ch.content.append("not a content item")
        with pytest.raises(ValueError, match="text"):
            validate_manuscript(m)


class TestValidateExportOptions:
    """Tests for validate_export_options."""

    def test_valid_options(self):
        """Test that valid options pass validation."""
        options = {
            "page_size": "A4",
            "font_family": "serif",
            "line_height": 1.5,
            "font_size": 12,
            "margins": {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"}
        }
        assert validate_export_options(options) is True

    def test_none_options_raises(self):
        """Test that None options raises ValueError."""
        with pytest.raises(ValueError, match="options"):
            validate_export_options(None)

    def test_invalid_page_size_raises(self):
        """Test that invalid page_size raises ValueError."""
        options = {"page_size": "Invalid"}
        with pytest.raises(ValueError, match="page_size"):
            validate_export_options(options)

    def test_invalid_font_family_raises(self):
        """Test that invalid font_family raises ValueError."""
        options = {"font_family": 123}
        with pytest.raises(ValueError, match="font_family"):
            validate_export_options(options)

    def test_invalid_line_height_raises(self):
        """Test that invalid line_height raises ValueError."""
        options = {"line_height": -1}
        with pytest.raises(ValueError, match="line_height"):
            validate_export_options(options)

    def test_invalid_font_size_raises(self):
        """Test that invalid font_size raises ValueError."""
        options = {"font_size": -1}
        with pytest.raises(ValueError, match="font_size"):
            validate_export_options(options)

    def test_invalid_margin_key_raises(self):
        """Test that invalid margin key raises ValueError."""
        options = {"margins": {"top": "1in", "invalid": "1in"}}
        with pytest.raises(ValueError, match="margin"):
            validate_export_options(options)

    def test_invalid_margin_value_raises(self):
        """Test that invalid margin value raises ValueError."""
        options = {"margins": {"top": "1"}}
        with pytest.raises(ValueError, match="unit"):
            validate_export_options(options)
