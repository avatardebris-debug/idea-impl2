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
        t = Ticker(symbol="TEST", price=42.0)
        assert t.symbol == "TEST"
        assert t.price == 42.0
        assert t.previous_price == 0.0


class TestTickerUpdate:
    def test_update_changes_price(self):
        t = Ticker(price=10.0)
        t.update(20.0)
        assert t.price == 20.0
        assert t.previous_price == 10.0

    def test_update_updates_timestamp(self):
        t = Ticker(price=10.0)
        before = time.time()
        t.update(20.0)
        after = time.time()
        assert before <= t.timestamp <= after


class TestTickerPriceColor:
    def test_first_update_is_white(self):
        t = Ticker()
        assert t.price_color == "white"

    def test_price_increase_is_green(self):
        t = Ticker(price=10.0)
        t.update(20.0)
        assert t.price_color == "green"

    def test_price_decrease_is_red(self):
        t = Ticker(price=20.0)
        t.update(10.0)
        assert t.price_color == "red"

    def test_price_unchanged_is_white(self):
        t = Ticker(price=10.0)
        t.update(10.0)
        assert t.price_color == "white"


class TestTickerSerialization:
    def test_to_dict(self):
        t = Ticker(symbol="TEST", price=42.0)
        d = t.to_dict()
        assert d["symbol"] == "TEST"
        assert d["price"] == 42.0
        assert "timestamp" in d
        assert "previous_price" in d
        assert "price_color" in d

    def test_from_dict(self):
        data = {
            "symbol": "TEST",
            "price": 42.0,
            "timestamp": 1000.0,
            "previous_price": 10.0,
        }
        t = Ticker.from_dict(data)
        assert t.symbol == "TEST"
        assert t.price == 42.0
        assert t.timestamp == 1000.0
        assert t.previous_price == 10.0

    def test_roundtrip(self):
        t = Ticker(symbol="RT", price=99.9)
        d = t.to_dict()
        t2 = Ticker.from_dict(d)
        assert t2.symbol == t.symbol
        assert t2.price == t.price
        assert t2.previous_price == t.previous_price
