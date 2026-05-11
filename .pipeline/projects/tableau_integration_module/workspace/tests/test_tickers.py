"""Tests for dashboard tickers."""

import time
import pytest
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


class TestDashboardTicker:
    """Tests for DashboardTicker."""

    def test_default_values(self):
        """Test default values are correct."""
        ticker = DashboardTicker(symbol="TEST")
        assert ticker.symbol == "TEST"
        assert isinstance(ticker.current_win_rate, WinRateMetric)
        assert isinstance(ticker.bankroll_history, BankrollCurvePoint)
        assert isinstance(ticker.nash_distance, NashEquilibriumShift)

    def test_price_color_win_rate_above_half(self):
        """Test price color is green when win rate > 0.5."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.6)
        assert ticker.price_color == "green"

    def test_price_color_win_rate_below_half(self):
        """Test price color is red when win rate < 0.5."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.4)
        assert ticker.price_color == "red"

    def test_price_color_win_rate_exactly_half(self):
        """Test price color is white when win rate == 0.5."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.5)
        assert ticker.price_color == "white"

    def test_update_from_state(self):
        """Test updating ticker from DashboardState."""
        ticker = DashboardTicker(symbol="TEST")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=1234567890.0,
        )
        ticker.update_from_state(state)
        assert ticker.current_win_rate.value == 0.75
        assert ticker.bankroll_history.bankroll == 1500.0
        assert ticker.nash_distance.distance == 0.1
        assert ticker.price == 0.75
        assert ticker.timestamp == 1234567890.0

    def test_update_price(self):
        """Test updating price."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.price = 100.0
        ticker.previous_price = 90.0
        ticker.update_price(110.0)
        assert ticker.price == 110.0
        assert ticker.previous_price == 100.0
        assert isinstance(ticker.timestamp, float)

    def test_price_change(self):
        """Test price change calculation."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.price = 110.0
        ticker.previous_price = 100.0
        assert ticker.price_change == 10.0

    def test_price_change_percent(self):
        """Test price change percent calculation."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.price = 110.0
        ticker.previous_price = 100.0
        assert ticker.price_change_percent == 10.0

    def test_price_change_percent_zero_previous(self):
        """Test price change percent returns 0 when previous price is zero."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.price = 50.0
        ticker.previous_price = 0.0
        assert ticker.price_change_percent == 0.0

    def test_to_dict(self):
        """Test serialization to dict."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.price = 0.75
        ticker.previous_price = 0.70
        ticker.timestamp = 1234567890.0
        ticker.current_win_rate = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0)
        ticker.bankroll_history = BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0)
        ticker.nash_distance = NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0)

        d = ticker.to_dict()
        assert d["symbol"] == "TEST"
        assert d["price"] == 0.75
        assert d["previous_price"] == 0.70
        assert d["timestamp"] == 1234567890.0
        assert d["current_win_rate"]["value"] == 0.75
        assert d["bankroll_history"]["bankroll"] == 1500.0
        assert d["nash_distance"]["distance"] == 0.1

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "symbol": "TEST",
            "price": 0.80,
            "timestamp": 9876543210.0,
            "previous_price": 0.75,
            "current_win_rate": {"value": 0.8, "total_games": 200, "wins": 160, "losses": 40, "timestamp": 200.0},
            "bankroll_history": {"step": 10, "bankroll": 2000.0, "peak_bankroll": 2200.0, "drawdown": -200.0, "history": [1000.0, 2000.0], "timestamp": 200.0},
            "nash_distance": {"distance": 0.15, "current_strategy": "call", "nash_strategy": "nash_equilibrium", "timestamp": 200.0},
        }
        ticker = DashboardTicker.from_dict(data)
        assert ticker.symbol == "TEST"
        assert ticker.price == 0.80
        assert ticker.previous_price == 0.75
        assert ticker.timestamp == 9876543210.0
        assert ticker.current_win_rate.value == 0.8
        assert ticker.bankroll_history.bankroll == 2000.0
        assert ticker.nash_distance.distance == 0.15

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {"symbol": "TEST"}
        ticker = DashboardTicker.from_dict(data)
        assert ticker.symbol == "TEST"
        assert ticker.price == 0.0
        assert ticker.previous_price == 0.0

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = DashboardTicker(symbol="TEST")
        original.price = 0.65
        original.previous_price = 0.60
        original.timestamp = 1111111111.0
        original.current_win_rate = WinRateMetric(value=0.65, total_games=50, wins=32, losses=18, timestamp=1111111111.0)
        original.bankroll_history = BankrollCurvePoint(step=3, bankroll=1200.0, peak_bankroll=1300.0, drawdown=-100.0, history=[1000.0, 1100.0, 1200.0], timestamp=1111111111.0)
        original.nash_distance = NashEquilibriumShift(distance=0.08, current_strategy="fold", nash_strategy="nash_equilibrium", timestamp=1111111111.0)

        d = original.to_dict()
        restored = DashboardTicker.from_dict(d)
        assert restored.symbol == original.symbol
        assert restored.price == original.price
        assert restored.previous_price == original.previous_price
        assert restored.timestamp == original.timestamp
        assert restored.current_win_rate.value == original.current_win_rate.value
        assert restored.bankroll_history.bankroll == original.bankroll_history.bankroll
        assert restored.nash_distance.distance == original.nash_distance.distance

    def test_nested_objects_preserved(self):
        """Test that nested objects are preserved through roundtrip."""
        original = DashboardTicker(symbol="TEST")
        original.price = 0.55
        original.previous_price = 0.50
        original.timestamp = 1111111111.0
        original.current_win_rate = WinRateMetric(value=0.55, total_games=100, wins=55, losses=45, timestamp=400.0)
        original.bankroll_history = BankrollCurvePoint(step=20, bankroll=2500.0, peak_bankroll=2800.0, drawdown=-300.0, history=[1000.0, 2000.0, 2500.0], timestamp=400.0)
        original.nash_distance = NashEquilibriumShift(distance=0.2, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=400.0)

        d = original.to_dict()
        restored = DashboardTicker.from_dict(d)
        assert restored.current_win_rate.total_games == original.current_win_rate.total_games
        assert restored.current_win_rate.wins == original.current_win_rate.wins
        assert restored.current_win_rate.losses == original.current_win_rate.losses
        assert restored.bankroll_history.step == original.bankroll_history.step
        assert restored.bankroll_history.peak_bankroll == original.bankroll_history.peak_bankroll
        assert restored.bankroll_history.drawdown == original.bankroll_history.drawdown
        assert restored.bankroll_history.history == original.bankroll_history.history
        assert restored.nash_distance.current_strategy == original.nash_distance.current_strategy
        assert restored.nash_distance.nash_strategy == original.nash_distance.nash_strategy
