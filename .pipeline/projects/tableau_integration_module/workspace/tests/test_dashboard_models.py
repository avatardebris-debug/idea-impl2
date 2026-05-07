"""Tests for dashboard data model classes.

Covers:
  - WinRateMetric creation and serialization
  - BankrollCurvePoint creation and serialization
  - NashEquilibriumShift creation and serialization
  - DashboardState creation and serialization
  - Round-trip serialization (to_dict → from_dict)
"""

import time

import pytest

from src.dashboard.models import (
    BankrollCurvePoint,
    DashboardState,
    NashEquilibriumShift,
    WinRateMetric,
)


# ===== WinRateMetric =====

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

    def test_to_dict_roundtrip(self):
        m = WinRateMetric(value=0.6, total_games=50, wins=30, losses=20, timestamp=1234567.89)
        d = m.to_dict()
        m2 = WinRateMetric.from_dict(d)
        assert m2.value == m.value
        assert m2.total_games == m.total_games
        assert m2.wins == m.wins
        assert m2.losses == m.losses
        assert m2.timestamp == m.timestamp

    def test_from_dict_missing_timestamp(self):
        d = {"value": 0.5, "total_games": 10, "wins": 5, "losses": 5}
        m = WinRateMetric.from_dict(d)
        assert m.value == 0.5
        assert isinstance(m.timestamp, float)

    def test_from_dict_type_coercion(self):
        d = {"value": "0.8", "total_games": "20", "wins": "16", "losses": "4", "timestamp": "100.0"}
        m = WinRateMetric.from_dict(d)
        assert m.value == 0.8
        assert m.total_games == 20
        assert m.wins == 16
        assert m.losses == 4
        assert m.timestamp == 100.0


# ===== BankrollCurvePoint =====

class TestBankrollCurvePoint:
    def test_default_values(self):
        p = BankrollCurvePoint()
        assert p.step == 0
        assert p.bankroll == 0.0
        assert p.peak_bankroll == 0.0
        assert p.drawdown == 0.0
        assert isinstance(p.timestamp, float)

    def test_custom_values(self):
        p = BankrollCurvePoint(step=5, bankroll=1100.0, peak_bankroll=1200.0, drawdown=-0.0833)
        assert p.step == 5
        assert p.bankroll == 1100.0
        assert p.peak_bankroll == 1200.0
        assert p.drawdown == -0.0833

    def test_to_dict_roundtrip(self):
        p = BankrollCurvePoint(step=10, bankroll=950.0, peak_bankroll=1000.0, drawdown=-0.05, timestamp=999999.0)
        d = p.to_dict()
        p2 = BankrollCurvePoint.from_dict(d)
        assert p2.step == p.step
        assert p2.bankroll == p.bankroll
        assert p2.peak_bankroll == p.peak_bankroll
        assert p2.drawdown == p.drawdown
        assert p2.timestamp == p.timestamp

    def test_from_dict_missing_timestamp(self):
        d = {"step": 1, "bankroll": 100.0, "peak_bankroll": 100.0, "drawdown": 0.0}
        p = BankrollCurvePoint.from_dict(d)
        assert p.step == 1
        assert isinstance(p.timestamp, float)


# ===== NashEquilibriumShift =====

class TestNashEquilibriumShift:
    def test_default_values(self):
        n = NashEquilibriumShift()
        assert n.distance == 0.0
        assert n.current_strategy == "unknown"
        assert n.nash_strategy == "nash_equilibrium"
        assert isinstance(n.timestamp, float)

    def test_custom_values(self):
        n = NashEquilibriumShift(distance=0.25, current_strategy="greedy", nash_strategy="nash")
        assert n.distance == 0.25
        assert n.current_strategy == "greedy"
        assert n.nash_strategy == "nash"

    def test_to_dict_roundtrip(self):
        n = NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=55555.0)
        d = n.to_dict()
        n2 = NashEquilibriumShift.from_dict(d)
        assert n2.distance == n.distance
        assert n2.current_strategy == n.current_strategy
        assert n2.nash_strategy == n.nash_strategy
        assert n2.timestamp == n.timestamp

    def test_from_dict_missing_timestamp(self):
        d = {"distance": 0.5, "current_strategy": "test", "nash_strategy": "nash"}
        n = NashEquilibriumShift.from_dict(d)
        assert n.distance == 0.5
        assert isinstance(n.timestamp, float)


