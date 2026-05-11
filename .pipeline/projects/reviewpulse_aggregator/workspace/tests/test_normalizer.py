"""Tests for the normalizer service."""

import sys
import pathlib

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from app.services.normalizer import normalize_review


class TestNormalizer:
    """Tests for the normalize_review function."""

    def test_normalize_basic_fields(self):
        raw = {
            "place_id": "ChIJ1234567890",
            "platform": "google",
            "author_name": "John Doe",
            "rating": 4,
            "text": "Great place!",
            "time": 1700000000,
            "profile_photo_url": "https://example.com/photo.jpg",
        }
        result = normalize_review(raw)
        assert result["business_id"] == "ChIJ1234567890"
        assert result["platform"] == "google"
        assert result["author"] == "John Doe"
        assert result["rating"] == 4
        assert result["text"] == "Great place!"
        assert result["sentiment_score"] is None
        assert result["sentiment_label"] is None

    def test_normalize_html_decoding(self):
        raw = {
            "place_id": "ChIJ1234567890",
            "rating": 5,
            "text": "It&#39;s <b>amazing</b>!",
            "time": 1700000000,
        }
        result = normalize_review(raw)
        assert "&amp;" not in result["text"]
        assert "&lt;" not in result["text"]
        assert "&gt;" not in result["text"]
        assert "&quot;" not in result["text"]
        assert "&#39;" not in result["text"]

    def test_normalize_whitespace_normalization(self):
        raw = {
            "place_id": "ChIJ1234567890",
            "rating": 3,
            "text": "  This   is   a   test.  ",
            "time": 1700000000,
        }
        result = normalize_review(raw)
        assert "  " not in result["text"]
        assert result["text"] == "This is a test."

    def test_normalize_missing_fields(self):
        raw = {
            "place_id": "ChIJ1234567890",
        }
        result = normalize_review(raw)
        assert result["author"] == ""
        assert result["rating"] is None
        assert result["text"] == ""
        assert result["published_at"] is None

    def test_normalize_rating_clamping(self):
        raw = {
            "place_id": "ChIJ1234567890",
            "rating": 0,
            "text": "Test",
            "time": 1700000000,
        }
        result = normalize_review(raw)
        assert result["rating"] == 1

        raw["rating"] = 6
        result = normalize_review(raw)
        assert result["rating"] == 5
