"""Aggregators subpackage."""

from book_researcher.aggregator import (
    AmazonReviewAggregator,
    GoodreadsReviewAggregator,
    ReviewAggregator,
    SampleReviewAggregator,
)

__all__ = [
    "ReviewAggregator",
    "SampleReviewAggregator",
    "GoodreadsReviewAggregator",
    "AmazonReviewAggregator",
]
