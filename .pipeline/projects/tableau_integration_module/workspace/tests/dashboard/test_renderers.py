"""Tests for src.dashboard.renderers."""

import csv
import io
import json
import pytest
from unittest.mock import patch, MagicMock
from src.dashboard.renderers import (
    TableauRenderer,
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)
from src.dashboard.panels import (
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
from src.dashboard.models import DashboardState
from src.dashboard.tickers import DashboardTicker


# ===== TableauRenderer (abstract) =====

class TestTableauRenderer:
    def test_render_raises_not_implemented(self):
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render(None)

    def test_render_panel_raises_not_implemented(self):
        renderer = TableauRenderer()
        panel = WinRatePanel()
        with pytest.raises(NotImplementedError):
            renderer.render_panel(panel)


# ===== TableauCSVRenderer =====

class TestTableauCSVRenderer:
    def test_render_win_rate_panel(self):
        renderer = TableauCSVRenderer()
        panel = WinRatePanel()
        panel.gauge_value = 0.75
        panel.confidence_interval = (0.65, 0.85)
        panel.trend_arrow = "↑"
        panel.total_games = 100
        panel.wins = 75
        panel.losses = 25
        panel.title = "Test Win Rate"
        panel.description = "Test description"
        panel.width = 10
        panel.height = 10
        panel.x = 0
        panel.y = 0
        panel.symbol = "WIN_RATE"

        result = renderer.render_panel(panel)
        assert "Test Win Rate" in result
        assert "0.75" in result
        assert "0.65" in result
        assert "0.85" in result
        assert "↑" in result
        assert "100" in result
        assert "75" in result
        assert "25" in result

    def test_render_bankroll_panel(self):
        renderer = TableauCSVRenderer()
        panel = BankrollCurvePanel()
        panel.current_bankroll = 1050.0
        panel.peak_bankroll = 1100.0
        panel.drawdown = -50.0
        panel.sparkline = [1000.0, 1050.0]
        panel.profit_loss = 50.0
        panel.initial_bankroll = 1000.0
        panel.title = "Test Bankroll"
        panel.description = "Test description"
        panel.width = 10
        panel.height = 10
        panel.x = 0
        panel.y = 0
        panel.symbol = "BANKROLL"

        result = renderer.render_panel(panel)
        assert "Test Bankroll" in result
        assert "1050.0" in result
        assert "1100.0" in result
        assert "-50.0" in result
        assert "50.0" in result

    def test_render_nash_panel(self):
        renderer = TableauCSVRenderer()
        panel = NashEquilibriumPanel()
        panel.distance = 0.1
        panel.current_strategy = "bluff"
        panel.nash_strategy = "nash_equilibrium"
        panel.heatmap_color = "yellow"
        panel.title = "Test Nash"
        panel.description = "Test description"
        panel.width = 10
        panel.height = 10
        panel.x = 0
        panel.y = 0
        panel.symbol = "NASH_DIST"

        result = renderer.render_panel(panel)
        assert "Test Nash" in result
        assert "0.1" in result
        assert "bluff" in result
        assert "nash_equilibrium" in result
        assert "yellow" in result

    def test_render_full_dashboard(self):
        renderer = TableauCSVRenderer()
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        dashboard.add_panel(NashEquilibriumPanel())

        result = renderer.render(dashboard)
        assert "Win Rate" in result
        assert "Bankroll" in result
        assert "Nash" in result

    def test_render_empty_dashboard(self):
        renderer = TableauCSVRenderer()
        dashboard = TableauDashboard()
        result = renderer.render(dashboard)
        # Should not raise
        assert result is not None

    def test_render_panel_empty_panel(self):
        renderer = TableauCSVRenderer()
        panel = WinRatePanel()
        result = renderer.render_panel(panel)
        # Should not raise
        assert result is not None


# ===== TableauRESTRenderer =====

class TestTableauRESTRenderer:
    def test_render_win_rate_panel(self):
        renderer = TableauRESTRenderer()
        panel = WinRatePanel()
        panel.gauge_value = 0.75
        panel.confidence_interval = (0.65, 0.85)
        panel.trend_arrow = "↑"
        panel.total_games = 100
        panel.wins = 75
        panel.losses = 25
        panel.title = "Test Win Rate"
        panel.description = "Test description"
        panel.width = 10
        panel.height = 10
        panel.x = 0
        panel.y = 0
        panel.symbol = "WIN_RATE"

        result = renderer.render_panel(panel)
        assert "Test Win Rate" in result
        assert "0.75" in result
        assert "0.65" in result
        assert "0.85" in result
        assert "↑" in result
        assert "100" in result
        assert "75" in result
        assert "25" in result

    def test_render_bankroll_panel(self):
        renderer = TableauRESTRenderer()
        panel = BankrollCurvePanel()
        panel.current_bankroll = 1050.0
        panel.peak_bankroll = 1100.0
        panel.drawdown = -50.0
        panel.sparkline = [1000.0, 1050.0]
        panel.profit_loss = 50.0
        panel.initial_bankroll = 1000.0
        panel.title = "Test Bankroll"
        panel.description = "Test description"
        panel.width = 10
        panel.height = 10
        panel.x = 0
        panel.y = 0
        panel.symbol = "BANKROLL"

        result = renderer.render_panel(panel)
        assert "Test Bankroll" in result
        assert "1050.0" in result
        assert "1100.0" in result
        assert "-50.0" in result
        assert "50.0" in result

    def test_render_nash_panel(self):
        renderer = TableauRESTRenderer()
        panel = NashEquilibriumPanel()
        panel.distance = 0.1
        panel.current_strategy = "bluff"
        panel.nash_strategy = "nash_equilibrium"
        panel.heatmap_color = "yellow"
        panel.title = "Test Nash"
        panel.description = "Test description"
        panel.width = 10
        panel.height = 10
        panel.x = 0
        panel.y = 0
        panel.symbol = "NASH_DIST"

        result = renderer.render_panel(panel)
        assert "Test Nash" in result
        assert "0.1" in result
        assert "bluff" in result
        assert "nash_equilibrium" in result
        assert "yellow" in result

    def test_render_full_dashboard(self):
        renderer = TableauRESTRenderer()
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        dashboard.add_panel(NashEquilibriumPanel())

        result = renderer.render(dashboard)
        assert "Win Rate" in result
        assert "Bankroll" in result
        assert "Nash" in result

    def test_render_empty_dashboard(self):
        renderer = TableauRESTRenderer()
        dashboard = TableauDashboard()
        result = renderer.render(dashboard)
        # Should not raise
        assert result is not None

    def test_render_panel_empty_panel(self):
        renderer = TableauRESTRenderer()
        panel = WinRatePanel()
        result = renderer.render_panel(panel)
        # Should not raise
        assert result is not None


# ===== TableauDashboard =====

class TestTableauDashboard:
    def test_add_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert panel in dashboard.panels

    def test_remove_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        dashboard.remove_panel(panel)
        assert panel not in dashboard.panels

    def test_get_panel_count(self):
        dashboard = TableauDashboard()
        assert dashboard.get_panel_count() == 0
        dashboard.add_panel(WinRatePanel())
        assert dashboard.get_panel_count() == 1

    def test_get_panels_by_type(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        wr_panels = dashboard.get_panels_by_type(WinRatePanel)
        assert len(wr_panels) == 2

    def test_to_dict(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        d = dashboard.to_dict()
        assert "panels" in d
        assert len(d["panels"]) == 1

    def test_from_dict(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        d = dashboard.to_dict()
        new_dashboard = TableauDashboard.from_dict(d)
        assert len(new_dashboard.panels) == 1
        assert isinstance(new_dashboard.panels[0], WinRatePanel)

    def test_clear_panels(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.clear_panels()
        assert len(dashboard.panels) == 0

    def test_panels_list_is_mutable(self):
        dashboard = TableauDashboard()
        dashboard.panels.append(WinRatePanel())
        assert len(dashboard.panels) == 1

    def test_remove_nonexistent_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        # Should not raise
        dashboard.remove_panel(panel)
        assert len(dashboard.panels) == 0

    def test_from_dict_empty(self):
        d = {"panels": []}
        dashboard = TableauDashboard.from_dict(d)
        assert len(dashboard.panels) == 0
