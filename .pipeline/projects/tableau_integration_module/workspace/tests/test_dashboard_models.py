"""Tests for src.dashboard.models."""

import time
import pytest
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


# ===== WinRateMetric =====

class TestWinRateMetricInit:
    def test_default_values(self):
        wr = WinRateMetric()
        assert wr.value == 0.0
        assert wr.total_games == 0
        assert wr.wins == 0
        assert wr.losses == 0
        assert isinstance(wr.timestamp, float)

    def test_custom_values(self):
        wr = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=1234.0)
        assert wr.value == 0.75
        assert wr.total_games == 100
        assert wr.wins == 75
        assert wr.losses == 25
        assert wr.timestamp == 1234.0


class TestWinRateMetricToDict:
    def test_to_dict_default(self):
        wr = WinRateMetric()
        d = wr.to_dict()
        assert d["value"] == 0.0
        assert d["total_games"] == 0
        assert d["wins"] == 0
        assert d["losses"] == 0
        assert isinstance(d["timestamp"], float)

    def test_to_dict_custom(self):
        wr = WinRateMetric(value=0.8, total_games=50, wins=40, losses=10, timestamp=999.0)
        d = wr.to_dict()
        assert d["value"] == 0.8
        assert d["total_games"] == 50
        assert d["wins"] == 40
        assert d["losses"] == 10
        assert d["timestamp"] == 999.0


class TestWinRateMetricFromDict:
    def test_from_dict_default(self):
        d = {}
        wr = WinRateMetric.from_dict(d)
        assert wr.value == 0.0
        assert wr.total_games == 0
        assert wr.wins == 0
        assert wr.losses == 0
        assert isinstance(wr.timestamp, float)

    def test_from_dict_custom(self):
        d = {
            "value": 0.9,
            "total_games": 200,
            "wins": 180,
            "losses": 20,
            "timestamp": 5000.0,
        }
        wr = WinRateMetric.from_dict(d)
        assert wr.value == 0.9
        assert wr.total_games == 200
        assert wr.wins == 180
        assert wr.losses == 20
        assert wr.timestamp == 5000.0

    def test_from_dict_partial(self):
        d = {"value": 0.5}
        wr = WinRateMetric.from_dict(d)
        assert wr.value == 0.5
        assert wr.total_games == 0
        assert wr.wins == 0
        assert wr.losses == 0

    def test_roundtrip(self):
        wr = WinRateMetric(value=0.65, total_games=30, wins=20, losses=10, timestamp=777.0)
        d = wr.to_dict()
        wr2 = WinRateMetric.from_dict(d)
        assert wr2.value == wr.value
        assert wr2.total_games == wr.total_games
        assert wr2.wins == wr.wins
        assert wr2.losses == wr.losses
        assert wr2.timestamp == wr.timestamp


# ===== BankrollCurvePoint =====

class TestBankrollCurvePointInit:
    def test_default_values(self):
        bp = BankrollCurvePoint()
        assert bp.step == 0
        assert bp.bankroll == 0.0
        assert bp.peak_bankroll == 0.0
        assert bp.drawdown == 0.0
        assert bp.history == []
        assert isinstance(bp.timestamp, float)

    def test_custom_values(self):
        bp = BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1200, 1500], timestamp=888.0)
        assert bp.step == 5
        assert bp.bankroll == 1500.0
        assert bp.peak_bankroll == 2000.0
        assert bp.drawdown == -500.0
        assert bp.history == [1000, 1200, 1500]
        assert bp.timestamp == 888.0


class TestBankrollCurvePointToDict:
    def test_to_dict_default(self):
        bp = BankrollCurvePoint()
        d = bp.to_dict()
        assert d["step"] == 0
        assert d["bankroll"] == 0.0
        assert d["peak_bankroll"] == 0.0
        assert d["drawdown"] == 0.0
        assert d["history"] == []
        assert isinstance(d["timestamp"], float)

    def test_to_dict_custom(self):
        bp = BankrollCurvePoint(step=10, bankroll=2000.0, peak_bankroll=2500.0, drawdown=-500.0, history=[1000, 1500, 2000], timestamp=100.0)
        d = bp.to_dict()
        assert d["step"] == 10
        assert d["bankroll"] == 2000.0
        assert d["peak_bankroll"] == 2500.0
        assert d["drawdown"] == -500.0
        assert d["history"] == [1000, 1500, 2000]
        assert d["timestamp"] == 100.0


