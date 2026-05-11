"""Tests for the reviews API endpoint."""

import sys
import pathlib

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from app.schemas.review import ReviewResponse, ReviewListResponse, ReviewCreate


class TestReviewSchemas:
    """Tests for the Pydantic review schemas."""

    def test_review_response_valid(self):
        data = {
            "id": 1,
            "business_id": "biz1",
            "platform": "google",
            "author": "Alice",
            "rating": 5,
            "text": "Great place!",
            "published_at": "2024-01-01T00:00:00",
            "source_url": "https://example.com",
            "sentiment_score": 0.8,
            "sentiment_label": "positive",
            "review_hash": "abc123",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        response = ReviewResponse.model_validate(data)
        assert response.id == 1
        assert response.rating == 5
        assert response.sentiment_label == "positive"

    def test_review_list_response_valid(self):
        data = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0,
        }
        response = ReviewListResponse.model_validate(data)
        assert response.total == 0
        assert response.page == 1

    def test_review_create_requires_hash(self):
        data = {
            "business_id": "biz1",
            "platform": "google",
            "review_hash": "abc123",
        }
        create = ReviewCreate.model_validate(data)
        assert create.review_hash == "abc123"
