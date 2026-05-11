"""Tests for the Ticker data model."""

from __future__ import annotations

import pytest
from src.ticker import Ticker


class TestTickerCreation:
    """Tests for Ticker creation and initialization."""

    def test_create_minimal_ticker(self):
        ticker = Ticker(symbol="AAPL")
        assert ticker.symbol == "AAPL"
        assert ticker.name == ""
        assert ticker.price == 0.0
        assert ticker.change == 0.0
        assert ticker.change_percent == 0.0
        assert ticker.volume == 0

    def test_create_full_ticker(self):
        ticker = Ticker(
            symbol="AAPL",
            name="Apple Inc.",
            price=100.0,
            open_price=98.0,
            change=2.0,
            change_percent=2.04,
            volume=1000000,
            high=102.0,
            low=97.0,
            previous_close=98.0,
        )
        assert ticker.symbol == "AAPL"
        assert ticker.name == "Apple Inc."
        assert ticker.price == 100.0
        assert ticker.open_price == 98.0
        assert ticker.change == 2.0
        assert ticker.change_percent == 2.04
        assert ticker.volume == 1000000
        assert ticker.high == 102.0
        assert ticker.low == 97.0
        assert ticker.previous_close == 98.0

    def test_post_init_calculates_open_price(self):
        """When open_price is 0 and change is provided, open_price should be calculated."""
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0)
        assert ticker.open_price == 95.0

    def test_post_init_does_not_calculate_open_price_when_change_is_zero(self):
        """When change is 0, open_price should not be calculated from price."""
        ticker = Ticker(symbol="AAPL", price=100.0, change=0.0)
        assert ticker.open_price == 0.0

    def test_post_init_does_not_calculate_open_price_when_price_is_zero(self):
        """When price is 0, open_price should not be calculated."""
        ticker = Ticker(symbol="AAPL", price=0.0, change=5.0)
        assert ticker.open_price == 0.0

    def test_post_init_calculates_previous_close(self):
        """When previous_close is 0 and open_price > 0, previous_close should be set to open_price."""
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0)
        assert ticker.previous_close == 95.0

    def test_post_init_does_not_calculate_previous_close_when_already_set(self):
        """When previous_close is already set, it should not be changed."""
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0, previous_close=90.0)
        assert ticker.previous_close == 90.0

    def test_post_init_does_not_calculate_previous_close_when_open_price_is_zero(self):
        """When open_price is 0, previous_close should not be calculated."""
        ticker = Ticker(symbol="AAPL", price=100.0, change=0.0)
        assert ticker.previous_close == 0.0


class TestTickerColors:
    """Tests for Ticker color calculations."""

    def test_positive_change_colors(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        assert ticker.price_color == (0.0, 1.0, 0.0)
        assert ticker.background_color == (0.0, 0.5, 0.0)

    def test_negative_change_colors(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=-5.0, change_percent=-5.0)
        assert ticker.price_color == (1.0, 0.0, 0.0)
        assert ticker.background_color == (0.5, 0.0, 0.0)

    def test_zero_change_colors(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=0.0, change_percent=0.0)
        assert ticker.price_color == (0.5, 0.5, 0.5)
        assert ticker.background_color == (0.25, 0.25, 0.25)

    def test_text_color_is_always_white(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        assert ticker.text_color == (1.0, 1.0, 1.0)


class TestTickerSerialization:
    """Tests for Ticker serialization."""

    def test_ticker_to_dict(self):
        ticker = Ticker(
            symbol="AAPL",
            name="Apple Inc.",
            price=100.0,
            open_price=98.0,
            change=2.0,
            change_percent=2.04,
            volume=1000000,
            high=102.0,
            low=97.0,
            previous_close=98.0,
        )
        data = ticker.to_dict()
        assert data["symbol"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["price"] == 100.0
        assert data["open_price"] == 98.0
        assert data["change"] == 2.0
        assert data["change_percent"] == 2.04
        assert data["volume"] == 1000000
        assert data["high"] == 102.0
        assert data["low"] == 97.0
        assert data["previous_close"] == 98.0

    def test_ticker_from_dict(self):
        data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "price": 100.0,
            "open_price": 98.0,
            "change": 2.0,
            "change_percent": 2.04,
            "volume": 1000000,
            "high": 102.0,
            "low": 97.0,
            "previous_close": 98.0,
        }
        ticker = Ticker.from_dict(data)
        assert ticker.symbol == "AAPL"
        assert ticker.name == "Apple Inc."
        assert ticker.price == 100.0
        assert ticker.open_price == 98.0
        assert ticker.change == 2.0
        assert ticker.change_percent == 2.04
        assert ticker.volume == 1000000
        assert ticker.high == 102.0
        assert ticker.low == 97.0
        assert ticker.previous_close == 98.0

    def test_ticker_equality(self):
        ticker1 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        ticker2 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        assert ticker1 == ticker2

    def test_ticker_inequality(self):
        ticker1 = Ticker(symbol="AAPL", price=100.0)
        ticker2 = Ticker(symbol="GOOGL", price=100.0)
        assert ticker1 != ticker2


class TestTickerValidation:
    """Tests for Ticker validation."""

    def test_invalid_symbol_raises_error(self):
        with pytest.raises(ValueError):
            Ticker(symbol="")

    def test_invalid_price_raises_error(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", price=-1.0)

    def test_invalid_high_raises_error(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", price=100.0, high=50.0)

    def test_invalid_low_raises_error(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", price=100.0, low=150.0)

    def test_invalid_volume_raises_error(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", volume=-1)

    def test_invalid_change_percent_raises_error(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", change_percent=150.0)

    def test_high_must_be_greater_than_low(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", price=100.0, high=90.0, low=95.0)

    def test_high_must_be_at_least_price(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", price=100.0, high=99.0)

    def test_low_must_be_at_most_price(self):
        with pytest.raises(ValueError):
            Ticker(symbol="AAPL", price=100.0, low=101.0)
