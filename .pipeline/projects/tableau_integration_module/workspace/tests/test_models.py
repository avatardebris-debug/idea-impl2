"""Tests for dashboard models."""

import time
import pytest
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


class TestWinRateMetric:
    """Tests for WinRateMetric."""

    def test_default_values(self):
        """Test default values are correct."""
        metric = WinRateMetric()
        assert metric.value == 0.0
        assert metric.total_games == 0
        assert metric.wins == 0
        assert metric.losses == 0
        assert isinstance(metric.timestamp, float)

    def test_to_dict(self):
        """Test serialization to dict."""
        metric = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=1234567890.0)
        d = metric.to_dict()
        assert d["value"] == 0.75
        assert d["total_games"] == 100
        assert d["wins"] == 75
        assert d["losses"] == 25
        assert d["timestamp"] == 1234567890.0

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "value": 0.8,
            "total_games": 200,
            "wins": 160,
            "losses": 40,
            "timestamp": 9876543210.0,
        }
        metric = WinRateMetric.from_dict(data)
        assert metric.value == 0.8
        assert metric.total_games == 200
        assert metric.wins == 160
        assert metric.losses == 40
        assert metric.timestamp == 9876543210.0

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {}
        metric = WinRateMetric.from_dict(data)
        assert metric.value == 0.0
        assert metric.total_games == 0
        assert metric.wins == 0
        assert metric.losses == 0

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = WinRateMetric(value=0.65, total_games=50, wins=32, losses=18, timestamp=1111111111.0)
        d = original.to_dict()
        restored = WinRateMetric.from_dict(d)
        assert restored.value == original.value
        assert restored.total_games == original.total_games
        assert restored.wins == original.wins
        assert restored.losses == original.losses
        assert restored.timestamp == original.timestamp


class TestBankrollCurvePoint:
    """Tests for BankrollCurvePoint."""

    def test_default_values(self):
        """Test default values are correct."""
        point = BankrollCurvePoint()
        assert point.step == 0
        assert point.bankroll == 0.0
        assert point.peak_bankroll == 0.0
        assert point.drawdown == 0.0
        assert point.history == []
        assert isinstance(point.timestamp, float)

    def test_to_dict(self):
        """Test serialization to dict."""
        point = BankrollCurvePoint(
            step=5,
            bankroll=1500.0,
            peak_bankroll=1600.0,
            drawdown=-100.0,
            history=[1000.0, 1100.0, 1200.0, 1300.0, 1500.0],
            timestamp=1234567890.0,
        )
        d = point.to_dict()
        assert d["step"] == 5
        assert d["bankroll"] == 1500.0
        assert d["peak_bankroll"] == 1600.0
        assert d["drawdown"] == -100.0
        assert d["history"] == [1000.0, 1100.0, 1200.0, 1300.0, 1500.0]
        assert d["timestamp"] == 1234567890.0

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "step": 10,
            "bankroll": 2000.0,
            "peak_bankroll": 2500.0,
            "drawdown": -500.0,
            "history": [1000.0, 2000.0],
            "timestamp": 9876543210.0,
        }
        point = BankrollCurvePoint.from_dict(data)
        assert point.step == 10
        assert point.bankroll == 2000.0
        assert point.peak_bankroll == 2500.0
        assert point.drawdown == -500.0
        assert point.history == [1000.0, 2000.0]
        assert point.timestamp == 9876543210.0

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {}
        point = BankrollCurvePoint.from_dict(data)
        assert point.step == 0
        assert point.bankroll == 0.0
        assert point.history == []

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = BankrollCurvePoint(
            step=3,
            bankroll=1200.0,
            peak_bankroll=1300.0,
            drawdown=-100.0,
            history=[1000.0, 1100.0, 1200.0],
            timestamp=1111111111.0,
        )
        d = original.to_dict()
        restored = BankrollCurvePoint.from_dict(d)
        assert restored.step == original.step
        assert restored.bankroll == original.bankroll
        assert restored.peak_bankroll == original.peak_bankroll
        assert restored.drawdown == original.drawdown
        assert restored.history == original.history
        assert restored.timestamp == original.timestamp


