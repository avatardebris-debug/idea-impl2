"""Unit tests for ScriptPipeline."""

import os
import tempfile
import pytest

from audiobook_script_pipeline.pipeline.script_pipeline import ScriptPipeline
from audiobook_script_pipeline.parser.manuscript_parser import ManuscriptParseError


@pytest.fixture
def pipeline():
    return ScriptPipeline(default_pause=2.0)


@pytest.fixture
def sample_text():
    return "# Chapter One\n\nHello world. This is a test.\n\n# Chapter Two\n\nAnother chapter."


# --- run() tests ---

def test_run_end_to_end(pipeline, sample_text):
    """Test run() end-to-end with a sample manuscript file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(sample_text)
        f.flush()
        tmp_path = f.name
    try:
        result = pipeline.run(tmp_path)
        assert "title" in result
        assert "chapters" in result
        assert len(result["chapters"]) == 2
        assert result["chapters"][0]["title"] == "Chapter One"
        assert result["chapters"][1]["title"] == "Chapter Two"
    finally:
        os.unlink(tmp_path)


def test_run_nonexistent_file(pipeline):
    """Test run() raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError, match="Manuscript file not found"):
        pipeline.run("/nonexistent/file.txt")


def test_run_empty_file(pipeline):
    """Test run() raises ManuscriptParseError for empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("")
        f.flush()
        tmp_path = f.name
    try:
        with pytest.raises(ManuscriptParseError, match="Manuscript file is empty"):
            pipeline.run(tmp_path)
    finally:
        os.unlink(tmp_path)


# --- run_from_text() tests ---

def test_run_from_text(pipeline, sample_text):
    """Test run_from_text() works with raw text."""
    result = pipeline.run_from_text(sample_text)
    assert "title" in result
    assert "chapters" in result
    assert len(result["chapters"]) == 2
    assert result["chapters"][0]["title"] == "Chapter One"


def test_run_from_text_empty_input(pipeline):
    """Test run_from_text() raises ValueError for empty input."""
    with pytest.raises(ValueError, match="input text is empty"):
        pipeline.run_from_text("")


def test_run_from_text_whitespace_only_input(pipeline):
    """Test run_from_text() raises ValueError for whitespace-only input."""
    with pytest.raises(ValueError, match="input text is empty"):
        pipeline.run_from_text("   \n\n  ")


# --- default_pause parameter propagation ---

def test_default_pause_propagation(pipeline):
    """Test that default_pause is correctly propagated to the formatter."""
    assert pipeline.formatter.default_pause == 2.0


def test_custom_pause_propagation():
    """Test that a custom pause value is correctly propagated."""
    pipeline = ScriptPipeline(default_pause=0.5)
    assert pipeline.formatter.default_pause == 0.5

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("# Chapter One\n\nHello world.")
        f.flush()
        tmp_path = f.name
    try:
        result = pipeline.run(tmp_path)
        # Check that the pause marker reflects the custom value
        pause_entries = []
        for chapter in result["chapters"]:
            for entry in chapter["entries"]:
                if "[PAUSE" in entry["text"]:
                    pause_entries.append(entry["text"])
        assert len(pause_entries) > 0
        assert "[PAUSE: 0.5s]" in pause_entries[0]
    finally:
        os.unlink(tmp_path)


# --- empty input handling ---

def test_run_from_text_no_chapters_detected(pipeline):
    """Test run_from_text with text that has no chapter headings (falls back to Untitled)."""
    text = "Just some plain text with no chapters."
    result = pipeline.run_from_text(text)
    assert len(result["chapters"]) == 1
    assert result["chapters"][0]["title"] == "Untitled"


def test_run_from_text_with_emphasis(pipeline):
    """Test that emphasis markers are preserved through the pipeline."""
    text = "# Chapter One\n\nThis is a GREAT discovery with some AMAZING details."
    result = pipeline.run_from_text(text)
    output_text = pipeline.formatter.format_to_string(result)
    assert "[EMPHASIS]GREAT[/EMPHASIS]" in output_text
    assert "[EMPHASIS]AMAZING[/EMPHASIS]" in output_text
