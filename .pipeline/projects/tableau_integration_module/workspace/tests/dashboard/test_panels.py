"""Tests for src.dashboard.panels."""

import math
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
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            DashboardPanel()

    def test_subclass_instantiation(self):
        panel = WinRatePanel()
        assert panel.symbol == "WIN_RATE"
        assert panel.title == "Win Rate"
        assert panel.description == "Shows the win rate of the agent."
        assert panel.width == 10
        assert panel.height == 10
        assert panel.x == 0
        assert panel.y == 0

    def test_custom_init_params(self):
        panel = WinRatePanel(
            title="Custom Title",
            description="Custom Desc",
            width=5,
            height=5,
            x=1,
            y=2,
        )
        assert panel.title == "Custom Title"
        assert panel.description == "Custom Desc"
        assert panel.width == 5
        assert panel.height == 5
        assert panel.x == 1
        assert panel.y == 2

    def test_bind_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        panel.bind_ticker(ticker)
        assert panel._ticker is ticker

    def test_update_from_bound_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        panel.bind_ticker(ticker)
        panel.update_from_bound_ticker()
        # Should not raise

    def test_render_data_base(self):
        panel = WinRatePanel()
        data = panel.render_data()
        assert "symbol" in data
        assert "title" in data
        assert "description" in data
        assert "width" in data
        assert "height" in data
        assert "x" in data
        assert "y" in data

    def test_render_data_with_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        panel.bind_ticker(ticker)
        panel.update(ticker)
        data = panel.render_data()
        assert "ticker" in data

    def test_to_dict(self):
        panel = WinRatePanel()
        d = panel.to_dict()
        assert d["symbol"] == "WIN_RATE"
        assert d["title"] == "Win Rate"

    def test_from_dict(self):
        data = {
            "symbol": "CUSTOM",
            "title": "Custom",
            "description": "Desc",
            "width": 8,
            "height": 8,
            "x": 1,
            "y": 2,
        }
        panel = WinRatePanel.from_dict(data)
        assert panel.symbol == "CUSTOM"
        assert panel.title == "Custom"
        assert panel.description == "Desc"
        assert panel.width == 8
        assert panel.height == 8
        assert panel.x == 1
        assert panel.y == 2

    def test_render_not_implemented(self):
        panel = WinRatePanel()
        with pytest.raises(NotImplementedError):
            panel.render("data")


# ===== WinRatePanel =====

