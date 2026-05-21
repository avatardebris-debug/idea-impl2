"""Tests for the gap_extractor module."""

import pytest
from book_researcher.gap_extractor import extract_gaps, GAP_PHRASES
from book_researcher.models import Gap


class TestExtractGaps:
    """Tests for extract_gaps function."""

    def test_extract_gaps_returns_list(self):
        """extract_gaps should return a list."""
        reviews = [
            {"text": "I wish it also covered more examples", "rating": 3.0},
        ]
        result = extract_gaps(reviews)
        assert isinstance(result, list)

    def test_extract_gaps_returns_gap_objects(self):
        """extract_gaps should return Gap objects."""
        reviews = [
            {"text": "I wish it also covered more examples", "rating": 3.0},
        ]
        result = extract_gaps(reviews)
        for gap in result:
            assert isinstance(gap, Gap)

    def test_extract_gaps_with_gap_phrase(self):
        """extract_gaps should find gaps with gap-indicating phrases."""
        reviews = [
            {"text": "Great book but I wish it also covered deep learning", "rating": 4.0},
        ]
        result = extract_gaps(reviews)
        assert len(result) > 0

    def test_extract_gaps_empty_reviews(self):
        """extract_gaps should return empty list for empty reviews."""
        result = extract_gaps([])
        assert result == []

    def test_extract_gaps_no_gap_phrases(self):
        """extract_gaps should return empty list when no gap phrases found."""
        reviews = [
            {"text": "This book is excellent and covers everything I needed", "rating": 5.0},
        ]
        result = extract_gaps(reviews)
        # Should have no gaps since no gap-indicating phrases
        assert len(result) == 0

    def test_extract_gaps_multiple_reviews(self):
        """extract_gaps should process multiple reviews."""
        reviews = [
            {"text": "I wish it also covered examples", "rating": 3.0},
            {"text": "I want more practical exercises", "rating": 2.5},
            {"text": "Great overview but I wish it also had case studies", "rating": 4.0},
        ]
        result = extract_gaps(reviews)
        assert len(result) >= 2  # At least 2 gaps should be found

    def test_extract_gaps_gap_has_topic(self):
        """Each gap should have a topic field."""
        reviews = [
            {"text": "I wish it also covered deep learning", "rating": 3.0},
        ]
        result = extract_gaps(reviews)
        for gap in result:
            assert hasattr(gap, "topic")
            assert gap.topic

    def test_extract_gaps_gap_has_text(self):
        """Each gap should have a text field."""
        reviews = [
            {"text": "I wish it also covered deep learning", "rating": 3.0},
        ]
        result = extract_gaps(reviews)
        for gap in result:
            assert hasattr(gap, "text")
            assert gap.text
