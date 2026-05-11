"""Tests for the ingestion task (idempotent upsert logic)."""

import sys
import pathlib

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from app.repositories.review_repo import _compute_hash


class TestIngestionTask:
    """Tests for the idempotent upsert logic."""

    def test_compute_hash_deterministic(self):
        """Same inputs should produce the same hash."""
        h1 = _compute_hash("biz1", "google", "Alice", "Great place")
        h2 = _compute_hash("biz1", "google", "Alice", "Great place")
        assert h1 == h2

    def test_compute_hash_different_inputs(self):
        """Different inputs should produce different hashes."""
        h1 = _compute_hash("biz1", "google", "Alice", "Great place")
        h2 = _compute_hash("biz1", "google", "Bob", "Great place")
        assert h1 != h2

        h3 = _compute_hash("biz1", "yelp", "Alice", "Great place")
        assert h1 != h3

        h4 = _compute_hash("biz1", "google", "Alice", "Different text")
        assert h1 != h4

    def test_compute_hash_empty_fields(self):
        """Hash should still be valid with empty fields."""
        h = _compute_hash("biz1", "google", "", "")
        assert len(h) == 64  # SHA-256 hex length

    def test_compute_hash_consistency(self):
        """Hash should be consistent across multiple calls."""
        hashes = [
            _compute_hash("biz1", "google", "Alice", "Great place")
            for _ in range(100)
        ]
        assert len(set(hashes)) == 1
