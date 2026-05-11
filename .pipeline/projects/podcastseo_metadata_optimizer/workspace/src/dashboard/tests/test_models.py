"""Tests for src.dashboard.models."""

import pytest
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


class TestWinRateMetric:
    def test_default_values(self):
        m = WinRateMetric()
        assert m.value == 0.0
        assert m.total_games == 0
        assert m.wins == 0
        assert m.losses == 0
        assert isinstance(m.timestamp, float)

    def test_custom_values(self):
        m = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25)
        assert m.value == 0.75
        assert m.total_games == 100
        assert m.wins == 75
        assert m.losses == 25

    def test_to_dict(self):
        m = WinRateMetric(value=0.8, total_games=50, wins=40, losses=10)
        d = m.to_dict()
        assert d["value"] == 0.8
        assert d["total_games"] == 50
        assert d["wins"] == 40
        assert d["losses"] == 10
        assert "timestamp" in d

    def test_from_dict(self):
        d = {"value": 0.9, "total_games": 200, "wins": 180, "losses": 20, "timestamp": 1234567890.0}
        m = WinRateMetric.from_dict(d)
        assert m.value == 0.9
        assert m.total_games == 200
        assert m.wins == 180
        assert m.losses == 20
        assert m.timestamp == 1234567890.0


class TestBankrollCurvePoint:
    def test_default_values(self):
        p = BankrollCurvePoint()
        assert p.step == 0
        assert p.bankroll == 0.0
        assert p.peak_bankroll == 0.0
        assert p.drawdown == 0.0
        assert p.history == []
        assert isinstance(p.timestamp, float)

    def test_custom_values(self):
        p = BankrollCurvePoint(step=5, bankroll=150.0, peak_bankroll=200.0, drawdown=-50.0)
        assert p.step == 5
        assert p.bankroll == 150.0
        assert p.peak_bankroll == 200.0
        assert p.drawdown == -50.0

    def test_to_dict(self):
        p = BankrollCurvePoint(step=10, bankroll=200.0, peak_bankroll=250.0, drawdown=-50.0)
        d = p.to_dict()
        assert d["step"] == 10
        assert d["bankroll"] == 200.0
        assert d["peak_bankroll"] == 250.0
        assert d["drawdown"] == -50.0
        assert "timestamp" in d

    def test_from_dict(self):
        d = {
            "step": 15,
            "bankroll": 300.0,
            "peak_bankroll": 350.0,
            "drawdown": -50.0,
            "timestamp": 1234567890.0,
            "history": [100, 150, 200],
        }
        p = BankrollCurvePoint.from_dict(d)
        assert p.step == 15
        assert p.bankroll == 300.0
        assert p.peak_bankroll == 350.0
        assert p.drawdown == -50.0
        assert p.timestamp == 1234567890.0
        assert p.history == [100, 150, 200]


class TestNashEquilibriumShift:
    def test_default_values(self):
        s = NashEquilibriumShift()
        assert s.distance == 0.0
        assert s.current_strategy == "unknown"
        assert s.nash_strategy == "nash_equilibrium"
        assert isinstance(s.timestamp, float)

    def test_custom_values(self):
        s = NashEquilibriumShift(distance=0.5, current_strategy="aggressive")
        assert s.distance == 0.5
        assert s.current_strategy == "aggressive"
        assert s.nash_strategy == "nash_equilibrium"

    def test_to_dict(self):
        s = NashEquilibriumShift(distance=0.3, current_strategy="conservative")
        d = s.to_dict()
        assert d["distance"] == 0.3
        assert d["current_strategy"] == "conservative"
        assert d["nash_strategy"] == "nash_equilibrium"
        assert "timestamp" in d

    def test_from_dict(self):
        d = {
            "distance": 0.4,
            "current_strategy": "balanced",
            "nash_strategy": "nash_equilibrium",
            "timestamp": 1234567890.0,
        }
        s = NashEquilibriumShift.from_dict(d)
        assert s.distance == 0.4
        assert s.current_strategy == "balanced"
        assert s.nash_strategy == "nash_equilibrium"
        assert s.timestamp == 1234567890.0


class TestDashboardState:
    def test_default_values(self):
        s = DashboardState()
        assert isinstance(s.win_rate, WinRateMetric)
        assert isinstance(s.bankroll, BankrollCurvePoint)
        assert isinstance(s.nash_distance, NashEquilibriumShift)
        assert isinstance(s.timestamp, float)

    def test_custom_values(self):
        wr = WinRateMetric(value=0.6, total_games=10, wins=6, losses=4)
        bc = BankrollCurvePoint(step=5, bankroll=100.0, peak_bankroll=120.0, drawdown=-20.0)
        ne = NashEquilibriumShift(distance=0.3, current_strategy="aggressive")
        s = DashboardState(win_rate=wr, bankroll=bc, nash_distance=ne)
        assert s.win_rate.value == 0.6
        assert s.bankroll.step == 5
        assert s.nash_distance.distance == 0.3

    def test_to_dict(self):
        s = DashboardState(
            win_rate=WinRateMetric(value=0.7, total_games=20, wins=14, losses=6),
            bankroll=BankrollCurvePoint(step=10, bankroll=150.0, peak_bankroll=180.0, drawdown=-30.0),
            nash_distance=NashEquilibriumShift(distance=0.4, current_strategy="balanced"),
        )
        d = s.to_dict()
        assert "win_rate" in d
        assert "bankroll" in d
        assert "nash_distance" in d
        assert "timestamp" in d
        assert d["win_rate"]["value"] == 0.7
        assert d["bankroll"]["step"] == 10
        assert d["nash_distance"]["distance"] == 0.4

    def test_from_dict(self):
        d = {
            "win_rate": {"value": 0.8, "total_games": 50, "wins": 40, "losses": 10, "timestamp": 1234567890.0},
            "bankroll": {"step": 20, "bankroll": 200.0, "peak_bankroll": 250.0, "drawdown": -50.0, "timestamp": 1234567890.0, "history": [100, 150, 200]},
            "nash_distance": {"distance": 0.5, "current_strategy": "aggressive", "nash_strategy": "nash_equilibrium", "timestamp": 1234567890.0},
            "timestamp": 1234567890.0,
        }
        s = DashboardState.from_dict(d)
        assert s.win_rate.value == 0.8
        assert s.bankroll.step == 20
        assert s.nash_distance.distance == 0.5
        assert s.timestamp == 1234567890.0