class TestBankrollCurvePointFromDict:
    def test_from_dict_default(self):
        d = {}
        bp = BankrollCurvePoint.from_dict(d)
        assert bp.step == 0
        assert bp.bankroll == 0.0
        assert bp.peak_bankroll == 0.0
        assert bp.drawdown == 0.0
        assert bp.history == []

    def test_from_dict_custom(self):
        d = {
            "step": 7,
            "bankroll": 1800.0,
            "peak_bankroll": 2200.0,
            "drawdown": -400.0,
            "history": [1000, 1600, 1800],
            "timestamp": 300.0,
        }
        bp = BankrollCurvePoint.from_dict(d)
        assert bp.step == 7
        assert bp.bankroll == 1800.0
        assert bp.peak_bankroll == 2200.0
        assert bp.drawdown == -400.0
        assert bp.history == [1000, 1600, 1800]
        assert bp.timestamp == 300.0

    def test_from_dict_partial(self):
        d = {"bankroll": 500.0}
        bp = BankrollCurvePoint.from_dict(d)
        assert bp.bankroll == 500.0
        assert bp.step == 0
        assert bp.peak_bankroll == 0.0

    def test_roundtrip(self):
        bp = BankrollCurvePoint(step=3, bankroll=1200.0, peak_bankroll=1500.0, drawdown=-300.0, history=[1000, 1100, 1200], timestamp=42.0)
        d = bp.to_dict()
        bp2 = BankrollCurvePoint.from_dict(d)
        assert bp2.step == bp.step
        assert bp2.bankroll == bp.bankroll
        assert bp2.peak_bankroll == bp.peak_bankroll
        assert bp2.drawdown == bp.drawdown
        assert bp2.history == bp.history
        assert bp2.timestamp == bp.timestamp


# ===== NashEquilibriumShift =====

class TestNashEquilibriumShiftInit:
    def test_default_values(self):
        ne = NashEquilibriumShift()
        assert ne.distance == 0.0
        assert ne.current_strategy == "unknown"
        assert ne.nash_strategy == "nash_equilibrium"
        assert isinstance(ne.timestamp, float)

    def test_custom_values(self):
        ne = NashEquilibriumShift(distance=0.25, current_strategy="aggressive", nash_strategy="nash_balanced", timestamp=777.0)
        assert ne.distance == 0.25
        assert ne.current_strategy == "aggressive"
        assert ne.nash_strategy == "nash_balanced"
        assert ne.timestamp == 777.0


class TestNashEquilibriumShiftToDict:
    def test_to_dict_default(self):
        ne = NashEquilibriumShift()
        d = ne.to_dict()
        assert d["distance"] == 0.0
        assert d["current_strategy"] == "unknown"
        assert d["nash_strategy"] == "nash_equilibrium"
        assert isinstance(d["timestamp"], float)

    def test_to_dict_custom(self):
        ne = NashEquilibriumShift(distance=0.5, current_strategy="defensive", nash_strategy="nash_optimal", timestamp=100.0)
        d = ne.to_dict()
        assert d["distance"] == 0.5
        assert d["current_strategy"] == "defensive"
        assert d["nash_strategy"] == "nash_optimal"
        assert d["timestamp"] == 100.0


class TestNashEquilibriumShiftFromDict:
    def test_from_dict_default(self):
        d = {}
        ne = NashEquilibriumShift.from_dict(d)
        assert ne.distance == 0.0
        assert ne.current_strategy == "unknown"
        assert ne.nash_strategy == "nash_equilibrium"

    def test_from_dict_custom(self):
        d = {
            "distance": 0.3,
            "current_strategy": "mixed",
            "nash_strategy": "nash_core",
            "timestamp": 200.0,
        }
        ne = NashEquilibriumShift.from_dict(d)
        assert ne.distance == 0.3
        assert ne.current_strategy == "mixed"
        assert ne.nash_strategy == "nash_core"
        assert ne.timestamp == 200.0

    def test_from_dict_partial(self):
        d = {"distance": 0.1}
        ne = NashEquilibriumShift.from_dict(d)
        assert ne.distance == 0.1
        assert ne.current_strategy == "unknown"
        assert ne.nash_strategy == "nash_equilibrium"

    def test_roundtrip(self):
        ne = NashEquilibriumShift(distance=0.4, current_strategy="random", nash_strategy="nash_final", timestamp=555.0)
        d = ne.to_dict()
        ne2 = NashEquilibriumShift.from_dict(d)
        assert ne2.distance == ne.distance
        assert ne2.current_strategy == ne.current_strategy
        assert ne2.nash_strategy == ne.nash_strategy
        assert ne2.timestamp == ne.timestamp


