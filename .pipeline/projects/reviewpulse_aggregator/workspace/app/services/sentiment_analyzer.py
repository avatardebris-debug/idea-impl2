"""Sentiment analysis service for review text.

Provides sentiment scoring and labeling for review text using either
a local model or an external API.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment of review text."""

    def analyze(self, text: Optional[str]) -> tuple[Optional[float], Optional[str]]:
        """Analyze sentiment of the given text.

        Args:
            text: Review text to analyze.

        Returns:
            Tuple of (sentiment_score, sentiment_label).
            - sentiment_score: Float between -1.0 (negative) and 1.0 (positive).
            - sentiment_label: One of 'positive', 'neutral', 'negative'.
        """
        if not text:
            return None, None

        # Simple keyword-based sentiment for now
        # In production, this would use a proper NLP model
        text_lower = text.lower()

        positive_words = {
            "great", "excellent", "amazing", "wonderful", "fantastic",
            "love", "best", "perfect", "outstanding", "superb",
            "happy", "pleased", "satisfied", "recommend", "good",
        }

        negative_words = {
            "terrible", "awful", "horrible", "worst", "hate",
            "bad", "poor", "disappointing", "disappointed", "waste",
            "angry", "frustrated", "unhappy", "never", "avoid",
        }

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.0, "neutral"

        score = (pos_count - neg_count) / total
        score = max(-1.0, min(1.0, score))

        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return round(score, 3), label

    def analyze_batch(self, texts: list[Optional[str]]) -> list[tuple[Optional[float], Optional[str]]]:
        """Analyze sentiment for a batch of texts.

        Args:
            texts: List of review texts to analyze.

        Returns:
            List of (sentiment_score, sentiment_label) tuples.
        """
        return [self.analyze(text) for text in texts]
