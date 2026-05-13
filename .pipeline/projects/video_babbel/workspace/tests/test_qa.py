"""Tests for the QAEngine class."""

import pytest

from video_babbel.core import QAError
from video_babbel.qa import QAEngine


class TestQAEngine:
    """Tests for the QAEngine class."""

    def test_init(self):
        """QAEngine should be initialized with segments."""
        segments = [{"text": "Hello world", "start": 0.0, "end": 1.0}]
        qa_engine = QAEngine(segments)
        assert len(qa_engine.segments) == 1

    def test_answer_empty_question(self):
        """answer should return empty string for empty question."""
        segments = [{"text": "Hello world", "start": 0.0, "end": 1.0}]
        qa_engine = QAEngine(segments)
        assert qa_engine.answer("") == ""

    def test_answer_whitespace_question(self):
        """answer should return empty string for whitespace-only question."""
        segments = [{"text": "Hello world", "start": 0.0, "end": 1.0}]
        qa_engine = QAEngine(segments)
        assert qa_engine.answer("   ") == ""

    def test_answer_question_with_keyword_match(self):
        """answer should return text containing the keyword."""
        segments = [
            {"text": "The main topic is AI.", "start": 0.0, "end": 1.0},
            {"text": "AI is important.", "start": 1.0, "end": 2.0},
        ]
        qa_engine = QAEngine(segments)
        result = qa_engine.answer("What is the main topic?")
        assert "AI" in result

    def test_answer_question_with_no_match(self):
        """answer should return empty string if no keyword match."""
        segments = [{"text": "Hello world", "start": 0.0, "end": 1.0}]
        qa_engine = QAEngine(segments)
        result = qa_engine.answer("What is the main topic?")
        assert result == ""

    def test_answer_question_with_multiple_matches(self):
        """answer should return the first matching segment."""
        segments = [
            {"text": "First topic is AI.", "start": 0.0, "end": 1.0},
            {"text": "Second topic is ML.", "start": 1.0, "end": 2.0},
        ]
        qa_engine = QAEngine(segments)
        result = qa_engine.answer("What is the main topic?")
        assert "AI" in result

    def test_answer_question_with_empty_segments(self):
        """answer should return empty string for empty segments."""
        qa_engine = QAEngine([])
        assert qa_engine.answer("What is the main topic?") == ""

    def test_answer_question_with_none_text_segments(self):
        """answer should handle segments with None text."""
        segments = [
            {"text": None, "start": 0.0, "end": 1.0},
            {"text": "Hello world", "start": 1.0, "end": 2.0},
        ]
        qa_engine = QAEngine(segments)
        result = qa_engine.answer("What is the main topic?")
        assert result == ""

    def test_answer_question_with_special_characters(self):
        """answer should handle special characters in question."""
        segments = [
            {"text": "The main topic is AI.", "start": 0.0, "end": 1.0},
        ]
        qa_engine = QAEngine(segments)
        result = qa_engine.answer("What is the main topic?")
        assert "AI" in result

    def test_answer_question_with_unicode(self):
        """answer should handle unicode in question."""
        segments = [
            {"text": "こんにちは世界", "start": 0.0, "end": 1.0},
        ]
        qa_engine = QAEngine(segments)
        result = qa_engine.answer("What is the main topic?")
        assert "こんにちは" in result

    def test_answer_question_with_long_text(self):
        """answer should handle long text segments."""
        long_text = "A" * 10000
        segments = [
            {"text": long_text, "start": 0.0, "end": 1.0},
        ]
        qa_engine = QAEngine(segments)
        result = qa_engine.answer("What is the main topic?")
        assert result == ""

    def test_answer_question_with_exception_wrapped(self):
        """QAError should wrap underlying exceptions."""
        qa_engine = QAEngine(None)  # type: ignore
        with pytest.raises(QAError, match="Q&A failed"):
            qa_engine.answer("What is the main topic?")