class TestWinRatePanel:
    def test_default_values(self):
        panel = WinRatePanel()
        assert panel.gauge_value == 0.0
        assert panel.confidence_interval == (0.0, 1.0)
        assert panel.trend_arrow == "→"
        assert panel.total_games == 0
        assert panel.wins == 0
        assert panel.losses == 0

    def test_update_from_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(
            value=0.75,
            total_games=100,
            wins=75,
            losses=25,
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.gauge_value == 0.75
        assert panel.total_games == 100
        assert panel.wins == 75
        assert panel.losses == 25

    def test_gauge_value_clamped(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(
            value=1.5,  # > 1
            total_games=100,
            wins=100,
            losses=0,
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.gauge_value == 1.0

        ticker.current_win_rate = WinRateMetric(
            value=-0.5,  # < 0
            total_games=100,
            wins=0,
            losses=100,
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.gauge_value == 0.0

    def test_confidence_interval_computation(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        # 50% win rate with 100 games
        ticker.current_win_rate = WinRateMetric(
            value=0.5,
            total_games=100,
            wins=50,
            losses=50,
            timestamp=0,
        )
        panel.update(ticker)
        lo, hi = panel.confidence_interval
        assert lo >= 0.0
        assert hi <= 1.0
        assert lo < hi

    def test_trend_arrow_up(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(
            value=0.5,
            total_games=100,
            wins=50,
            losses=50,
            timestamp=0,
        )
        panel.update(ticker)

        # Now increase win rate
        ticker.current_win_rate = WinRateMetric(
            value=0.6,
            total_games=100,
            wins=60,
            losses=40,
            timestamp=1,
        )
        panel.update(ticker)
        assert panel.trend_arrow == "↑"

    def test_trend_arrow_down(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(
            value=0.6,
            total_games=100,
            wins=60,
            losses=40,
            timestamp=0,
        )
        panel.update(ticker)

        # Now decrease win rate
        ticker.current_win_rate = WinRateMetric(
            value=0.5,
            total_games=100,
            wins=50,
            losses=50,
            timestamp=1,
        )
        panel.update(ticker)
        assert panel.trend_arrow == "↓"

    def test_trend_arrow_flat(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(
            value=0.5,
            total_games=100,
            wins=50,
            losses=50,
            timestamp=0,
        )
        panel.update(ticker)

        # Same win rate
        ticker.current_win_rate = WinRateMetric(
            value=0.5,
            total_games=100,
            wins=50,
            losses=50,
            timestamp=1,
        )
        panel.update(ticker)
        assert panel.trend_arrow == "→"

    def test_render_data(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(
            value=0.75,
            total_games=100,
            wins=75,
            losses=25,
            timestamp=0,
        )
        panel.update(ticker)
        data = panel.render_data()
        assert data["gauge_value"] == 0.75
        assert data["confidence_interval"] is not None
        assert data["trend_arrow"] is not None
        assert data["total_games"] == 100
        assert data["wins"] == 75
        assert data["losses"] == 25

    def test_visual_encoding_green(self):
        panel = WinRatePanel()
        panel.gauge_value = 0.6
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "gauge"
        assert encoding["color"] == "green"

    def test_visual_encoding_red(self):
        panel = WinRatePanel()
        panel.gauge_value = 0.4
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "gauge"
        assert encoding["color"] == "red"


# ===== BankrollCurvePanel =====

class TestBankrollCurvePanel:
    def test_default_values(self):
        panel = BankrollCurvePanel()
        assert panel.current_bankroll == 0.0
        assert panel.peak_bankroll == 0.0
        assert panel.drawdown == 0.0
        assert panel.sparkline == []
        assert panel.profit_loss == 0.0
        assert panel.initial_bankroll == 1000.0

    def test_update_from_ticker(self):
        panel = BankrollCurvePanel()
        ticker = DashboardTicker()
        ticker.bankroll_history = BankrollCurvePoint(
            step=1,
            bankroll=1050.0,
            peak_bankroll=1100.0,
            drawdown=-50.0,
            history=[1000.0, 1050.0],
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.current_bankroll == 1050.0
        assert panel.peak_bankroll == 1100.0
        assert panel.drawdown == -50.0
        assert panel.sparkline == [1000.0, 1050.0]
        assert panel.profit_loss == 50.0

    def test_profit_loss_calculation(self):
        panel = BankrollCurvePanel(initial_bankroll=1000.0)
        ticker = DashboardTicker()
        ticker.bankroll_history = BankrollCurvePoint(
            step=1,
            bankroll=950.0,
            peak_bankroll=1000.0,
            drawdown=-50.0,
            history=[1000.0, 950.0],
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.profit_loss == -50.0

    def test_render_data(self):
        panel = BankrollCurvePanel()
        ticker = DashboardTicker()
        ticker.bankroll_history = BankrollCurvePoint(
            step=1,
            bankroll=1050.0,
            peak_bankroll=1100.0,
            drawdown=-50.0,
            history=[1000.0, 1050.0],
            timestamp=0,
        )
        panel.update(ticker)
        data = panel.render_data()
        assert data["current_bankroll"] == 1050.0
        assert data["peak_bankroll"] == 1100.0
        assert data["drawdown"] == -50.0
        assert data["sparkline"] == [1000.0, 1050.0]
        assert data["profit_loss"] == 50.0

    def test_visual_encoding_green(self):
        panel = BankrollCurvePanel()
        panel.profit_loss = 100.0
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "sparkline"
        assert encoding["color"] == "green"

    def test_visual_encoding_red(self):
        panel = BankrollCurvePanel()
        panel.profit_loss = -100.0
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "sparkline"
        assert encoding["color"] == "red"


# ===== NashEquilibriumPanel =====

class TestNashEquilibriumPanel:
    def test_default_values(self):
        panel = NashEquilibriumPanel()
        assert panel.distance == 0.0
        assert panel.current_strategy == "unknown"
        assert panel.nash_strategy == "nash_equilibrium"
        assert panel.heatmap_color == "white"

    def test_update_from_ticker(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker()
        ticker.nash_distance = NashEquilibriumShift(
            distance=0.1,
            current_strategy="bluff",
            nash_strategy="nash_equilibrium",
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.distance == 0.1
        assert panel.current_strategy == "bluff"
        assert panel.nash_strategy == "nash_equilibrium"

    def test_heatmap_color_green(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker()
        ticker.nash_distance = NashEquilibriumShift(
            distance=0.01,
            current_strategy="call",
            nash_strategy="nash_equilibrium",
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.heatmap_color == "green"

    def test_heatmap_color_yellow(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker()
        ticker.nash_distance = NashEquilibriumShift(
            distance=0.1,
            current_strategy="call",
            nash_strategy="nash_equilibrium",
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.heatmap_color == "yellow"

    def test_heatmap_color_red(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker()
        ticker.nash_distance = NashEquilibriumShift(
            distance=0.2,
            current_strategy="call",
            nash_strategy="nash_equilibrium",
            timestamp=0,
        )
        panel.update(ticker)
        assert panel.heatmap_color == "red"

    def test_render_data(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker()
        ticker.nash_distance = NashEquilibriumShift(
            distance=0.1,
            current_strategy="bluff",
            nash_strategy="nash_equilibrium",
            timestamp=0,
        )
        panel.update(ticker)
        data = panel.render_data()
        assert data["distance"] == 0.1
        assert data["current_strategy"] == "bluff"
        assert data["nash_strategy"] == "nash_equilibrium"
        assert data["heatmap_color"] == "yellow"

    def test_visual_encoding(self):
        panel = NashEquilibriumPanel()
        panel.heatmap_color = "green"
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "heatmap"
        assert encoding["color"] == "green"
