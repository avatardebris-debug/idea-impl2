"""Tests for the sentiment analyzer service."""

import sys
import pathlib

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from app.services.sentiment_analyzer import analyze_sentiment


class TestSentimentAnalyzer:
    """Tests for the analyze_sentiment function."""

    def test_positive_sentiment(self):
        result = analyze_sentiment("This is absolutely wonderful! I love it!")
        assert result["label"] == "positive"
        assert result["compound"] > 0

    def test_negative_sentiment(self):
        result = analyze_sentiment("This is terrible. I hate it.")
        assert result["label"] == "negative"
        assert result["compound"] < 0

    def test_neutral_sentiment(self):
        result = analyze_sentiment("The item is as described.")
        assert result["label"] == "neutral"
        assert -0.05 < result["compound"] < 0.05

    def test_empty_text(self):
        result = analyze_sentiment("")
        assert result["label"] == "neutral"
        assert result["compound"] == 0.0

    def test_mixed_sentiment(self):
        result = analyze_sentiment("The food was great but the service was slow.")
        # Should be closer to neutral or slightly positive/negative depending on weights
        assert "compound" in result
        assert "label" in result

    def test_very_positive(self):
        result = analyze_sentiment("Best place ever! 5 stars! Amazing! Incredible!")
        assert result["label"] == "positive"
        assert result["compound"] > 0.5

    def test_very_negative(self):
        result = analyze_sentiment("Worst place ever! 1 star! Terrible! Horrible!")
        assert result["label"] == "negative"
        assert result["compound"] < -0.5
