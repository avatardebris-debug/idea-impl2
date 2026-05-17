"""Tests for arbitrage detection."""

import pytest
from dfs_arb.core.arbitrage import (
    ArbitrageOpportunity,
    find_arbitrage,
    find_arbitrage_with_bankroll,
)
from dfs_arb.core.models import MarketType, OddsEntry


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


class TestFindArbitrage:
    """Tests for find_arbitrage function."""

    def test_no_arbitrage_even_odds(self):
        """Test no arbitrage with even odds on both sides."""
        entries = [
            _make_entry("test", "BK1", "over", 2.0),
            _make_entry("test", "BK2", "under", 2.0),
        ]
        result = find_arbitrage(entries)
        assert result is None

    def test_arbitrage_exists(self):
        """Test arbitrage detection when it exists."""
        entries = [
            _make_entry("test", "BK1", "over", 2.1),
            _make_entry("test", "BK2", "under", 2.1),
        ]
        result = find_arbitrage(entries)
        assert result is not None
        assert result.profit_pct > 0

    def test_no_arbitrage_unfavorable(self):
        """Test no arbitrage when odds are unfavorable."""
        entries = [
            _make_entry("test", "BK1", "over", 1.8),
            _make_entry("test", "BK2", "under", 1.8),
        ]
        result = find_arbitrage(entries)
        assert result is None

    def test_three_way_arbitrage(self):
        """Test three-way arbitrage detection."""
        entries = [
            _make_entry("test", "BK1", "home", 3.0),
            _make_entry("test", "BK2", "draw", 3.5),
            _make_entry("test", "BK3", "away", 3.0),
        ]
        result = find_arbitrage(entries)
        # With these odds, there should be no arbitrage
        assert result is None

    def test_three_way_arbitrage_exists(self):
        """Test three-way arbitrage when it exists."""
        entries = [
            _make_entry("test", "BK1", "home", 3.2),
            _make_entry("test", "BK2", "draw", 3.5),
            _make_entry("test", "BK3", "away", 3.2),
        ]
        result = find_arbitrage(entries)
        assert result is not None
        assert result.profit_pct > 0


class TestFindArbitrageWithBankroll:
    """Tests for find_arbitrage_with_bankroll function."""

    def test_arbitrage_with_bankroll(self):
        """Test arbitrage with bankroll constraint."""
        entries = [
            _make_entry("test", "BK1", "over", 2.1),
            _make_entry("test", "BK2", "under", 2.1),
        ]
        result = find_arbitrage_with_bankroll(entries, bankroll=1000.0, min_profit_pct=0.5)
        assert result is not None
        assert result.total_stake == pytest.approx(1000.0)
        assert result.guaranteed_profit > 0

    def test_no_arbitrage_with_bankroll(self):
        """Test no arbitrage with bankroll constraint."""
        entries = [
            _make_entry("test", "BK1", "over", 1.8),
            _make_entry("test", "BK2", "under", 1.8),
        ]
        result = find_arbitrage_with_bankroll(entries, bankroll=1000.0, min_profit_pct=0.5)
        assert result is None

    def test_min_profit_filter(self):
        """Test minimum profit filter."""
        entries = [
            _make_entry("test", "BK1", "over", 2.01),
            _make_entry("test", "BK2", "under", 2.01),
        ]
        # Should find arbitrage with low min_profit
        result_low = find_arbitrage_with_bankroll(entries, bankroll=1000.0, min_profit_pct=0.1)
        assert result_low is not None

        # Should not find arbitrage with high min_profit
        result_high = find_arbitrage_with_bankroll(entries, bankroll=1000.0, min_profit_pct=1.0)
        assert result_high is None

    def test_max_stake_constraint(self):
        """Test max stake constraint."""
        entries = [
            _make_entry("test", "BK1", "over", 2.5),
            _make_entry("test", "BK2", "under", 2.5),
        ]
        result = find_arbitrage_with_bankroll(
            entries,
            bankroll=1000.0,
            min_profit_pct=0.5,
            max_stake_pct=0.5,
        )
        assert result is not None
        assert result.total_stake == pytest.approx(500.0)  # 50% of 1000


class TestArbitrageOpportunity:
    """Tests for ArbitrageOpportunity dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        opp = ArbitrageOpportunity(
            market_id="test",
            market_type=MarketType.TWO_SIDED,
            event_name="Test",
            event_date="2024-01-01",
            sport="Test",
            total_implied_prob=0.95,
            profit_pct=5.0,
            total_stake=1000.0,
            guaranteed_profit=50.0,
            stake_distribution={"over": 500.0, "under": 500.0},
            outcomes=[("over", "BK1", 2.1), ("under", "BK2", 2.1)],
        )
        d = opp.to_dict()
        assert d["market_id"] == "test"
        assert d["profit_pct"] == 5.0
        assert d["total_stake"] == 1000.0
        assert d["guaranteed_profit"] == 50.0