# ===== DashboardState =====

class TestDashboardState:
    def test_default_values(self):
        s = DashboardState()
        assert isinstance(s.win_rate, WinRateMetric)
        assert isinstance(s.bankroll, BankrollCurvePoint)
        assert isinstance(s.nash_shift, NashEquilibriumShift)
        assert isinstance(s.timestamp, float)

    def test_custom_values(self):
        wr = WinRateMetric(value=0.6, total_games=10, wins=6, losses=4)
        bk = BankrollCurvePoint(step=1, bankroll=1000.0, peak_bankroll=1000.0, drawdown=0.0)
        ns = NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash")
        s = DashboardState(win_rate=wr, bankroll=bk, nash_shift=ns, timestamp=77777.0)
        assert s.win_rate.value == 0.6
        assert s.bankroll.step == 1
        assert s.nash_shift.distance == 0.1
        assert s.timestamp == 77777.0

    def test_to_dict_roundtrip(self):
        wr = WinRateMetric(value=0.55, total_games=20, wins=11, losses=9, timestamp=11111.0)
        bk = BankrollCurvePoint(step=2, bankroll=1050.0, peak_bankroll=1050.0, drawdown=0.0, timestamp=11111.0)
        ns = NashEquilibriumShift(distance=0.15, current_strategy="s2", nash_strategy="nash", timestamp=11111.0)
        s = DashboardState(win_rate=wr, bankroll=bk, nash_shift=ns, timestamp=22222.0)
        d = s.to_dict()
        s2 = DashboardState.from_dict(d)
        assert s2.win_rate.value == s.win_rate.value
        assert s2.bankroll.step == s.bankroll.step
        assert s2.nash_shift.distance == s.nash_shift.distance
        assert s2.timestamp == s.timestamp

    def test_to_dict_structure(self):
        s = DashboardState()
        d = s.to_dict()
        assert "win_rate" in d
        assert "bankroll" in d
        assert "nash_shift" in d
        assert "timestamp" in d
        assert isinstance(d["win_rate"], dict)
        assert isinstance(d["bankroll"], dict)
        assert isinstance(d["nash_shift"], dict)


# ===== Cross-model integration =====

class TestCrossModelIntegration:
    def test_dashboard_state_from_nested_dict(self):
        """Ensure DashboardState.from_dict correctly deserializes nested dicts."""
        d = {
            "win_rate": {"value": 0.7, "total_games": 100, "wins": 70, "losses": 30, "timestamp": 1000.0},
            "bankroll": {"step": 50, "bankroll": 1500.0, "peak_bankroll": 1600.0, "drawdown": -0.0625, "timestamp": 1000.0},
            "nash_shift": {"distance": 0.2, "current_strategy": "test", "nash_strategy": "nash", "timestamp": 1000.0},
            "timestamp": 2000.0,
        }
        s = DashboardState.from_dict(d)
        assert s.win_rate.value == 0.7
        assert s.bankroll.bankroll == 1500.0
        assert s.nash_shift.distance == 0.2
        assert s.timestamp == 2000.0

    def test_all_models_have_to_dict_and_from_dict(self):
        """All four models must have to_dict and from_dict methods."""
        for cls in [WinRateMetric, BankrollCurvePoint, NashEquilibriumShift, DashboardState]:
            assert hasattr(cls, "to_dict")
            assert hasattr(cls, "from_dict")
            obj = cls()
            d = obj.to_dict()
            obj2 = cls.from_dict(d)
            assert obj2 is not None
