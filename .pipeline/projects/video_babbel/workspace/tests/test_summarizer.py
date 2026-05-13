"""Tests for the Summarizer class."""

import pytest

from video_babbel.core import SummarizationError
from video_babbel.summarizer import Summarizer


class TestSummarizer:
    """Tests for the Summarizer class."""

    def test_init_default_max_sentences(self):
        """Default max_sentences should be 5."""
        summarizer = Summarizer()
        assert summarizer.max_sentences == 5

    def test_init_custom_max_sentences(self):
        """Custom max_sentences should be set correctly."""
        summarizer = Summarizer(max_sentences=10)
        assert summarizer.max_sentences == 10

    def test_summarize_empty_segments(self):
        """summarize should return empty string for empty segments."""
        summarizer = Summarizer()
        result = summarizer.summarize([])
        assert result == ""

    def test_summarize_single_segment(self):
        """summarize should handle single segment."""
        segments = [{"text": "Hello world", "start": 0.0, "end": 1.0}]
        summarizer = Summarizer()
        result = summarizer.summarize(segments)
        assert result == "Hello world"

    def test_summarize_multiple_segments(self):
        """summarize should join multiple segments."""
        segments = [
            {"text": "Hello", "start": 0.0, "end": 1.0},
            {"text": "world", "start": 1.0, "end": 2.0},
        ]
        summarizer = Summarizer()
        result = summarizer.summarize(segments)
        assert result == "Hello world"

    def test_summarize_max_sentences_limit(self):
        """summarize should respect max_sentences limit."""
        segments = [
            {"text": f"Sentence {i}", "start": float(i), "end": float(i + 1)}
            for i in range(10)
        ]
        summarizer = Summarizer(max_sentences=3)
        result = summarizer.summarize(segments)
        sentences = result.split(". ")
        assert len(sentences) <= 3

    def test_summarize_with_empty_text_segments(self):
        """summarize should filter out segments with empty text."""
        segments = [
            {"text": "Hello", "start": 0.0, "end": 1.0},
            {"text": "", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]
        summarizer = Summarizer()
        result = summarizer.summarize(segments)
        assert "Hello" in result
        assert "world" in result

    def test_summarize_with_none_text_segments(self):
        """summarize should handle segments with None text."""
        segments = [
            {"text": "Hello", "start": 0.0, "end": 1.0},
            {"text": None, "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]
        summarizer = Summarizer()
        result = summarizer.summarize(segments)
        assert "Hello" in result
        assert "world" in result

    def test_summarize_exception_wrapped(self):
        """SummarizationError should wrap underlying exceptions."""
        summarizer = Summarizer()
        with pytest.raises(SummarizationError, match="Summarization failed"):
            summarizer.summarize(None)  # type: ignore

    def test_summarize_preserves_order(self):
        """summarize should preserve the order of segments."""
        segments = [
            {"text": "First", "start": 0.0, "end": 1.0},
            {"text": "Second", "start": 1.0, "end": 2.0},
            {"text": "Third", "start": 2.0, "end": 3.0},
        ]
        summarizer = Summarizer()
        result = summarizer.summarize(segments)
        assert result.index("First") < result.index("Second") < result.index("Third")

    def test_summarize_with_special_characters(self):
        """summarize should handle special characters."""
        segments = [
            {"text": "Hello! How are you?", "start": 0.0, "end": 1.0},
            {"text": "I'm fine, thanks.", "start": 1.0, "end": 2.0},
        ]
        summarizer = Summarizer()
        result = summarizer.summarize(segments)
        assert "!" in result
        assert "?" in result
        assert "." in result

    def test_summarize_with_unicode_text(self):
        """summarize should handle unicode text."""
        segments = [
            {"text": "こんにちは", "start": 0.0, "end": 1.0},
            {"text": "世界", "start": 1.0, "end": 2.0},
        ]
        summarizer = Summarizer()
        result = summarizer.summarize(segments)
        assert "こんにちは" in result
        assert "世界" in result
