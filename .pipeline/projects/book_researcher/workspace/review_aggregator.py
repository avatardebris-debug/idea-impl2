"""Review aggregator with sample data for MVP."""

from __future__ import annotations

from typing import List, Optional

from book_researcher.models import Gap


class ReviewAggregator:
    """Aggregates reviews from various sources to identify content gaps.

    For MVP, uses sample data. In production, would connect to:
    - Amazon reviews
    - Goodreads
    - Udemy/Coursera course reviews
    - Quora/Reddit discussions
    """

    def __init__(self, source: str = "sample"):
        self.source = source
        self.gaps: List[Gap] = []

    def fetch_reviews(self, topic: str) -> List[dict]:
        """Fetch reviews for a given topic. Returns sample data for MVP."""
        sample_reviews = self._get_sample_reviews(topic)
        return sample_reviews

    def extract_gaps(self, reviews: List[dict]) -> List[Gap]:
        """Extract content gaps from reviews.

        Looks for phrases like:
        - "I wish it covered..."
        - "This didn't explain..."
        - "Missing section on..."
        - "The author forgot to mention..."
        """
        gaps = []
        gap_indicators = [
            "wish", "wanted", "missing", "didn't", "did not",
            "forgot", "lacked", "lacked", "hope", "expected",
            "should have", "need to know", "confusing", "unclear",
            "not covered", "didn't cover", "didn't explain",
            "didn't mention", "didn't include", "didn't discuss",
        ]

        for review in reviews:
            text = review.get("text", "").lower()
            rating = review.get("rating", 3)

            # Only extract gaps from reviews that express dissatisfaction
            if rating >= 4:
                continue

            for indicator in gap_indicators:
                if indicator in text:
                    # Extract the gap description
                    gap_text = self._extract_gap_text(text, indicator)
                    if gap_text:
                        gap = Gap(
                            text=gap_text,
                            topic=review.get("topic", "general"),
                            source=review.get("source", self.source),
                            helpful_votes=review.get("helpful_votes", 0),
                            confidence=self._calculate_confidence(gap_text, rating),
                        )
                        gaps.append(gap)
                    break  # One gap per review is enough for MVP

        return gaps

    def analyze_topic(self, topic: str) -> List[Gap]:
        """Full pipeline: fetch reviews and extract gaps for a topic."""
        reviews = self.fetch_reviews(topic)
        return self.extract_gaps(reviews)

    def _get_sample_reviews(self, topic: str) -> List[dict]:
        """Return sample reviews for MVP."""
        return [
            {
                "text": "Good overview but I wish it covered advanced techniques in depth. The section on optimization was too basic.",
                "rating": 3,
                "topic": topic,
                "source": "sample_amazon",
                "helpful_votes": 45,
            },
            {
                "text": "This book didn't explain the practical applications well. I expected more real-world examples.",
                "rating": 2,
                "topic": topic,
                "source": "sample_amazon",
                "helpful_votes": 32,
            },
            {
                "text": "Excellent book! Very comprehensive and well-written.",
                "rating": 5,
                "topic": topic,
                "source": "sample_amazon",
                "helpful_votes": 120,
            },
            {
                "text": "Missing section on implementation strategies. The theory is good but practice is lacking.",
                "rating": 3,
                "topic": topic,
                "source": "sample_goodreads",
                "helpful_votes": 28,
            },
            {
                "text": "I wanted more case studies. The author forgot to include recent developments in the field.",
                "rating": 3,
                "topic": topic,
                "source": "sample_goodreads",
                "helpful_votes": 15,
            },
            {
                "text": "The chapter on advanced topics was confusing and unclear. Needs better explanations.",
                "rating": 2,
                "topic": topic,
                "source": "sample_coursera",
                "helpful_votes": 67,
            },
            {
                "text": "Should have covered more about the latest tools and technologies. Outdated information.",
                "rating": 3,
                "topic": topic,
                "source": "sample_udemy",
                "helpful_votes": 89,
            },
            {
                "text": "Not covered the ethical implications which are crucial for this field.",
                "rating": 4,
                "topic": topic,
                "source": "sample_reddit",
                "helpful_votes": 54,
            },
        ]

    def _extract_gap_text(self, text: str, indicator: str) -> Optional[str]:
        """Extract the gap description from review text."""
        # Simple extraction: get the sentence containing the indicator
        sentences = text.split(".")
        for sentence in sentences:
            if indicator in sentence:
                # Clean up the sentence
                gap = sentence.strip().capitalize()
                if len(gap) > 10:  # Filter out very short gaps
                    return gap
        return None

    def _calculate_confidence(self, gap_text: str, rating: int) -> float:
        """Calculate confidence score for a gap."""
        base_confidence = 0.5
        # Lower rating = higher confidence in the gap
        rating_factor = (5 - rating) / 4.0
        # Longer gap text = more specific = higher confidence
        length_factor = min(len(gap_text) / 100.0, 1.0)
        return min(base_confidence + rating_factor * 0.3 + length_factor * 0.2, 1.0)
