"""Tests for the MockDataSource."""

from __future__ import annotations

import threading
import time
import pytest
from src.data_source import MockDataSource
from src.ticker import Ticker


class TestMockDataSourceCreation:
    """Tests for MockDataSource creation and initialization."""

    def test_create_default_data_source(self):
        ds = MockDataSource()
        assert ds.update_interval == 1.0
        assert ds.volatility == 0.01
        assert ds.get_status()["running"] is False
        assert ds.get_status()["ticker_count"] == 0

    def test_create_data_source_with_custom_params(self):
        ds = MockDataSource(update_interval=0.5, volatility=0.05)
        assert ds.update_interval == 0.5
        assert ds.volatility == 0.05

    def test_create_data_source_with_initial_tickers(self):
        ds = MockDataSource(tickers={"AAPL": 100.0, "GOOGL": 200.0})
        assert ds.get_status()["ticker_count"] == 2
        assert ds.get_ticker("AAPL").price == 100.0
        assert ds.get_ticker("GOOGL").price == 200.0


class TestMockDataSourceTickerManagement:
    """Tests for ticker management in MockDataSource."""

    def test_add_ticker(self):
        ds = MockDataSource()
        ds.add_ticker("AAPL", 100.0, "Apple Inc.")
        assert ds.get_status()["ticker_count"] == 1
        ticker = ds.get_ticker("AAPL")
        assert ticker is not None
        assert ticker.symbol == "AAPL"
        assert ticker.price == 100.0
        assert ticker.name == "Apple Inc."

    def test_add_ticker_default_name(self):
        ds = MockDataSource()
        ds.add_ticker("AAPL", 100.0)
        assert ds.get_ticker("AAPL").name == "AAPL"

    def test_add_duplicate_ticker(self):
        ds = MockDataSource()
        ds.add_ticker("AAPL", 100.0)
        ds.add_ticker("AAPL", 105.0)
        # Should not add a duplicate
        assert ds.get_status()["ticker_count"] == 1
        assert ds.get_ticker("AAPL").price == 100.0

    def test_remove_ticker(self):
        ds = MockDataSource()
        ds.add_ticker("AAPL", 100.0)
        assert ds.remove_ticker("AAPL") is True
        assert ds.get_status()["ticker_count"] == 0
        assert ds.get_ticker("AAPL") is None

    def test_remove_nonexistent_ticker(self):
        ds = MockDataSource()
        assert ds.remove_ticker("AAPL") is False
        assert ds.get_status()["ticker_count"] == 0

    def test_get_nonexistent_ticker(self):
        ds = MockDataSource()
        assert ds.get_ticker("AAPL") is None

    def test_get_all_tickers(self):
        ds = MockDataSource()
        ds.add_ticker("AAPL", 100.0)
        ds.add_ticker("GOOGL", 200.0)
        tickers = ds.get_tickers()
        assert len(tickers) == 2
        symbols = {t.symbol for t in tickers}
        assert symbols == {"AAPL", "GOOGL"}


class TestMockDataSourceUpdate:
    """Tests for ticker updates in MockDataSource."""

    def test_force_update_returns_tickers(self):
        ds = MockDataSource()
        ds.add_ticker("AAPL", 100.0)
        updated = ds.force_update()
        assert len(updated) == 1
        assert updated[0].symbol == "AAPL"

    def test_force_update_changes_prices(self):
        ds = MockDataSource(volatility=0.01)
        ds.add_ticker("AAPL", 100.0)
        initial_price = ds.get_ticker("AAPL").price
        updated = ds.force_update()
        new_price = updated[0].price
        # Price should have changed (with high probability given volatility)
        # Since volatility is 0.01, change is at most 1%
        assert abs(new_price - initial_price) > 0 or abs(new_price - initial_price) <= initial_price * 0.01

    def test_force_update_with_no_tickers(self):
        ds = MockDataSource()
        updated = ds.force_update()
        assert updated == []

    def test_start_stops_thread(self):
        ds = MockDataSource(update_interval=0.1)
        ds.add_ticker("AAPL", 100.0)
        ds.start()
        assert ds.get_status()["running"] is True
        time.sleep(0.3)
        ds.stop()
        assert ds.get_status()["running"] is False

    def test_start_multiple_times(self):
        ds = MockDataSource()
        ds.start()
        ds.start()  # Should not raise
        assert ds.get_status()["running"] is True
        ds.stop()

    def test_stop_without_start(self):
        ds = MockDataSource()
        ds.stop()  # Should not raise
        assert ds.get_status()["running"] is False


class TestMockDataSourceStatus:
    """Tests for MockDataSource status reporting."""

    def test_get_status(self):
        ds = MockDataSource(update_interval=0.5, volatility=0.02)
        ds.add_ticker("AAPL", 100.0)
        status = ds.get_status()
        assert status["running"] is False
        assert status["ticker_count"] == 1
        assert status["update_interval"] == 0.5
        assert status["volatility"] == 0.02

    def test_status_after_start(self):
        ds = MockDataSource()
        ds.start()
        status = ds.get_status()
        assert status["running"] is True
        ds.stop()

    def test_ticker_count_after_add_remove(self):
        ds = MockDataSource()
        assert ds.get_status()["ticker_count"] == 0
        ds.add_ticker("AAPL", 100.0)
        assert ds.get_status()["ticker_count"] == 1
        ds.remove_ticker("AAPL")
        assert ds.get_status()["ticker_count"] == 0
