"""Tests for the ArbEngine."""

import pytest
from dfs_arb.core.engine import ArbEngine
from dfs_arb.core.models import MarketType, OddsEntry
from dfs_arb.core.promos import PromoOffer, PromoType


def _make_entry(
    market_id: str,
    bookmaker: str,
    side: str,
    decimal_odds: float,
    line_value: float = None,
) -> OddsEntry:
    """Helper to create an OddsEntry."""
    return OddsEntry(
        market_id=market_id,
        market_type=MarketType.TWO_SIDED,
        event_name="Test Event",
        event_date="2024-01-01",
        sport="Test",
        bookmaker=bookmaker,
        side=side,
        decimal_odds=decimal_odds,
        line_value=line_value,
        odds_format="decimal",
        odds_value=decimal_odds,
    )


class TestArbEngine:
    """Tests for ArbEngine class."""

    def test_init(self):
        """Test engine initialization."""
        entries = [
            _make_entry("test", "BK1", "over", 2.1),
            _make_entry("test", "BK2", "under", 2.1),
        ]
        engine = ArbEngine(entries=entries, bankroll=1000.0)
        assert engine.total_markets == 1
        assert engine.total_bookmakers == 2
        assert engine.total_entries == 2

    def test_find_arbitrage_opportunities(self):
        """Test finding arbitrage opportunities."""
        entries = [
            _make_entry("test", "BK1", "over", 2.1),
            _make_entry("test", "BK2", "under", 2.1),
        ]
        engine = ArbEngine(entries=entries, bankroll=1000.0, min_profit_pct=0.5)
        opportunities = engine.find_arbitrage_opportunities()
        assert len(opportunities) == 1
        assert opportunities[0].profit_pct > 0

    def test_no_arbitrage_opportunities(self):
        """Test no arbitrage opportunities when none exist."""
        entries = [
            _make_entry("test", "BK1", "over", 1.8),
            _make_entry("test", "BK2", "under", 1.8),
        ]
        engine = ArbEngine(entries=entries, bankroll=1000.0, min_profit_pct=0.5)
        opportunities = engine.find_arbitrage_opportunities()
        assert len(opportunities) == 0

    def test_multiple_markets(self):
        """Test engine with multiple markets."""
        entries = [
            _make_entry("test1", "BK1", "over", 2.1),
            _make_entry("test1", "BK2", "under", 2.1),
            _make_entry("test2", "BK3", "over", 1.8),
            _make_entry("test2", "BK4", "under", 1.8),
        ]
        engine = ArbEngine(entries=entries, bankroll=1000.0, min_profit_pct=0.5)
        assert engine.total_markets == 2
        opportunities = engine.find_arbitrage_opportunities()
        assert len(opportunities) == 1  # Only test1 has arbitrage

    def test_run_analysis(self):
        """Test full analysis pipeline."""
        entries = [
            _make_entry("test", "BK1", "over", 2.1),
            _make_entry("test", "BK2", "under", 2.1),
        ]
        promos = [
            PromoOffer(
                promo_id="test_promo",
                promo_type=PromoType.SIGNUP_BONUS,
                provider="TestProvider",
                description="Test promo",
                max_bonus=100.0,
                min_deposit=10.0,
                rollover_requirement=1.0,
                expiry_date="2024-12-31",
                eligible_markets=["all"],
                terms="Test terms",
            )
        ]
        engine = ArbEngine(entries=entries, promos=promos, bankroll=1000.0)
        result = engine.run_analysis()
        assert result.total_markets == 1
        assert result.total_bookmakers == 2
        assert result.total_entries == 2
        assert len(result.arbitrage_opportunities) == 1
        assert len(result.promo_evaluations) == 1

    def test_get_best_odds(self):
        """Test getting best odds for a market."""
        entries = [
            _make_entry("test", "BK1", "over", 2.0),
            _make_entry("test", "BK2", "over", 2.5),
            _make_entry("test", "BK3", "under", 1.8),
            _make_entry("test", "BK4", "under", 1.9),
        ]
        engine = ArbEngine(entries=entries)
        best = engine.get_best_odds("test")
        assert best is not None
        assert best["over"] == pytest.approx(2.5)
        assert best["under"] == pytest.approx(1.9)

    def test_get_overround(self):
        """Test getting overround for a market."""
        entries = [
            _make_entry("test", "BK1", "over", 2.0),
            _make_entry("test", "BK2", "under", 2.0),
        ]
        engine = ArbEngine(entries=entries)
        overround = engine.get_overround("test")
        assert overround is not None
        assert overround == pytest.approx(0.0)

    def test_get_market_entries(self):
        """Test getting market entries."""
        entries = [
            _make_entry("test", "BK1", "over", 2.0),
            _make_entry("test", "BK2", "under", 2.0),
        ]
        engine = ArbEngine(entries=entries)
        market_entries = engine.get_market_entries("test")
        assert market_entries is not None
        assert len(market_entries) == 2

    def test_repr(self):
        """Test string representation."""
        entries = [
            _make_entry("test", "BK1", "over", 2.0),
        ]
        engine = ArbEngine(entries=entries)
        assert "ArbEngine" in repr(engine)
        assert "markets=1" in repr(engine)

    def test_empty_engine(self):
        """Test engine with no entries."""
        engine = ArbEngine(entries=[])
        assert engine.total_markets == 0
        assert engine.total_bookmakers == 0
        assert engine.total_entries == 0
        opportunities = engine.find_arbitrage_opportunities()
        assert len(opportunities) == 0
