"""Tests for src.dashboard.tickers.DashboardTicker."""

import time
import pytest
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


class TestDashboardTickerInit:
    def test_default_values(self):
        dt = DashboardTicker()
        assert dt.symbol == ""
        assert dt.price == 0.0
        assert isinstance(dt.current_win_rate, WinRateMetric)
        assert isinstance(dt.bankroll_history, BankrollCurvePoint)
        assert isinstance(dt.nash_distance, NashEquilibriumShift)

    def test_custom_symbol(self):
        dt = DashboardTicker(symbol="TEST")
        assert dt.symbol == "TEST"


class TestDashboardTickerPriceColor:
    def test_win_rate_above_05_is_green(self):
        dt = DashboardTicker()
        dt.current_win_rate = WinRateMetric(value=0.6)
        assert dt.price_color == "green"

    def test_win_rate_below_05_is_red(self):
        dt = DashboardTicker()
        dt.current_win_rate = WinRateMetric(value=0.4)
        assert dt.price_color == "red"

    def test_win_rate_equal_05_is_white(self):
        dt = DashboardTicker()
        dt.current_win_rate = WinRateMetric(value=0.5)
        assert dt.price_color == "white"


class TestDashboardTickerUpdateFromState:
    def test_update_from_state(self):
        dt = DashboardTicker()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.7, total_games=100, wins=70, losses=30),
            bankroll=BankrollCurvePoint(step=10, bankroll=150.0, peak_bankroll=200.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash"),
            timestamp=1000.0,
        )
        dt.update_from_state(state)
        assert dt.current_win_rate.value == 0.7
        assert dt.current_win_rate.total_games == 100
        assert dt.bankroll_history.step == 10
        assert dt.bankroll_history.bankroll == 150.0
        assert dt.nash_distance.distance == 0.1
        assert dt.price == 0.7
        assert dt.timestamp == 1000.0

    def test_update_from_state_sets_color(self):
        dt = DashboardTicker()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        dt.update_from_state(state)
        assert dt.price_color == "green"


class TestDashboardTickerSerialization:
    def test_to_dict(self):
        dt = DashboardTicker(symbol="TEST")
        dt.current_win_rate = WinRateMetric(value=0.5)
        dt.bankroll_history = BankrollCurvePoint(step=1, bankroll=100.0)
        dt.nash_distance = NashEquilibriumShift(distance=0.1)
        d = dt.to_dict()
        assert d["symbol"] == "TEST"
        assert d["price"] == 0.0  # default price
        assert "current_win_rate" in d
        assert "bankroll_history" in d
        assert "nash_distance" in d

    def test_from_dict(self):
        data = {
            "symbol": "TEST",
            "price": 0.5,
            "timestamp": 1000.0,
            "previous_price": 0.0,
            "current_win_rate": {"value": 0.5, "total_games": 10, "wins": 5, "losses": 5, "timestamp": 1000.0},
            "bankroll_history": {"step": 1, "bankroll": 100.0, "peak_bankroll": 100.0, "drawdown": 0.0, "history": []},
            "nash_distance": {"distance": 0.1, "current_strategy": "test", "nash_strategy": "nash"},
        }
        dt = DashboardTicker.from_dict(data)
        assert dt.symbol == "TEST"
        assert dt.price == 0.5
        assert dt.current_win_rate.value == 0.5
        assert dt.bankroll_history.bankroll == 100.0
        assert dt.nash_distance.distance == 0.1

    def test_roundtrip(self):
        dt = DashboardTicker(symbol="RT")
        dt.current_win_rate = WinRateMetric(value=0.6, total_games=20, wins=12, losses=8)
        dt.bankroll_history = BankrollCurvePoint(step=5, bankroll=200.0, peak_bankroll=250.0, drawdown=-50.0)
        dt.nash_distance = NashEquilibriumShift(distance=0.05, current_strategy="s1", nash_strategy="nash")
        d = dt.to_dict()
        dt2 = DashboardTicker.from_dict(d)
        assert dt2.symbol == dt.symbol
        assert dt2.current_win_rate.value == dt.current_win_rate.value
        assert dt2.bankroll_history.bankroll == dt.bankroll_history.bankroll
        assert dt2.nash_distance.distance == dt.nash_distance.distance


class TestDashboardTickerPriceUpdate:
    def test_update_price(self):
        dt = DashboardTicker()
        dt.update_price(100.0)
        assert dt.price == 100.0
        assert dt.previous_price == 0.0

    def test_update_price_second_call(self):
        dt = DashboardTicker()
        dt.update_price(100.0)
        dt.update_price(110.0)
        assert dt.price == 110.0
        assert dt.previous_price == 100.0

    def test_price_change(self):
        dt = DashboardTicker()
        dt.update_price(100.0)
        dt.update_price(110.0)
        assert dt.price_change == 10.0

    def test_price_change_percent(self):
        dt = DashboardTicker()
        dt.update_price(100.0)
        dt.update_price(110.0)
        assert dt.price_change_percent == 10.0

    def test_price_change_percent_zero_base(self):
        dt = DashboardTicker()
        dt.update_price(0.0)
        dt.update_price(10.0)
        assert dt.price_change_percent == 0.0  # avoid division by zero


class TestDashboardTickerTimestamp:
    def test_timestamp_default(self):
        dt = DashboardTicker()
        assert isinstance(dt.timestamp, float)

    def test_timestamp_update(self):
        dt = DashboardTicker()
        old_ts = dt.timestamp
        time.sleep(0.01)
        dt.timestamp = time.time()
        assert dt.timestamp > old_ts
