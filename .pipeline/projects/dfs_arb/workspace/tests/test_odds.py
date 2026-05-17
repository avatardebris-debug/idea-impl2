"""Tests for odds conversion and analysis functions."""

import pytest
from dfs_arb.core.odds import (
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    odds_entry_to_decimal,
    check_overround,
    compute_implied_probabilities,
    find_best_odds,
)
from dfs_arb.core.models import OddsEntry, MarketType, OddsFormat


class TestAmericanToDecimal:
    """Tests for american_to_decimal conversion."""

    def test_positive_american(self):
        """Test conversion of positive American odds."""
        assert american_to_decimal(150) == 2.5
        assert american_to_decimal(200) == 3.0
        assert american_to_decimal(100) == 2.0

    def test_negative_american(self):
        """Test conversion of negative American odds."""
        assert american_to_decimal(-150) == 1.6666666666666667
        assert american_to_decimal(-200) == 1.5
        assert american_to_decimal(-100) == 2.0

    def test_zero_american(self):
        """Test conversion of zero American odds."""
        assert american_to_decimal(0) == 2.0

    def test_edge_cases(self):
        """Test edge cases."""
        # Large positive
        assert american_to_decimal(1000) == 11.0
        # Large negative
        assert american_to_decimal(-1000) == 1.1


class TestDecimalToAmerican:
    """Tests for decimal_to_american conversion."""

    def test_decimal_greater_than_2(self):
        """Test conversion of decimal odds > 2 to American."""
        assert decimal_to_american(2.5) == 150
        assert decimal_to_american(3.0) == 200
        assert decimal_to_american(2.0) == 100

    def test_decimal_less_than_2(self):
        """Test conversion of decimal odds < 2 to American."""
        assert decimal_to_american(1.5) == -200
        assert decimal_to_american(1.6666666666666667) == -150
        assert decimal_to_american(1.909) == -110

    def test_decimal_equal_2(self):
        """Test conversion of decimal odds = 2 to American."""
        assert decimal_to_american(2.0) == 100

    def test_edge_cases(self):
        """Test edge cases."""
        # Very large decimal
        assert decimal_to_american(11.0) == 1000
        # Very small decimal
        assert decimal_to_american(1.1) == -1000


class TestImpliedProbability:
    """Tests for implied probability calculation."""

    def test_decimal_odds(self):
        """Test implied probability with decimal odds."""
        assert implied_probability(2.0, "decimal") == 0.5
        assert implied_probability(1.5, "decimal") == pytest.approx(0.6666666666666666)
        assert implied_probability(3.0, "decimal") == pytest.approx(0.3333333333333333)

    def test_american_odds(self):
        """Test implied probability with American odds."""
        # American +100 = decimal 2.0
        assert implied_probability(100, "american") == 0.5
        # American -200 = decimal 1.5
        assert implied_probability(-200, "american") == pytest.approx(0.6666666666666666)
        # American +200 = decimal 3.0
        assert implied_probability(200, "american") == pytest.approx(0.3333333333333333)

    def test_invalid_format(self):
        """Test with invalid format raises ValueError."""
        with pytest.raises(ValueError):
            implied_probability(2.0, "invalid")


class TestOddsEntryToDecimal:
    """Tests for converting OddsEntry to decimal odds."""

    def test_decimal_entry(self):
        """Test conversion of decimal odds entry."""
        entry = OddsEntry(
            bookmaker="TestBook",
            market_id="test_market",
            side="over",
            odds=2.5,
            odds_format=OddsFormat.DECIMAL,
            market_type=MarketType.SPREAD,
        )
        assert odds_entry_to_decimal(entry) == 2.5

    def test_american_entry(self):
        """Test conversion of American odds entry."""
        entry = OddsEntry(
            bookmaker="TestBook",
            market_id="test_market",
            side="over",
            odds=150,
            odds_format=OddsFormat.AMERICAN,
            market_type=MarketType.SPREAD,
        )
        assert odds_entry_to_decimal(entry) == 2.5

    def test_invalid_format_entry(self):
        """Test with invalid format raises ValueError."""
        entry = OddsEntry(
            bookmaker="TestBook",
            market_id="test_market",
            side="over",
            odds=2.5,
            odds_format="invalid",  # type: ignore
            market_type=MarketType.SPREAD,
        )
        with pytest.raises(ValueError):
            odds_entry_to_decimal(entry)


class TestComputeImpliedProbabilities:
    """Tests for computing implied probabilities from entries."""

    def test_two_sided_market(self):
        """Test implied probability calculation for a two-sided market."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="over",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK2",
                market_id="test_market",
                side="under",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        probs = compute_implied_probabilities(entries)
        assert len(probs) == 2
        assert probs[0] == pytest.approx(0.5)
        assert probs[1] == pytest.approx(0.5)

    def test_three_sided_market(self):
        """Test implied probability calculation for a three-sided market."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="home",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK2",
                market_id="test_market",
                side="draw",
                odds=3.5,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK3",
                market_id="test_market",
                side="away",
                odds=4.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        probs = compute_implied_probabilities(entries)
        assert len(probs) == 3
        assert probs[0] == pytest.approx(0.5)
        assert probs[1] == pytest.approx(1.0 / 3.5)
        assert probs[2] == pytest.approx(0.25)


class TestCheckOverround:
    """Tests for overround calculation."""

    def test_fair_market(self):
        """Test overround for a fair market (sum of probs = 1)."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="over",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK2",
                market_id="test_market",
                side="under",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        overround = check_overround(entries)
        assert overround == pytest.approx(0.0)

    def test_vig_market(self):
        """Test overround for a market with vig."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="over",
                odds=1.90,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK2",
                market_id="test_market",
                side="under",
                odds=1.90,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        overround = check_overround(entries)
        # Sum of implied probs = 1/1.9 + 1/1.9 = 1.0526...
        # Overround = (1.0526 - 1) * 100 = 5.26...
        assert overround == pytest.approx(5.2631578947368425)

    def test_arbitrage_market(self):
        """Test overround for an arbitrage market (sum of probs < 1)."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="over",
                odds=2.10,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK2",
                market_id="test_market",
                side="under",
                odds=2.10,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        overround = check_overround(entries)
        # Sum of implied probs = 1/2.1 + 1/2.1 = 0.9523...
        # Overround = (0.9523 - 1) * 100 = -4.76...
        assert overround == pytest.approx(-4.761904761904762)


class TestFindBestOdds:
    """Tests for finding best odds."""

    def test_best_over(self):
        """Test finding best odds for 'over' side."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="over",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK2",
                market_id="test_market",
                side="over",
                odds=2.5,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        best_entry, best_decimal = find_best_odds(entries, "over")
        assert best_decimal == 2.5
        assert best_entry.bookmaker == "BK2"

    def test_best_under(self):
        """Test finding best odds for 'under' side."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="under",
                odds=1.90,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
            OddsEntry(
                bookmaker="BK2",
                market_id="test_market",
                side="under",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        best_entry, best_decimal = find_best_odds(entries, "under")
        assert best_decimal == 2.0
        assert best_entry.bookmaker == "BK2"

    def test_no_entries_for_side(self):
        """Test when no entries exist for the requested side."""
        entries = [
            OddsEntry(
                bookmaker="BK1",
                market_id="test_market",
                side="over",
                odds=2.0,
                odds_format=OddsFormat.DECIMAL,
                market_type=MarketType.SPREAD,
            ),
        ]
        best_entry, best_decimal = find_best_odds(entries, "under")
        assert best_decimal == 0.0
        assert best_entry is None
