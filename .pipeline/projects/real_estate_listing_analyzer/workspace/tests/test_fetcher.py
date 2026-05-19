"""
tests/test_fetcher.py — unit tests for real_estate_listing_analyzer fetcher & analyzer
"""
import pytest
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from real_estate_listing_analyzer.fetcher import Listing, save_cache, load_latest_cache
from real_estate_listing_analyzer.analyzer import TrendAnalyzer, ComparablesFinder, linear_slope


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_listing(**kwargs) -> Listing:
    defaults = dict(
        zpid="1", address="123 Main St", city="Austin", state="TX",
        zip_code="78701", bedrooms=3, bathrooms=2.0, sqft=1500,
        price=450_000, price_per_sqft=300.0, days_on_market=15,
        zestimate=460_000,
    )
    defaults.update(kwargs)
    return Listing(**defaults)


SAMPLE_LISTINGS = [
    _make_listing(zpid="1", price=400_000, price_per_sqft=266.67, sqft=1500, days_on_market=10, zestimate=420_000),
    _make_listing(zpid="2", price=500_000, price_per_sqft=312.50, sqft=1600, days_on_market=20, zestimate=490_000, bedrooms=4),
    _make_listing(zpid="3", price=350_000, price_per_sqft=233.33, sqft=1500, days_on_market=5,  zestimate=380_000, bedrooms=2),
    _make_listing(zpid="4", price=600_000, price_per_sqft=375.00, sqft=1600, days_on_market=30, zestimate=610_000, bedrooms=4, bathrooms=3.0),
    _make_listing(zpid="5", price=420_000, price_per_sqft=280.00, sqft=1500, days_on_market=12, zestimate=430_000),
]


# ---------------------------------------------------------------------------
# linear_slope
# ---------------------------------------------------------------------------

def test_linear_slope_increasing():
    slope = linear_slope([1.0, 2.0, 3.0, 4.0])
    assert slope > 0

def test_linear_slope_flat():
    slope = linear_slope([5.0, 5.0, 5.0])
    assert abs(slope) < 1e-9

def test_linear_slope_single_point():
    assert linear_slope([42.0]) == 0.0

def test_linear_slope_empty():
    assert linear_slope([]) == 0.0


# ---------------------------------------------------------------------------
# TrendAnalyzer
# ---------------------------------------------------------------------------

def test_trend_analyzer_basic():
    analyzer = TrendAnalyzer()
    result = analyzer.analyze(SAMPLE_LISTINGS, zip_code="78701")
    assert result.listing_count == 5
    assert result.median_price > 0
    assert result.median_price_per_sqft > 0
    assert 0 <= result.neighborhood_score <= 100
    assert result.median_dom > 0

def test_trend_analyzer_empty():
    analyzer = TrendAnalyzer()
    result = analyzer.analyze([], zip_code="00000")
    assert result.listing_count == 0
    assert result.median_price == 0

def test_list_to_zestimate_ratio():
    """Listings priced below Zestimate should yield ratio < 1."""
    analyzer = TrendAnalyzer()
    result = analyzer.analyze(SAMPLE_LISTINGS, zip_code="78701")
    # Most sample listings are below their Zestimate
    assert result.list_to_sale_ratio < 1.0


# ---------------------------------------------------------------------------
# ComparablesFinder
# ---------------------------------------------------------------------------

def test_comparables_returns_k_results():
    finder = ComparablesFinder()
    target = SAMPLE_LISTINGS[0]
    comps = finder.find(target, SAMPLE_LISTINGS, k=3)
    assert len(comps) == 3
    # Target itself should not be in comps
    assert all(c.zpid != target.zpid for c in comps)

def test_comparables_excludes_target():
    finder = ComparablesFinder()
    target = SAMPLE_LISTINGS[2]
    comps = finder.find(target, SAMPLE_LISTINGS, k=10)
    assert target.zpid not in [c.zpid for c in comps]

def test_comparables_similarity():
    """Most similar listing should have closest price and sqft."""
    finder = ComparablesFinder()
    target = _make_listing(zpid="99", price=400_000, sqft=1500, bedrooms=3)
    comps = finder.find(target, SAMPLE_LISTINGS, k=1)
    assert comps[0].bedrooms == 3  # closest match should be a 3-bed
