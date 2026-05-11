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

class TestWinRateMetric:
    def test_default_values(self):
        wr = WinRateMetric()
        assert wr.value == 0.0
        assert wr.total_games == 0
        assert wr.wins == 0
        assert wr.losses == 0
        assert isinstance(wr.timestamp, float)

    def test_custom_values(self):
        wr = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25)
        assert wr.value == 0.75
        assert wr.total_games == 100
        assert wr.wins == 75
        assert wr.losses == 25

    def test_to_dict(self):
        wr = WinRateMetric(value=0.5, total_games=10, wins=5, losses=5)
        d = wr.to_dict()
        assert d["value"] == 0.5
        assert d["total_games"] == 10
        assert d["wins"] == 5
        assert d["losses"] == 5
        assert "timestamp" in d

    def test_from_dict(self):
        data = {
            "value": 0.6,
            "total_games": 20,
            "wins": 12,
            "losses": 8,
            "timestamp": 1000.0,
        }
        wr = WinRateMetric.from_dict(data)
        assert wr.value == 0.6
        assert wr.total_games == 20
        assert wr.wins == 12
        assert wr.losses == 8
        assert wr.timestamp == 1000.0

    def test_roundtrip(self):
        wr = WinRateMetric(value=0.8, total_games=50, wins=40, losses=10)
        d = wr.to_dict()
        wr2 = WinRateMetric.from_dict(d)
        assert wr2.value == wr.value
        assert wr2.total_games == wr.total_games
        assert wr2.wins == wr.wins
        assert wr2.losses == wr.losses


# ===== BankrollCurvePoint =====

class TestBankrollCurvePoint:
    def test_default_values(self):
        bp = BankrollCurvePoint()
        assert bp.step == 0
        assert bp.bankroll == 0.0
        assert bp.peak_bankroll == 0.0
        assert bp.drawdown == 0.0
        assert bp.history == []

    def test_custom_values(self):
        bp = BankrollCurvePoint(step=5, bankroll=150.0, peak_bankroll=200.0, drawdown=-50.0)
        assert bp.step == 5
        assert bp.bankroll == 150.0
        assert bp.peak_bankroll == 200.0
        assert bp.drawdown == -50.0

    def test_to_dict(self):
        bp = BankrollCurvePoint(step=10, bankroll=100.0, peak_bankroll=120.0, drawdown=-20.0, history=[100, 110, 120])
        d = bp.to_dict()
        assert d["step"] == 10
        assert d["bankroll"] == 100.0
        assert d["peak_bankroll"] == 120.0
        assert d["drawdown"] == -20.0
        assert d["history"] == [100, 110, 120]

    def test_from_dict(self):
        data = {
            "step": 3,
            "bankroll": 80.0,
            "peak_bankroll": 100.0,
            "drawdown": -20.0,
            "history": [70, 80, 90, 100],
        }
        bp = BankrollCurvePoint.from_dict(data)
        assert bp.step == 3
        assert bp.bankroll == 80.0
        assert bp.peak_bankroll == 100.0
        assert bp.drawdown == -20.0
        assert bp.history == [70, 80, 90, 100]

    def test_roundtrip(self):
        bp = BankrollCurvePoint(step=7, bankroll=90.0, peak_bankroll=100.0, drawdown=-10.0, history=[80, 90])
        d = bp.to_dict()
        bp2 = BankrollCurvePoint.from_dict(d)
        assert bp2.step == bp.step
        assert bp2.bankroll == bp.bankroll
        assert bp2.peak_bankroll == bp.peak_bankroll
        assert bp2.drawdown == bp.drawdown
        assert bp2.history == bp.history


# ===== NashEquilibriumShift =====

class TestNashEquilibriumShift:
    def test_default_values(self):
        nes = NashEquilibriumShift()
        assert nes.distance == 0.0
        assert nes.current_strategy == "unknown"
        assert nes.nash_strategy == "nash_equilibrium"

    def test_custom_values(self):
        nes = NashEquilibriumShift(distance=0.5, current_strategy="aggressive")
        assert nes.distance == 0.5
        assert nes.current_strategy == "aggressive"
        assert nes.nash_strategy == "nash_equilibrium"

    def test_to_dict(self):
        nes = NashEquilibriumShift(distance=0.3, current_strategy="defensive")
        d = nes.to_dict()
        assert d["distance"] == 0.3
        assert d["current_strategy"] == "defensive"
        assert d["nash_strategy"] == "nash_equilibrium"

    def test_from_dict(self):
        data = {
            "distance": 0.4,
            "current_strategy": "bluff",
            "nash_strategy": "nash_equilibrium",
        }
        nes = NashEquilibriumShift.from_dict(data)
        assert nes.distance == 0.4
        assert nes.current_strategy == "bluff"
        assert nes.nash_strategy == "nash_equilibrium"

    def test_roundtrip(self):
        nes = NashEquilibriumShift(distance=0.25, current_strategy="balanced")
        d = nes.to_dict()
        nes2 = NashEquilibriumShift.from_dict(d)
        assert nes2.distance == nes.distance
        assert nes2.current_strategy == nes.current_strategy
        assert nes2.nash_strategy == nes.nash_strategy


# ===== DashboardState =====

class TestDashboardState:
    def test_default_values(self):
        ds = DashboardState()
        assert isinstance(ds.win_rate, WinRateMetric)
        assert isinstance(ds.bankroll, BankrollCurvePoint)
        assert isinstance(ds.nash_distance, NashEquilibriumShift)
        assert isinstance(ds.timestamp, float)

    def test_custom_values(self):
        wr = WinRateMetric(value=0.6, total_games=10, wins=6, losses=4)
        bp = BankrollCurvePoint(step=5, bankroll=100.0, peak_bankroll=120.0, drawdown=-20.0)
        nes = NashEquilibriumShift(distance=0.3, current_strategy="aggressive")
        ds = DashboardState(win_rate=wr, bankroll=bp, nash_distance=nes)
        assert ds.win_rate.value == 0.6
        assert ds.bankroll.step == 5
        assert ds.nash_distance.distance == 0.3

    def test_to_dict(self):
        ds = DashboardState()
        d = ds.to_dict()
        assert "win_rate" in d
        assert "bankroll" in d
        assert "nash_distance" in d
        assert "timestamp" in d

    def test_from_dict(self):
        ds = DashboardState(
            win_rate=WinRateMetric(value=0.7, total_games=20, wins=14, losses=6),
            bankroll=BankrollCurvePoint(step=10, bankroll=150.0, peak_bankroll=180.0, drawdown=-30.0),
            nash_distance=NashEquilibriumShift(distance=0.4, current_strategy="defensive"),
        )
        d = ds.to_dict()
        ds2 = DashboardState.from_dict(d)
        assert ds2.win_rate.value == 0.7
        assert ds2.bankroll.step == 10
        assert ds2.nash_distance.distance == 0.4

    def test_roundtrip(self):
        ds = DashboardState(
            win_rate=WinRateMetric(value=0.55, total_games=100, wins=55, losses=45),
            bankroll=BankrollCurvePoint(step=50, bankroll=200.0, peak_bankroll=250.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.15, current_strategy="balanced"),
        )
        d = ds.to_dict()
        ds2 = DashboardState.from_dict(d)
        assert ds2.win_rate.value == ds.win_rate.value
        assert ds2.bankroll.step == ds.bankroll.step
        assert ds2.nash_distance.distance == ds.nash_distance.distance
