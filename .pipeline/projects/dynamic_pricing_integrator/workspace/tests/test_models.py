"""Unit tests for dynamic pricing models and configuration."""

import pytest
from datetime import datetime

from dynamic_pricing.models import Product, CompetitorPrice, PriceSnapshot
from dynamic_pricing.config import PricingConfig
from dynamic_pricing.constants import DEFAULT_CURRENCY
from dynamic_pricing.mock_sources import MockAPISource, MockCSVSource
from dynamic_pricing.price_tracker import PriceTracker


# ---- Product tests ----

def test_product_creation():
    """(1) Product dataclass creation."""
    p = Product(id="1", name="Test Product", base_price=10.0, category="Electronics")
    assert p.id == "1"
    assert p.name == "Test Product"
    assert p.base_price == 10.0
    assert p.category == "Electronics"


def test_product_default_currency():
    """(2) Product default currency."""
    p = Product(id="2", name="Default Currency", base_price=5.0)
    assert p.currency == DEFAULT_CURRENCY


# ---- CompetitorPrice tests ----

def test_competitor_price_creation():
    """(3) CompetitorPrice dataclass creation."""
    cp = CompetitorPrice(
        product_id="1",
        competitor_name="CompA",
        price=9.99,
        last_updated=datetime.now(),
    )
    assert cp.product_id == "1"
    assert cp.competitor_name == "CompA"
    assert cp.price == 9.99
    assert isinstance(cp.last_updated, datetime)


# ---- PriceSnapshot tests ----

def test_price_snapshot_creation():
    """(4) PriceSnapshot dataclass creation."""
    ts = datetime.now()
    ps = PriceSnapshot(
        product_id="1",
        competitor="CompA",
        price=9.99,
        timestamp=ts,
        source="test_source",
    )
    assert ps.product_id == "1"
    assert ps.competitor == "CompA"
    assert ps.price == 9.99
    assert ps.source == "test_source"


def test_price_snapshot_timestamp_is_datetime():
    """(5) PriceSnapshot timestamp is datetime."""
    ps = PriceSnapshot(
        product_id="1",
        competitor="CompA",
        price=9.99,
        timestamp=datetime.now(),
        source="test",
    )
    assert isinstance(ps.timestamp, datetime)


# ---- PricingConfig tests ----

def test_pricing_config_default_polling_interval():
    """(6) PricingConfig default polling_interval."""
    c = PricingConfig()
    assert c.polling_interval == 900


def test_pricing_config_default_margin_floor():
    """(7) PricingConfig default margin_floor."""
    c = PricingConfig()
    assert c.margin_floor == 0.15


def test_pricing_config_custom_values():
    """(8) PricingConfig custom values."""
    c = PricingConfig(
        polling_interval=600,
        margin_floor=0.20,
        competitor_sources=["SourceA", "SourceB"],
    )
    assert c.polling_interval == 600
    assert c.margin_floor == 0.20
    assert c.competitor_sources == ["SourceA", "SourceB"]


# ---- MockAPISource tests ----

def test_mock_api_source_returns_prices():
    """(9) MockAPISource returns prices."""
    source = MockAPISource()
    prices = source.fetch_prices("prod1")
    assert len(prices) >= 2
    assert all(isinstance(p, CompetitorPrice) for p in prices)


def test_mock_csv_source_returns_prices():
    """(10) MockCSVSource returns prices."""
    source = MockCSVSource()
    prices = source.fetch_prices("prod1")
    assert len(prices) >= 2
    assert all(isinstance(p, CompetitorPrice) for p in prices)


def test_mock_sources_return_different_competitors():
    """(11) Mock sources return different competitors."""
    api_source = MockAPISource()
    csv_source = MockCSVSource()
    api_prices = api_source.fetch_prices("prod1")
    csv_prices = csv_source.fetch_prices("prod1")
    api_names = {p.competitor_name for p in api_prices}
    csv_names = {p.competitor_name for p in csv_prices}
    # API and CSV sources should have different competitor names
    assert api_names.isdisjoint(csv_names)


# ---- PriceTracker tests ----

def test_price_tracker_add_source():
    """(12) PriceTracker add_source."""
    tracker = PriceTracker()
    source = MockAPISource()
    tracker.add_source(source)
    assert source in tracker._sources


def test_price_tracker_remove_source():
    """(13) PriceTracker remove_source."""
    tracker = PriceTracker()
    source = MockAPISource()
    tracker.add_source(source)
    tracker.remove_source(source)
    assert source not in tracker._sources


def test_poll_all_returns_snapshots_with_correct_fields():
    """(14) poll_all returns snapshots with correct fields."""
    tracker = PriceTracker()
    source = MockAPISource()
    tracker.add_source(source)
    snapshots = tracker.poll_all()
    assert len(snapshots) >= 2
    for s in snapshots:
        assert isinstance(s, PriceSnapshot)
        assert hasattr(s, "product_id")
        assert hasattr(s, "competitor")
        assert hasattr(s, "price")
        assert hasattr(s, "timestamp")
        assert hasattr(s, "source")


def test_poll_all_from_multiple_sources():
    """(15) poll_all from 2+ sources simultaneously."""
    tracker = PriceTracker()
    api_source = MockAPISource()
    csv_source = MockCSVSource()
    tracker.add_source(api_source)
    tracker.add_source(csv_source)
    snapshots = tracker.poll_all()
    # Should have at least 4 snapshots (2 from each source)
    assert len(snapshots) >= 4
    sources_seen = {s.source for s in snapshots}
    assert "mock_api" in sources_seen
    assert "mock_csv" in sources_seen


def test_get_current_price_returns_latest_snapshot():
    """(16) get_current_price returns latest snapshot."""
    tracker = PriceTracker()
    source = MockAPISource()
    tracker.add_source(source)
    # poll_all sets product_id to "" from MockAPISource, so we need a source
    # that sets a real product_id. Let's use a custom approach.
    # Actually, MockAPISource.fetch_prices("") sets product_id="" — let's test
    # with a product_id that matches.
    # We need to test with a source that returns a non-empty product_id.
    # Let's create a custom source for this test.
    class CustomSource:
        def fetch_prices(self, product_id):
            return [
                CompetitorPrice(
                    product_id=product_id,
                    competitor_name="CompX",
                    price=10.0,
                    last_updated=datetime.now(),
                )
            ]

    tracker2 = PriceTracker()
    tracker2.add_source(CustomSource())
    result = tracker2.get_current_price("prod1")
    assert result is not None
    assert result.product_id == "prod1"


def test_get_current_price_returns_none_for_unknown_product():
    """(17) get_current_price returns None for unknown product."""
    # Use a source that only returns data for a specific product
    class SelectiveSource:
        def fetch_prices(self, product_id):
            if product_id == "prod1":
                return [
                    CompetitorPrice(
                        product_id=product_id,
                        competitor_name="CompX",
                        price=10.0,
                        last_updated=datetime.now(),
                    )
                ]
            return []

    tracker = PriceTracker()
    tracker.add_source(SelectiveSource())
    result = tracker.get_current_price("unknown_prod")
    assert result is None
