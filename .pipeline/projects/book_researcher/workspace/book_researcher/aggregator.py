"""Aggregator interface and concrete implementations for fetching book reviews."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from book_researcher.models import BookReview


class ReviewAggregator(ABC):
    """Abstract interface for fetching book reviews."""

    @abstractmethod
    def fetch_reviews(self, book_id: str) -> list[dict[str, Any]]:
        """Fetch reviews for a given book_id.

        Returns a list of dicts with keys: text, rating, source, reviewer, helpful_votes.

        Raises:
            ValueError: If book_id is invalid.
            RuntimeError: If the fetch operation fails.
        """
        ...


class SampleReviewAggregator(ReviewAggregator):
    """Aggregator that returns sample/mock reviews for testing."""

    def fetch_reviews(self, book_id: str) -> list[dict[str, Any]]:
        """Return sample reviews.

        Args:
            book_id: Ignored for sample aggregator; any value works.

        Returns:
            List of review dicts.
        """
        from book_researcher.aggregators.sample_reviews import get_sample_reviews

        reviews = get_sample_reviews()
        return [
            {
                "text": r.text,
                "rating": r.rating,
                "source": r.source,
                "reviewer": r.reviewer,
                "helpful_votes": r.helpful_votes,
            }
            for r in reviews
        ]


class AmazonReviewAggregator(ReviewAggregator):
    """Aggregator for Amazon reviews (stub for future implementation)."""

    def fetch_reviews(self, book_id: str) -> list[dict[str, Any]]:
        """Fetch Amazon reviews.

        Raises:
            NotImplementedError: This aggregator is not yet implemented.
        """
        raise NotImplementedError("AmazonReviewAggregator is not yet implemented")


class GoodreadsReviewAggregator(ReviewAggregator):
    """Aggregator for Goodreads reviews (stub for future implementation)."""

    def fetch_reviews(self, book_id: str) -> list[dict[str, Any]]:
        """Fetch Goodreads reviews.

        Raises:
            NotImplementedError: This aggregator is not yet implemented.
        """
        raise NotImplementedError("GoodreadsReviewAggregator is not yet implemented")
