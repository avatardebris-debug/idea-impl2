"""Tests for video_ingestor.summarizer."""

import pytest
from unittest.mock import patch, MagicMock

from video_ingestor.summarizer import Summarizer, SummarizationError


class TestSummarizer:
    def test_summarize_with_mocked_harness(self):
        """Test summarization with mocked LLM harness."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "This is a summary",
            "key_points": ["Point 1", "Point 2"],
            "action_items": ["Action 1"],
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [
            {"text": "Hello world", "start": 0.0, "end": 5.0},
            {"text": "Goodbye world", "start": 5.0, "end": 10.0},
        ]
        result = summarizer.summarize("Hello world Goodbye world", segments)

        assert result["summary_text"] == "This is a summary"
        assert result["key_points"] == ["Point 1", "Point 2"]
        assert result["action_items"] == ["Action 1"]
        mock_harness.generate_json.assert_called_once()

    def test_summarize_with_custom_length(self):
        """Test summarization with custom length parameter."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Short summary",
            "key_points": [],
            "action_items": [],
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": "Test", "start": 0.0, "end": 1.0}]
        result = summarizer.summarize("Test", segments, length="short")

        assert result["summary_text"] == "Short summary"

    def test_summarize_with_custom_tone(self):
        """Test summarization with custom tone parameter."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Formal summary",
            "key_points": [],
            "action_items": [],
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": "Test", "start": 0.0, "end": 1.0}]
        result = summarizer.summarize("Test", segments, tone="formal")

        assert result["summary_text"] == "Formal summary"

    def test_summarize_with_custom_format(self):
        """Test summarization with custom format parameter."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Bullet summary",
            "key_points": [],
            "action_items": [],
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": "Test", "start": 0.0, "end": 1.0}]
        result = summarizer.summarize("Test", segments, format_type="bullet")

        assert result["summary_text"] == "Bullet summary"

    def test_summarize_handles_exception(self):
        """Test that summarization handles LLM errors gracefully."""
        mock_harness = MagicMock()
        mock_harness.generate_json.side_effect = Exception("LLM error")

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": "Test", "start": 0.0, "end": 1.0}]

        with pytest.raises(SummarizationError, match="Summarization failed"):
            summarizer.summarize("Test", segments)

    def test_summarize_with_empty_segments(self):
        """Test summarization with empty segments list."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Empty summary",
            "key_points": [],
            "action_items": [],
        }

        summarizer = Summarizer(harness=mock_harness)
        result = summarizer.summarize("", [])

        assert result["summary_text"] == "Empty summary"

    def test_summarize_with_many_segments(self):
        """Test summarization with many segments (should limit to 50)."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Summary of many segments",
            "key_points": [],
            "action_items": [],
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": f"Segment {i}", "start": float(i), "end": float(i) + 1.0}
                    for i in range(100)]
        result = summarizer.summarize(" ".join(f"Segment {i}" for i in range(100)), segments)

        assert result["summary_text"] == "Summary of many segments"
        # Verify that only last 50 segments were used
        call_args = mock_harness.generate_json.call_args[0][0]
        assert "Segment 50" in call_args
        assert "Segment 99" in call_args

    def test_summarize_from_text(self):
        """Test summarization from full text only."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Text summary",
            "key_points": ["Key point 1"],
            "action_items": ["Action 1"],
        }

        summarizer = Summarizer(harness=mock_harness)
        result = summarizer.summarize_from_text("This is the full text")

        assert result["summary_text"] == "Text summary"
        assert result["key_points"] == ["Key point 1"]
        assert result["action_items"] == ["Action 1"]

    def test_summarize_from_text_with_custom_params(self):
        """Test summarization from text with custom parameters."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Custom summary",
            "key_points": [],
            "action_items": [],
        }

        summarizer = Summarizer(harness=mock_harness)
        result = summarizer.summarize_from_text(
            "Full text",
            length="long",
            tone="casual",
            format_type="paragraph"
        )

        assert result["summary_text"] == "Custom summary"

    def test_summarize_from_text_handles_exception(self):
        """Test that summarize_from_text handles errors."""
        mock_harness = MagicMock()
        mock_harness.generate_json.side_effect = Exception("LLM error")

        summarizer = Summarizer(harness=mock_harness)

        with pytest.raises(SummarizationError, match="Summarization failed"):
            summarizer.summarize_from_text("Test text")

    def test_summarize_default_params(self):
        """Test that default parameters are used when not specified."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Default summary",
            "key_points": [],
            "action_items": [],
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": "Test", "start": 0.0, "end": 1.0}]
        result = summarizer.summarize("Test", segments)

        assert result["summary_text"] == "Default summary"
        # Verify that default params were used in the prompt
        call_args = mock_harness.generate_json.call_args[0][0]
        assert "medium" in call_args  # Default length
        assert "neutral" in call_args  # Default tone

    def test_summarize_with_missing_keys_in_response(self):
        """Test that summarization handles missing keys in LLM response."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": "Summary only",
            # Missing key_points and action_items
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": "Test", "start": 0.0, "end": 1.0}]
        result = summarizer.summarize("Test", segments)

        assert result["summary_text"] == "Summary only"
        assert result["key_points"] == []
        assert result["action_items"] == []

    def test_summarize_with_none_values_in_response(self):
        """Test that summarization handles None values in LLM response."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "summary_text": None,
            "key_points": None,
            "action_items": None,
        }

        summarizer = Summarizer(harness=mock_harness)
        segments = [{"text": "Test", "start": 0.0, "end": 1.0}]
        result = summarizer.summarize("Test", segments)

        assert result["summary_text"] == ""
        assert result["key_points"] == []
        assert result["action_items"] == []
