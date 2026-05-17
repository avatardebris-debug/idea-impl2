"""Tests for quant_developing_program.core.utils."""

import pytest

from quant_developing_program.core.utils import (
    trend_indicator,
    format_probability,
    format_odds,
    clamp,
    safe_divide,
    expected_value,
    implied_probability,
    decimal_odds_from_probability,
)


class TestTrendIndicator:
    def test_upward_trend(self):
        result = trend_indicator(110, 100)
        assert result == "▲ +10.0%"

    def test_downward_trend(self):
        result = trend_indicator(90, 100)
        assert result == "▼ -10.0%"

    def test_no_change(self):
        result = trend_indicator(100, 100)
        assert result == "● 0.0%"

    def test_large_increase(self):
        result = trend_indicator(200, 100)
        assert result == "▲ +100.0%"

    def test_large_decrease(self):
        result = trend_indicator(50, 100)
        assert result == "▼ -50.0%"

    def test_zero_reference(self):
        result = trend_indicator(100, 0)
        assert result == "● 0.0%"


class TestFormatProbability:
    def test_zero_probability(self):
        assert format_probability(0.0) == "0.00%"

    def test_one_probability(self):
        assert format_probability(1.0) == "100.00%"

    def test_half_probability(self):
        assert format_probability(0.5) == "50.00%"

    def test_invalid_probability(self):
        with pytest.raises(ValueError):
            format_probability(1.5)

    def test_negative_probability(self):
        with pytest.raises(ValueError):
            format_probability(-0.1)


class TestFormatOdds:
    def test_decimal_odds(self):
        assert format_odds(2.0) == "2.00"

    def test_fractional_odds(self):
        assert format_odds(1.5) == "3/2"

    def test_american_odds(self):
        assert format_odds(3.0) == "+200"

    def test_invalid_odds(self):
        with pytest.raises(ValueError):
            format_odds(0.5)

    def test_negative_odds(self):
        with pytest.raises(ValueError):
            format_odds(-1.0)


class TestClamp:
    def test_within_range(self):
        assert clamp(5, 0, 10) == 5

    def test_below_range(self):
        assert clamp(-5, 0, 10) == 0

    def test_above_range(self):
        assert clamp(15, 0, 10) == 10

    def test_equal_to_min(self):
        assert clamp(0, 0, 10) == 0

    def test_equal_to_max(self):
        assert clamp(10, 0, 10) == 10

    def test_invalid_range(self):
        with pytest.raises(ValueError):
            clamp(5, 10, 0)


class TestSafeDivide:
    def test_normal_division(self):
        assert safe_divide(10, 2) == 5.0

    def test_division_by_zero(self):
        assert safe_divide(10, 0) == 0.0

    def test_zero_numerator(self):
        assert safe_divide(0, 5) == 0.0

    def test_both_zero(self):
        assert safe_divide(0, 0) == 0.0

    def test_negative_values(self):
        assert safe_divide(-10, 2) == -5.0


class TestExpectedValue:
    def test_positive_ev(self):
        ev = expected_value(0.6, 2.0)
        assert ev > 0

    def test_negative_ev(self):
        ev = expected_value(0.4, 2.0)
        assert ev < 0

    def test_zero_ev(self):
        ev = expected_value(0.5, 2.0)
        assert ev == 0.0

    def test_invalid_probability(self):
        with pytest.raises(ValueError):
            expected_value(1.5, 2.0)

    def test_invalid_odds(self):
        with pytest.raises(ValueError):
            expected_value(0.6, 0.5)


class TestImpliedProbability:
    def test_decimal_odds(self):
        prob = implied_probability(2.0)
        assert prob == pytest.approx(0.5)

    def test_high_odds(self):
        prob = implied_probability(10.0)
        assert prob == pytest.approx(0.1)

    def test_low_odds(self):
        prob = implied_probability(1.1)
        assert prob == pytest.approx(0.909)

    def test_invalid_odds(self):
        with pytest.raises(ValueError):
            implied_probability(0.5)


class TestDecimalOddsFromProbability:
    def test_half_probability(self):
        odds = decimal_odds_from_probability(0.5)
        assert odds == pytest.approx(2.0)

    def test_high_probability(self):
        odds = decimal_odds_from_probability(0.9)
        assert odds == pytest.approx(1.111)

    def test_low_probability(self):
        odds = decimal_odds_from_probability(0.1)
        assert odds == pytest.approx(10.0)

    def test_invalid_probability(self):
        with pytest.raises(ValueError):
            decimal_odds_from_probability(1.5)

    def test_zero_probability(self):
        with pytest.raises(ValueError):
            decimal_odds_from_probability(0.0)
