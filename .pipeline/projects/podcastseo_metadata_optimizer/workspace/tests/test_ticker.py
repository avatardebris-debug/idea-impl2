"""Tests for src.ticker.Ticker."""

import time
import pytest
from src.ticker import Ticker


class TestTickerInit:
    def test_default_values(self):
        t = Ticker()
        assert t.symbol == ""
        assert t.price == 0.0
        assert t.previous_price == 0.0
        assert t._color == "white"
        assert isinstance(t.timestamp, float)

    def test_custom_values(self):
        t = Ticker(symbol="AAPL", price=150.0)
        assert t.symbol == "AAPL"
        assert t.price == 150.0
        assert t.previous_price == 0.0


class TestTickerPriceColor:
    def test_price_increase_is_green(self):
        t = Ticker(price=100.0)
        t.update(110.0)
        assert t.price_color == "green"

    def test_price_decrease_is_red(self):
        t = Ticker(price=100.0)
        t.update(90.0)
        assert t.price_color == "red"

    def test_price_unchanged_is_white(self):
        t = Ticker(price=100.0)
        t.update(100.0)
        assert t.price_color == "white"

    def test_no_previous_price_is_white(self):
        t = Ticker(price=100.0)
        assert t.price_color == "white"


class TestTickerUpdate:
    def test_update_changes_price(self):
        t = Ticker(price=100.0)
        t.update(120.0)
        assert t.price == 120.0
        assert t.previous_price == 100.0

    def test_update_changes_timestamp(self):
        t = Ticker(price=100.0)
        old_ts = t.timestamp
        time.sleep(0.01)
        t.update(110.0)
        assert t.timestamp > old_ts


class TestTickerSerialization:
    def test_to_dict(self):
        t = Ticker(symbol="TEST", price=50.0)
        t.update(55.0)
        d = t.to_dict()
        assert d["symbol"] == "TEST"
        assert d["price"] == 55.0
        assert d["previous_price"] == 50.0
        assert "timestamp" in d
        assert "price_color" in d

    def test_from_dict(self):
        data = {
            "symbol": "TEST",
            "price": 75.0,
            "previous_price": 70.0,
            "timestamp": 1000.0,
            "price_color": "green",
        }
        t = Ticker.from_dict(data)
        assert t.symbol == "TEST"
        assert t.price == 75.0
        assert t.previous_price == 70.0
        assert t.timestamp == 1000.0

    def test_roundtrip(self):
        t = Ticker(symbol="RT", price=100.0)
        t.update(110.0)
        d = t.to_dict()
        t2 = Ticker.from_dict(d)
        assert t2.symbol == t.symbol
        assert t2.price == t.price
        assert t2.previous_price == t.previous_price
        assert t2.timestamp == t.timestamp