class TestNashEquilibriumShift:
    """Tests for NashEquilibriumShift."""

    def test_default_values(self):
        """Test default values are correct."""
        shift = NashEquilibriumShift()
        assert shift.distance == 0.0
        assert shift.current_strategy == "unknown"
        assert shift.nash_strategy == "nash_equilibrium"
        assert isinstance(shift.timestamp, float)

    def test_to_dict(self):
        """Test serialization to dict."""
        shift = NashEquilibriumShift(
            distance=0.12,
            current_strategy="bluff",
            nash_strategy="nash_equilibrium",
            timestamp=1234567890.0,
        )
        d = shift.to_dict()
        assert d["distance"] == 0.12
        assert d["current_strategy"] == "bluff"
        assert d["nash_strategy"] == "nash_equilibrium"
        assert d["timestamp"] == 1234567890.0

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "distance": 0.25,
            "current_strategy": "call",
            "nash_strategy": "nash_equilibrium",
            "timestamp": 9876543210.0,
        }
        shift = NashEquilibriumShift.from_dict(data)
        assert shift.distance == 0.25
        assert shift.current_strategy == "call"
        assert shift.nash_strategy == "nash_equilibrium"
        assert shift.timestamp == 9876543210.0

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {}
        shift = NashEquilibriumShift.from_dict(data)
        assert shift.distance == 0.0
        assert shift.current_strategy == "unknown"
        assert shift.nash_strategy == "nash_equilibrium"

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = NashEquilibriumShift(
            distance=0.08,
            current_strategy="fold",
            nash_strategy="nash_equilibrium",
            timestamp=1111111111.0,
        )
        d = original.to_dict()
        restored = NashEquilibriumShift.from_dict(d)
        assert restored.distance == original.distance
        assert restored.current_strategy == original.current_strategy
        assert restored.nash_strategy == original.nash_strategy
        assert restored.timestamp == original.timestamp


class TestDashboardState:
    """Tests for DashboardState."""

    def test_default_values(self):
        """Test default values are correct."""
        state = DashboardState()
        assert isinstance(state.win_rate, WinRateMetric)
        assert isinstance(state.bankroll, BankrollCurvePoint)
        assert isinstance(state.nash_distance, NashEquilibriumShift)
        assert isinstance(state.timestamp, float)

    def test_to_dict(self):
        """Test serialization to dict."""
        state = DashboardState(
            win_rate=WinRateMetric(value=0.7, total_games=10, wins=7, losses=3, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=1234567890.0,
        )
        d = state.to_dict()
        assert "win_rate" in d
        assert "bankroll" in d
        assert "nash_distance" in d
        assert "timestamp" in d
        assert d["timestamp"] == 1234567890.0
        assert d["win_rate"]["value"] == 0.7
        assert d["bankroll"]["bankroll"] == 1500.0
        assert d["nash_distance"]["distance"] == 0.1

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "win_rate": {"value": 0.8, "total_games": 20, "wins": 16, "losses": 4, "timestamp": 200.0},
            "bankroll": {"step": 10, "bankroll": 2000.0, "peak_bankroll": 2200.0, "drawdown": -200.0, "history": [1000.0, 2000.0], "timestamp": 200.0},
            "nash_distance": {"distance": 0.15, "current_strategy": "call", "nash_strategy": "nash_equilibrium", "timestamp": 200.0},
            "timestamp": 9876543210.0,
        }
        state = DashboardState.from_dict(data)
        assert state.win_rate.value == 0.8
        assert state.bankroll.bankroll == 2000.0
        assert state.nash_distance.distance == 0.15
        assert state.timestamp == 9876543210.0

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {}
        state = DashboardState.from_dict(data)
        assert state.win_rate.value == 0.0
        assert state.bankroll.bankroll == 0.0
        assert state.nash_distance.distance == 0.0

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=30, wins=18, losses=12, timestamp=300.0),
            bankroll=BankrollCurvePoint(step=15, bankroll=1800.0, peak_bankroll=2000.0, drawdown=-200.0, history=[1000.0, 1800.0], timestamp=300.0),
            nash_distance=NashEquilibriumShift(distance=0.05, current_strategy="fold", nash_strategy="nash_equilibrium", timestamp=300.0),
            timestamp=1111111111.0,
        )
        d = original.to_dict()
        restored = DashboardState.from_dict(d)
        assert restored.win_rate.value == original.win_rate.value
        assert restored.bankroll.bankroll == original.bankroll.bankroll
        assert restored.nash_distance.distance == original.nash_distance.distance
        assert restored.timestamp == original.timestamp

    def test_nested_objects_preserved(self):
        """Test that nested objects are preserved through roundtrip."""
        original = DashboardState(
            win_rate=WinRateMetric(value=0.55, total_games=100, wins=55, losses=45, timestamp=400.0),
            bankroll=BankrollCurvePoint(step=20, bankroll=2500.0, peak_bankroll=2800.0, drawdown=-300.0, history=[1000.0, 2000.0, 2500.0], timestamp=400.0),
            nash_distance=NashEquilibriumShift(distance=0.2, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=400.0),
            timestamp=1111111111.0,
        )
        d = original.to_dict()
        restored = DashboardState.from_dict(d)
        assert restored.win_rate.total_games == original.win_rate.total_games
        assert restored.win_rate.wins == original.win_rate.wins
        assert restored.win_rate.losses == original.win_rate.losses
        assert restored.bankroll.step == original.bankroll.step
        assert restored.bankroll.peak_bankroll == original.bankroll.peak_bankroll
        assert restored.bankroll.drawdown == original.bankroll.drawdown
        assert restored.bankroll.history == original.bankroll.history
        assert restored.nash_distance.current_strategy == original.nash_distance.current_strategy
        assert restored.nash_distance.nash_strategy == original.nash_distance.nash_strategy
