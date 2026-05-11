"""Tests for src.dashboard.panels."""

import pytest
from src.dashboard.panels import (
    DashboardPanel,
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
)


# ===== DashboardPanel =====

class TestDashboardPanel:
    def test_bind_ticker(self):
        panel = DashboardPanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.bind_ticker(ticker)
        assert panel._ticker is ticker

    def test_render_data_default(self):
        panel = DashboardPanel()
        assert panel.render_data() == {}

    def test_get_visual_encoding_default(self):
        panel = DashboardPanel()
        assert panel.get_visual_encoding() == {}


# ===== WinRatePanel =====

class TestWinRatePanel:
    def test_update(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.75)
        panel.update(ticker)
        assert panel.gauge_value == 0.75

    def test_update_from_bound_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.6)
        panel.bind_ticker(ticker)
        panel.update_from_bound_ticker()
        assert panel.gauge_value == 0.6

    def test_render_data(self):
        panel = WinRatePanel()
        panel.gauge_value = 0.5
        data = panel.render_data()
        assert data["gauge_value"] == 0.5

    def test_get_visual_encoding(self):
        panel = WinRatePanel()
        panel.gauge_value = 0.8
        enc = panel.get_visual_encoding()
        assert enc["type"] == "gauge"
        assert enc["value"] == 0.8


# ===== BankrollCurvePanel =====

class TestBankrollCurvePanel:
    def test_update(self):
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.bankroll_history = BankrollCurvePoint(step=5, bankroll=150.0, peak_bankroll=200.0, drawdown=-50.0)
        panel.update(ticker)
        assert panel.bankroll == 150.0
        assert panel.peak_bankroll == 200.0
        assert panel.drawdown == -50.0

    def test_update_from_bound_ticker(self):
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.bankroll_history = BankrollCurvePoint(step=10, bankroll=100.0, peak_bankroll=120.0, drawdown=-20.0)
        panel.bind_ticker(ticker)
        panel.update_from_bound_ticker()
        assert panel.bankroll == 100.0
        assert panel.peak_bankroll == 120.0
        assert panel.drawdown == -20.0

    def test_render_data(self):
        panel = BankrollCurvePanel()
        panel.bankroll = 100.0
        panel.peak_bankroll = 120.0
        panel.drawdown = -20.0
        data = panel.render_data()
        assert data["bankroll"] == 100.0
        assert data["peak_bankroll"] == 120.0
        assert data["drawdown"] == -20.0

    def test_get_visual_encoding(self):
        panel = BankrollCurvePanel()
        panel.bankroll = 150.0
        enc = panel.get_visual_encoding()
        assert enc["type"] == "curve"
        assert enc["bankroll"] == 150.0


# ===== NashEquilibriumPanel =====

class TestNashEquilibriumPanel:
    def test_update(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.3, current_strategy="aggressive")
        panel.update(ticker)
        assert panel.distance == 0.3
        assert panel.current_strategy == "aggressive"
        assert panel.nash_strategy == "nash_equilibrium"

    def test_update_from_bound_ticker(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.5, current_strategy="defensive")
        panel.bind_ticker(ticker)
        panel.update_from_bound_ticker()
        assert panel.distance == 0.5
        assert panel.current_strategy == "defensive"
        assert panel.nash_strategy == "nash_equilibrium"

    def test_render_data(self):
        panel = NashEquilibriumPanel()
        panel.distance = 0.4
        panel.current_strategy = "bluff"
        panel.nash_strategy = "nash_equilibrium"
        data = panel.render_data()
        assert data["distance"] == 0.4
        assert data["current_strategy"] == "bluff"
        assert data["nash_strategy"] == "nash_equilibrium"

    def test_get_visual_encoding(self):
        panel = NashEquilibriumPanel()
        panel.distance = 0.6
        enc = panel.get_visual_encoding()
        assert enc["type"] == "distance"
        assert enc["distance"] == 0.6
