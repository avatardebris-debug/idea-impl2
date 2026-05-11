"""Unit tests for AudioScriptFormatter."""

import pytest

from audiobook_script_pipeline.formatter.audio_formatter import AudioScriptFormatter


@pytest.fixture
def formatter():
    return AudioScriptFormatter(default_pause=1.5)


@pytest.fixture
def sample_chapters():
    return [
        {
            "title": "Chapter One",
            "body": "Hello world. This is a test.",
            "sentences": ["Hello world.", "This is a test."],
        },
        {
            "title": "Chapter Two",
            "body": "Another chapter here.",
            "sentences": ["Another chapter here."],
        },
    ]


# --- format_chapters tests ---

def test_format_chapters_output_structure(formatter, sample_chapters):
    """Test that format_chapters returns the expected dict structure."""
    result = formatter.format_chapters(sample_chapters)
    assert "title" in result
    assert "chapters" in result
    assert result["title"] == "Chapter One"
    assert len(result["chapters"]) == 2
    assert "title" in result["chapters"][0]
    assert "entries" in result["chapters"][0]


def test_format_chapters_empty_list_raises_valueerror(formatter):
    """Test that format_chapters raises ValueError for empty chapter list."""
    with pytest.raises(ValueError, match="chapters list is empty"):
        formatter.format_chapters([])


def test_format_chapters_pacing_markers(formatter, sample_chapters):
    """Test that pacing markers are correctly placed in the output."""
    result = formatter.format_chapters(sample_chapters)
    chapter_entries = result["chapters"][0]["entries"]

    # First entry should be [SLOW] with the chapter title
    assert "[SLOW]" in chapter_entries[0]["text"]
    assert chapter_entries[0]["markers"] == ["SLOW"]

    # Last entry should be [FAST]
    assert "[FAST]" in chapter_entries[-1]["text"]
    assert chapter_entries[-1]["markers"] == ["FAST"]

    # There should be [PAUSE] markers between sentences
    pause_entries = [e for e in chapter_entries if "[PAUSE" in e["text"]]
    assert len(pause_entries) >= 1


def test_format_chapters_default_pause_propagation(formatter, sample_chapters):
    """Test that the default_pause value is reflected in PAUSE markers."""
    result = formatter.format_chapters(sample_chapters)
    pause_entries = [e for e in result["chapters"][0]["entries"] if "[PAUSE" in e["text"]]
    assert len(pause_entries) > 0
    assert "[PAUSE: 1.5s]" in pause_entries[0]["text"]


# --- _add_emphasis tests ---

def test_add_emphasis_all_caps_words(formatter):
    """Test that ALL CAPS words get [EMPHASIS] markers."""
    text = "This is a GREAT day with some AMAZING news."
    result = formatter._add_emphasis(text)
    assert "[EMPHASIS]GREAT[/EMPHASIS]" in result
    assert "[EMPHASIS]AMAZING[/EMPHASIS]" in result


def test_add_emphasis_all_caps_skip_known_acronyms(formatter):
    """Test that known acronyms are not wrapped in emphasis."""
    text = "The API uses JSON format over HTTP."
    result = formatter._add_emphasis(text)
    # Known acronyms should NOT be wrapped
    assert "[EMPHASIS]API[/EMPHASIS]" not in result
    assert "[EMPHASIS]JSON[/EMPHASIS]" not in result
    assert "[EMPHASIS]HTTP[/EMPHASIS]" not in result


def test_add_emphasis_proper_nouns(formatter):
    """Test that proper nouns (first word of sentence) get emphasis."""
    text = "Sarah walked to the store. John stayed home."
    result = formatter._add_emphasis(text)
    # Sarah and John should be emphasized (proper nouns at sentence start)
    assert "[EMPHASIS]Sarah[/EMPHASIS]" in result
    assert "[EMPHASIS]John[/EMPHASIS]" in result


def test_add_emphasis_already_wrapped_text(formatter):
    """Test that text already containing [EMPHASIS] is returned unchanged."""
    text = "This has [EMPHASIS]existing[/EMPHASIS] markers."
    result = formatter._add_emphasis(text)
    assert result == text


def test_add_emphasis_common_words_not_emphasized(formatter):
    """Test that common words at sentence start are not emphasized."""
    text = "The cat sat on the mat. It was a good day."
    result = formatter._add_emphasis(text)
    # "The" and "It" are in the stop_words list
    assert "[EMPHASIS]The[/EMPHASIS]" not in result
    assert "[EMPHASIS]It[/EMPHASIS]" not in result


# --- format_to_string tests ---

def test_format_to_string_output(formatter, sample_chapters):
    """Test that format_to_string produces readable output."""
    audio_script = formatter.format_chapters(sample_chapters)
    output = formatter.format_to_string(audio_script)
    assert "=== Chapter One ===" in output
    assert "--- Chapter One ---" in output
    assert "--- Chapter Two ---" in output
    assert "[SLOW]" in output
    assert "[FAST]" in output


def test_format_to_string_contains_pacing_markers(formatter, sample_chapters):
    """Test that format_to_string output contains visible pacing markers."""
    audio_script = formatter.format_chapters(sample_chapters)
    output = formatter.format_to_string(audio_script)
    assert "[PAUSE:" in output
    assert "[EMPHASIS]" in output or "[SLOW]" in output
    assert "[FAST]" in output
