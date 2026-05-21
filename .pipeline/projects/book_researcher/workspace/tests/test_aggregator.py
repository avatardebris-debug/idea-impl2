"""Tests for the aggregator module."""

import pytest
from book_researcher.aggregator import SampleReviewAggregator, ReviewAggregator
from book_researcher.aggregators.sample_reviews import get_sample_reviews


class TestSampleReviewAggregator:
    """Tests for SampleReviewAggregator."""

    def test_fetch_reviews_returns_list(self):
        """fetch_reviews should return a list."""
        agg = SampleReviewAggregator()
        result = agg.fetch_reviews("test_book")
        assert isinstance(result, list)

    def test_fetch_reviews_returns_dicts(self):
        """fetch_reviews should return dicts with expected keys."""
        agg = SampleReviewAggregator()
        result = agg.fetch_reviews("test_book")
        if result:
            for item in result:
                assert isinstance(item, dict)
                assert "text" in item
                assert "rating" in item

    def test_fetch_reviews_non_empty(self):
        """fetch_reviews should return non-empty list for sample data."""
        agg = SampleReviewAggregator()
        result = agg.fetch_reviews("test_book")
        assert len(result) > 0

    def test_fetch_reviews_with_book_id(self):
        """fetch_reviews should accept a book_id parameter."""
        agg = SampleReviewAggregator()
        result = agg.fetch_reviews("dl_fundamentals")
        assert isinstance(result, list)


class TestSampleReviews:
    """Tests for the sample_reviews module."""

    def test_get_sample_reviews_returns_list(self):
        """get_sample_reviews should return a list."""
        reviews = get_sample_reviews()
        assert isinstance(reviews, list)

    def test_get_sample_reviews_non_empty(self):
        """get_sample_reviews should return non-empty list."""
        reviews = get_sample_reviews()
        assert len(reviews) > 0

    def test_get_sample_reviews_has_book_id(self):
        """Each review should have a book_id."""
        from book_researcher.models import BookReview
        reviews = get_sample_reviews()
        for review in reviews:
            assert isinstance(review, BookReview)
            assert hasattr(review, "book_id")
            assert review.book_id
