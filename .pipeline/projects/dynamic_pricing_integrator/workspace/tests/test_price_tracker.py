"""Unit tests for the PriceTracker engine."""

import pytest
from datetime import datetime

from dynamic_pricing.models import CompetitorPrice, PriceSnapshot
from dynamic_pricing.price_tracker import PriceTracker
from dynamic_pricing.mock_sources import MockAPISource, MockCSVSource


class TestPriceTrackerSourceManagement:
    """Tests for add_source and remove_source."""

    def test_add_source(self):
        """PriceTracker add_source adds a source."""
        tracker = PriceTracker()
        source = MockAPISource()
        tracker.add_source(source)
        assert source in tracker._sources

    def test_add_duplicate_source(self):
        """Adding the same source twice does not duplicate it."""
        tracker = PriceTracker()
        source = MockAPISource()
        tracker.add_source(source)
        tracker.add_source(source)
        assert tracker._sources.count(source) == 1

    def test_remove_source(self):
        """PriceTracker remove_source removes a source."""
        tracker = PriceTracker()
        source = MockAPISource()
        tracker.add_source(source)
        tracker.remove_source(source)
        assert source not in tracker._sources

    def test_remove_nonexistent_source(self):
        """Removing a nonexistent source does not raise."""
        tracker = PriceTracker()
        source = MockAPISource()
        tracker.remove_source(source)  # Should not raise


class TestPriceTrackerPolling:
    """Tests for poll_all and poll_for_product."""

    def test_poll_all_returns_snapshots(self):
        """poll_all returns a list of PriceSnapshot objects."""
        tracker = PriceTracker()
        tracker.add_source(MockAPISource())
        tracker.add_source(MockCSVSource())
        snapshots = tracker.poll_all()
        assert isinstance(snapshots, list)
        assert len(snapshots) > 0
        assert all(isinstance(s, PriceSnapshot) for s in snapshots)

    def test_poll_for_product_filters_by_product_id(self):
        """poll_for_product returns only snapshots for the given product."""
        tracker = PriceTracker()
        tracker.add_source(MockAPISource())
        snapshots = tracker.poll_for_product("PROD-001")
        assert all(s.product_id == "PROD-001" for s in snapshots)

    def test_poll_for_product_no_matches(self):
        """poll_for_product returns results for any product_id (mock sources don't filter)."""
        tracker = PriceTracker()
        tracker.add_source(MockAPISource())
        snapshots = tracker.poll_for_product("ANY_PRODUCT")
        # Mock sources return prices for any product_id
        assert len(snapshots) == 2

    def test_poll_all_empty_when_no_sources(self):
        """poll_all returns empty list when no sources are registered."""
        tracker = PriceTracker()
        snapshots = tracker.poll_all()
        assert snapshots == []

    def test_poll_for_product_empty_when_no_sources(self):
        """poll_for_product returns empty list when no sources are registered."""
        tracker = PriceTracker()
        snapshots = tracker.poll_for_product("PROD-001")
        assert snapshots == []


class TestPriceTrackerIntegration:
    """Integration tests for PriceTracker with mock sources."""

    def test_mock_api_source_produces_valid_snapshots(self):
        """MockAPISource produces PriceSnapshot objects with correct fields."""
        tracker = PriceTracker()
        tracker.add_source(MockAPISource())
        snapshots = tracker.poll_all()
        for s in snapshots:
            assert hasattr(s, "product_id")
            assert hasattr(s, "price")
            assert hasattr(s, "timestamp")
            assert hasattr(s, "source")
            assert s.source == "mock_api"

    def test_mock_csv_source_produces_valid_snapshots(self):
        """MockCSVSource produces PriceSnapshot objects with correct fields."""
        tracker = PriceTracker()
        tracker.add_source(MockCSVSource())
        snapshots = tracker.poll_all()
        for s in snapshots:
            assert hasattr(s, "product_id")
            assert hasattr(s, "price")
            assert hasattr(s, "timestamp")
            assert hasattr(s, "source")
            assert s.source == "mock_csv"

    def test_combined_sources_produce_combined_results(self):
        """Combining sources produces results from all sources."""
        tracker = PriceTracker()
        tracker.add_source(MockAPISource())
        tracker.add_source(MockCSVSource())
        snapshots = tracker.poll_all()
        sources = {s.source for s in snapshots}
        assert "mock_api" in sources
        assert "mock_csv" in sources

    def test_poll_for_product_with_multiple_sources(self):
        """poll_for_product works correctly with multiple sources."""
        tracker = PriceTracker()
        tracker.add_source(MockAPISource())
        tracker.add_source(MockCSVSource())
        snapshots = tracker.poll_for_product("PROD-001")
        assert len(snapshots) > 0
        assert all(s.product_id == "PROD-001" for s in snapshots)


class TestPriceSnapshotModel:
    """Tests for the PriceSnapshot model."""

    def test_price_snapshot_creation(self):
        """PriceSnapshot can be created with required fields."""
        snapshot = PriceSnapshot(
            product_id="PROD-001",
            competitor="Competitor A",
            price=99.99,
            timestamp=datetime.now(),
            source="test",
        )
        assert snapshot.product_id == "PROD-001"
        assert snapshot.competitor == "Competitor A"
        assert snapshot.price == 99.99
        assert snapshot.source == "test"

    def test_price_snapshot_str_representation(self):
        """PriceSnapshot str representation is informative."""
        snapshot = PriceSnapshot(
            product_id="PROD-001",
            competitor="Competitor A",
            price=99.99,
            timestamp=datetime.now(),
            source="test",
        )
        assert "PROD-001" in str(snapshot)
        assert "99.99" in str(snapshot)


class TestCompetitorPriceModel:
    """Tests for the CompetitorPrice model."""

    def test_competitor_price_creation(self):
        """CompetitorPrice can be created with required fields."""
        price = CompetitorPrice(
            product_id="PROD-001",
            competitor_name="Competitor A",
            price=99.99,
        )
        assert price.product_id == "PROD-001"
        assert price.competitor_name == "Competitor A"
        assert price.price == 99.99

    def test_competitor_price_str_representation(self):
        """CompetitorPrice str representation is informative."""
        price = CompetitorPrice(
            product_id="PROD-001",
            competitor_name="Competitor A",
            price=99.99,
        )
        assert "PROD-001" in str(price)
        assert "99.99" in str(price)
