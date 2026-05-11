"""Tests for the DataSource abstract interface and mock implementations."""

from __future__ import annotations

import pytest
from abc import ABC, abstractmethod
from typing import List, Optional

from src.ticker import Ticker
from src.data_source import DataSource


class MockDataSource(DataSource):
    """Concrete mock implementation of DataSource for testing."""

    def __init__(self):
        self._tickers: dict[str, Ticker] = {}
        self._connected: bool = False
        self._callbacks: List[callable] = []

    def get_tickers(self, symbols: Optional[List[str]] = None) -> List[Ticker]:
        if symbols:
            return [self._tickers[s] for s in symbols if s in self._tickers]
        return list(self._tickers.values())

    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        return self._tickers.get(symbol)

    def update_ticker(self, ticker: Ticker) -> None:
        self._tickers[ticker.symbol] = ticker

    def subscribe(self, callback: callable) -> None:
        self._callbacks.append(callback)

    def unsubscribe(self, callback: callable) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False


class TestDataSourceInterface:
    """Tests for DataSource abstract interface."""

    def test_data_source_is_abstract(self):
        """DataSource should not be instantiable directly."""
        with pytest.raises(TypeError):
            DataSource()

    def test_mock_data_source_implements_interface(self):
        """MockDataSource should be instantiable."""
        ds = MockDataSource()
        assert isinstance(ds, DataSource)


class TestMockDataSourceConnectivity:
    """Tests for DataSource connection management."""

    def test_initially_not_connected(self):
        ds = MockDataSource()
        assert ds.is_connected() is False

    def test_connect_sets_connected(self):
        ds = MockDataSource()
        result = ds.connect()
        assert result is True
        assert ds.is_connected() is True

    def test_disconnect_clears_connection(self):
        ds = MockDataSource()
        ds.connect()
        ds.disconnect()
        assert ds.is_connected() is False

    def test_double_connect(self):
        ds = MockDataSource()
        result1 = ds.connect()
        result2 = ds.connect()
        assert result1 is True
        assert result2 is True
        assert ds.is_connected() is True


class TestMockDataSourceTickerOperations:
    """Tests for DataSource ticker CRUD operations."""

    def test_get_ticker_empty(self):
        ds = MockDataSource()
        result = ds.get_ticker("AAPL")
        assert result is None

    def test_update_and_get_ticker(self):
        ds = MockDataSource()
        ticker = Ticker(symbol="AAPL", price=100.0)
        ds.update_ticker(ticker)
        result = ds.get_ticker("AAPL")
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.price == 100.0

    def test_get_tickers_empty(self):
        ds = MockDataSource()
        result = ds.get_tickers()
        assert result == []

    def test_get_tickers_with_data(self):
        ds = MockDataSource()
        ds.update_ticker(Ticker(symbol="AAPL", price=100.0))
        ds.update_ticker(Ticker(symbol="GOOGL", price=200.0))
        result = ds.get_tickers()
        assert len(result) == 2
        symbols = {t.symbol for t in result}
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

    def test_get_tickers_with_symbols_filter(self):
        ds = MockDataSource()
        ds.update_ticker(Ticker(symbol="AAPL", price=100.0))
        ds.update_ticker(Ticker(symbol="GOOGL", price=200.0))
        ds.update_ticker(Ticker(symbol="MSFT", price=300.0))
        result = ds.get_tickers(symbols=["AAPL", "MSFT"])
        assert len(result) == 2
        symbols = {t.symbol for t in result}
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" not in symbols

    def test_get_tickers_with_partial_symbols_filter(self):
        ds = MockDataSource()
        ds.update_ticker(Ticker(symbol="AAPL", price=100.0))
        result = ds.get_tickers(symbols=["AAPL", "NONEXISTENT"])
        assert len(result) == 1
        assert result[0].symbol == "AAPL"

    def test_update_existing_ticker(self):
        ds = MockDataSource()
        ds.update_ticker(Ticker(symbol="AAPL", price=100.0))
        ds.update_ticker(Ticker(symbol="AAPL", price=105.0))
        result = ds.get_ticker("AAPL")
        assert result.price == 105.0

    def test_update_ticker_overwrites_previous(self):
        ds = MockDataSource()
        ds.update_ticker(Ticker(symbol="AAPL", price=100.0))
        ds.update_ticker(Ticker(symbol="AAPL", price=105.0, change=5.0))
        result = ds.get_ticker("AAPL")
        assert result.price == 105.0
        assert result.change == 5.0


class TestMockDataSourceSubscription:
    """Tests for DataSource subscription mechanism."""

    def test_subscribe_and_unsubscribe(self):
        ds = MockDataSource()
        callback = lambda x: x
        ds.subscribe(callback)
        assert callback in ds._callbacks
        ds.unsubscribe(callback)
        assert callback not in ds._callbacks

    def test_unsubscribe_nonexistent_callback(self):
        ds = MockDataSource()
        callback = lambda x: x
        # Should not raise
        ds.unsubscribe(callback)

    def test_multiple_subscribers(self):
        ds = MockDataSource()
        callback1 = lambda x: x
        callback2 = lambda x: x
        ds.subscribe(callback1)
        ds.subscribe(callback2)
        assert len(ds._callbacks) == 2
        ds.unsubscribe(callback1)
        assert len(ds._callbacks) == 1
        assert callback2 in ds._callbacks

    def test_subscribe_same_callback_twice(self):
        ds = MockDataSource()
        callback = lambda x: x
        ds.subscribe(callback)
        ds.subscribe(callback)
        assert len(ds._callbacks) == 2

    def test_unsubscribe_removes_all_instances(self):
        ds = MockDataSource()
        callback = lambda x: x
        ds.subscribe(callback)
        ds.subscribe(callback)
        ds.unsubscribe(callback)
        assert callback not in ds._callbacks


class TestMockDataSourceEdgeCases:
    """Tests for edge cases in DataSource."""

    def test_get_ticker_with_empty_symbol(self):
        ds = MockDataSource()
        result = ds.get_ticker("")
        assert result is None

    def test_update_ticker_with_empty_symbol(self):
        ds = MockDataSource()
        ticker = Ticker(symbol="", price=100.0)
        ds.update_ticker(ticker)
        result = ds.get_ticker("")
        assert result is not None
        assert result.symbol == ""

    def test_get_tickers_with_empty_list(self):
        ds = MockDataSource()
        result = ds.get_tickers(symbols=[])
        assert result == []

    def test_get_tickers_with_none_symbols(self):
        ds = MockDataSource()
        ds.update_ticker(Ticker(symbol="AAPL", price=100.0))
        result = ds.get_tickers(symbols=None)
        assert len(result) == 1

    def test_update_ticker_with_none_values(self):
        ds = MockDataSource()
        ticker = Ticker(symbol="AAPL", price=100.0)
        ds.update_ticker(ticker)
        # Update with same ticker should not cause issues
        ds.update_ticker(ticker)
        result = ds.get_ticker("AAPL")
        assert result.price == 100.0

    def test_connection_state_persists_across_operations(self):
        ds = MockDataSource()
        ds.connect()
        ds.update_ticker(Ticker(symbol="AAPL", price=100.0))
        assert ds.is_connected() is True
        ds.get_ticker("AAPL")
        assert ds.is_connected() is True
        ds.disconnect()
        assert ds.is_connected() is False