# ===== DashboardState =====

class TestDashboardStateInit:
    def test_default_values(self):
        ds = DashboardState()
        assert isinstance(ds.win_rate, WinRateMetric)
        assert isinstance(ds.bankroll, BankrollCurvePoint)
        assert isinstance(ds.nash_distance, NashEquilibriumShift)
        assert isinstance(ds.timestamp, float)

    def test_custom_values(self):
        wr = WinRateMetric(value=0.8)
        bp = BankrollCurvePoint(step=1, bankroll=1000.0)
        ne = NashEquilibriumShift(distance=0.01)
        ds = DashboardState(win_rate=wr, bankroll=bp, nash_distance=ne, timestamp=999.0)
        assert ds.win_rate.value == 0.8
        assert ds.bankroll.step == 1
        assert ds.nash_distance.distance == 0.01
        assert ds.timestamp == 999.0


class TestDashboardStateToDict:
    def test_to_dict_default(self):
        ds = DashboardState()
        d = ds.to_dict()
        assert "win_rate" in d
        assert "bankroll" in d
        assert "nash_distance" in d
        assert "timestamp" in d
        assert isinstance(d["win_rate"], dict)
        assert isinstance(d["bankroll"], dict)
        assert isinstance(d["nash_distance"], dict)
        assert isinstance(d["timestamp"], float)

    def test_to_dict_custom(self):
        ds = DashboardState(
            win_rate=WinRateMetric(value=0.9, total_games=100, wins=90, losses=10, timestamp=10.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=2000.0, peak_bankroll=2500.0, drawdown=-500.0, history=[1000, 1500, 2000], timestamp=20.0),
            nash_distance=NashEquilibriumShift(distance=0.05, current_strategy="test", nash_strategy="nash", timestamp=30.0),
            timestamp=40.0,
        )
        d = ds.to_dict()
        assert d["win_rate"]["value"] == 0.9
        assert d["bankroll"]["step"] == 5
        assert d["nash_distance"]["distance"] == 0.05
        assert d["timestamp"] == 40.0


class TestDashboardStateFromDict:
    def test_from_dict_default(self):
        d = {}
        ds = DashboardState.from_dict(d)
        assert isinstance(ds.win_rate, WinRateMetric)
        assert isinstance(ds.bankroll, BankrollCurvePoint)
        assert isinstance(ds.nash_distance, NashEquilibriumShift)
        assert isinstance(ds.timestamp, float)

    def test_from_dict_custom(self):
        d = {
            "win_rate": {"value": 0.7, "total_games": 50, "wins": 35, "losses": 15, "timestamp": 1.0},
            "bankroll": {"step": 2, "bankroll": 1500.0, "peak_bankroll": 1800.0, "drawdown": -300.0, "history": [1000, 1200, 1500], "timestamp": 2.0},
            "nash_distance": {"distance": 0.1, "current_strategy": "a", "nash_strategy": "b", "timestamp": 3.0},
            "timestamp": 4.0,
        }
        ds = DashboardState.from_dict(d)
        assert ds.win_rate.value == 0.7
        assert ds.bankroll.step == 2
        assert ds.nash_distance.distance == 0.1
        assert ds.timestamp == 4.0

    def test_from_dict_partial(self):
        d = {"win_rate": {"value": 0.5}}
        ds = DashboardState.from_dict(d)
        assert ds.win_rate.value == 0.5
        assert ds.bankroll.step == 0
        assert ds.nash_distance.distance == 0.0

    def test_roundtrip(self):
        ds = DashboardState(
            win_rate=WinRateMetric(value=0.85, total_games=60, wins=51, losses=9, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=10, bankroll=3000.0, peak_bankroll=3500.0, drawdown=-500.0, history=[2000, 2500, 3000], timestamp=200.0),
            nash_distance=NashEquilibriumShift(distance=0.02, current_strategy="optimal", nash_strategy="nash_eq", timestamp=300.0),
            timestamp=400.0,
        )
        d = ds.to_dict()
        ds2 = DashboardState.from_dict(d)
        assert ds2.win_rate.value == ds.win_rate.value
        assert ds2.bankroll.step == ds.bankroll.step
        assert ds2.nash_distance.distance == ds.nash_distance.distance
        assert ds2.timestamp == ds.timestamp
