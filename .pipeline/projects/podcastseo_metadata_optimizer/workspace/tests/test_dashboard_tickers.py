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


class TestDashboardTickerSerialization:
    def test_to_dict(self):
        dt = DashboardTicker(symbol="TEST")
        dt.price = 50.0
        dt.timestamp = 1000.0
        dt.previous_price = 45.0
        dt.current_win_rate = WinRateMetric(value=0.6, total_games=10, wins=6, losses=4)
        dt.bankroll_history = BankrollCurvePoint(step=5, bankroll=100.0, peak_bankroll=120.0, drawdown=-20.0)
        dt.nash_distance = NashEquilibriumShift(distance=0.3, current_strategy="test")

        d = dt.to_dict()
        assert d["symbol"] == "TEST"
        assert d["price"] == 50.0
        assert d["timestamp"] == 1000.0
        assert d["previous_price"] == 45.0
        assert d["current_win_rate"]["value"] == 0.6
        assert d["bankroll_history"]["step"] == 5
        assert d["nash_distance"]["distance"] == 0.3

    def test_from_dict(self):
        data = {
            "symbol": "TEST",
            "price": 75.0,
            "timestamp": 2000.0,
            "previous_price": 70.0,
            "current_win_rate": {"value": 0.8, "total_games": 50, "wins": 40, "losses": 10},
            "bankroll_history": {"step": 10, "bankroll": 200.0, "peak_bankroll": 250.0, "drawdown": -50.0},
            "nash_distance": {"distance": 0.2, "current_strategy": "balanced"},
        }
        dt = DashboardTicker.from_dict(data)
        assert dt.symbol == "TEST"
        assert dt.price == 75.0
        assert dt.timestamp == 2000.0
        assert dt.previous_price == 70.0
        assert dt.current_win_rate.value == 0.8
        assert dt.bankroll_history.step == 10
        assert dt.nash_distance.distance == 0.2

    def test_roundtrip(self):
        dt = DashboardTicker(symbol="RT")
        dt.price = 100.0
        dt.timestamp = 3000.0
        dt.previous_price = 90.0
        dt.current_win_rate = WinRateMetric(value=0.55, total_games=20, wins=11, losses=9)
        dt.bankroll_history = BankrollCurvePoint(step=15, bankroll=180.0, peak_bankroll=200.0, drawdown=-20.0)
        dt.nash_distance = NashEquilibriumShift(distance=0.15, current_strategy="test")

        d = dt.to_dict()
        dt2 = DashboardTicker.from_dict(d)
        assert dt2.symbol == dt.symbol
        assert dt2.price == dt.price
        assert dt2.timestamp == dt.timestamp
        assert dt2.previous_price == dt.previous_price
        assert dt2.current_win_rate.value == dt.current_win_rate.value
        assert dt2.bankroll_history.step == dt.bankroll_history.step
        assert dt2.nash_distance.distance == dt.nash_distance.distance
