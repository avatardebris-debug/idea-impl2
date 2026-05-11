"""Tests for src.dashboard.renderers."""

import csv
import io
import json
from unittest.mock import MagicMock, patch

import pytest

from src.dashboard.models import (
    DashboardState,
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
)
from src.dashboard.panels import (
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
from src.dashboard.renderers import (
    TableauRenderer,
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)
from src.dashboard.tickers import DashboardTicker


# ===== TableauRenderer (abstract base) =====

class TestTableauRenderer:
    def test_render_raises_not_implemented(self):
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render(None)

    def test_render_panel_raises_not_implemented(self):
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render_panel(None)

    def test_render_panels(self):
        renderer = TableauRenderer()
        # render_panels calls render_panel which raises
        with pytest.raises(NotImplementedError):
            renderer.render_panels([])


# ===== TableauCSVRenderer =====

class TestTableauCSVRenderer:
    def test_render(self):
        renderer = TableauCSVRenderer()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5, total_games=100, wins=50, losses=50),
            bankroll=BankrollCurvePoint(step=10, bankroll=1050.0, peak_bankroll=1100.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="exploit", nash_strategy="nash_equilibrium"),
        )
        output = renderer.render(state)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) == 2  # header + data
        assert rows[0][0] == "timestamp"
        assert rows[1][0] == str(state.timestamp)

    def test_render_no_header(self):
        renderer = TableauCSVRenderer(include_header=False)
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5, total_games=100, wins=50, losses=50),
            bankroll=BankrollCurvePoint(step=10, bankroll=1050.0, peak_bankroll=1100.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="exploit", nash_strategy="nash_equilibrium"),
        )
        output = renderer.render(state)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) == 1  # only data row
        assert rows[0][0] == str(state.timestamp)

    def test_render_panel(self):
        renderer = TableauCSVRenderer()
        panel = WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25)
        output = renderer.render_panel(panel)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) == 2  # header + data

    def test_render_panel_no_header(self):
        renderer = TableauCSVRenderer(include_header=False)
        panel = WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25)
        output = renderer.render_panel(panel)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) == 1  # only data row

    def test_render_custom_delimiter(self):
        renderer = TableauCSVRenderer(delimiter=";")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5, total_games=100, wins=50, losses=50),
            bankroll=BankrollCurvePoint(step=10, bankroll=1050.0, peak_bankroll=1100.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="exploit", nash_strategy="nash_equilibrium"),
        )
        output = renderer.render(state)
        assert ";" in output


# ===== TableauRESTRenderer =====

class TestTableauRESTRenderer:
    def test_render(self):
        renderer = TableauRESTRenderer(server_url="https://test.example.com", site_id="test_site", content_url="test_project")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5, total_games=100, wins=50, losses=50),
            bankroll=BankrollCurvePoint(step=10, bankroll=1050.0, peak_bankroll=1100.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="exploit", nash_strategy="nash_equilibrium"),
        )
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response
            result = renderer.render(state)
            assert result is mock_response
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "test.example.com" in call_args[0][0]
            assert call_args[1]["json"]["win_rate"]["value"] == 0.5

    def test_render_with_token(self):
        renderer = TableauRESTRenderer(server_url="https://test.example.com", site_id="test_site", content_url="test_project", token="my_token")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5, total_games=100, wins=50, losses=50),
            bankroll=BankrollCurvePoint(step=10, bankroll=1050.0, peak_bankroll=1100.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="exploit", nash_strategy="nash_equilibrium"),
        )
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response
            renderer.render(state)
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert "Bearer my_token" in headers["Authorization"]

    def test_render_with_custom_payload_fn(self):
        def custom_payload(state):
            return {"custom": "data"}

        renderer = TableauRESTRenderer(
            server_url="https://test.example.com",
            site_id="test_site",
            content_url="test_project",
            payload_fn=custom_payload,
        )
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5, total_games=100, wins=50, losses=50),
            bankroll=BankrollCurvePoint(step=10, bankroll=1050.0, peak_bankroll=1100.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="exploit", nash_strategy="nash_equilibrium"),
        )
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response
            renderer.render(state)
            call_args = mock_post.call_args
            assert call_args[1]["json"]["custom"] == "data"

    def test_render_panel(self):
        renderer = TableauRESTRenderer(server_url="https://test.example.com", site_id="test_site", content_url="test_project")
        panel = WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25)
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response
            result = renderer.render_panel(panel)
            assert result is mock_response
            call_args = mock_post.call_args
            assert call_args[1]["json"]["gauge_value"] == 0.75


# ===== TableauDashboard =====

class TestTableauDashboard:
    def test_default_values(self):
        dashboard = TableauDashboard()
        assert dashboard.title == "Tableau Dashboard"
        assert dashboard.description == "Auto-generated Tableau Dashboard"
        assert dashboard.width == 1000
        assert dashboard.height == 800
        assert dashboard.panels == []
        assert dashboard.layout == "grid"
        assert dashboard.row_height == 200
        assert dashboard.column_width == 300

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

    def test_render(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response
            result = dashboard.render()
            assert result is mock_response
            call_args = mock_post.call_args
            assert call_args[1]["json"]["title"] == "Tableau Dashboard"
            assert len(call_args[1]["json"]["panels"]) == 1

    def test_render_empty(self):
        dashboard = TableauDashboard()
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response
            result = dashboard.render()
            assert result is mock_response
            call_args = mock_post.call_args
            assert len(call_args[1]["json"]["panels"]) == 0

    def test_render_with_custom_layout(self):
        dashboard = TableauDashboard(layout="freeform", row_height=150, column_width=250)
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response
            result = dashboard.render()
            assert result is mock_response
            call_args = mock_post.call_args
            assert call_args[1]["json"]["layout"] == "freeform"
            assert call_args[1]["json"]["row_height"] == 150
            assert call_args[1]["json"]["column_width"] == 250

    def test_to_dict(self):
        dashboard = TableauDashboard(title="Test", description="Desc", width=1200, height=900, layout="grid", row_height=250, column_width=350)
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        d = dashboard.to_dict()
        assert d["title"] == "Test"
        assert d["description"] == "Desc"
        assert d["width"] == 1200
        assert d["height"] == 900
        assert d["layout"] == "grid"
        assert d["row_height"] == 250
        assert d["column_width"] == 350
        assert len(d["panels"]) == 1

    def test_from_dict(self):
        data = {
            "title": "Test Dashboard",
            "description": "Test Desc",
            "width": 1200,
            "height": 900,
            "layout": "freeform",
            "row_height": 250,
            "column_width": 350,
            "panels": [
                {
                    "symbol": "WIN_RATE",
                    "title": "Win Rate",
                    "description": "Shows the win rate of the agent.",
                    "width": 10,
                    "height": 10,
                    "x": 0,
                    "y": 0,
                }
            ],
        }
        dashboard = TableauDashboard.from_dict(data)
        assert dashboard.title == "Test Dashboard"
        assert dashboard.description == "Test Desc"
        assert dashboard.width == 1200
        assert dashboard.height == 900
        assert dashboard.layout == "freeform"
        assert dashboard.row_height == 250
        assert dashboard.column_width == 350
        assert len(dashboard.panels) == 1
        assert dashboard.panels[0].symbol == "WIN_RATE"

    def test_from_dict_empty(self):
        data = {
            "title": "Empty",
            "description": "Empty Desc",
            "width": 1000,
            "height": 800,
            "layout": "grid",
            "row_height": 200,
            "column_width": 300,
            "panels": [],
        }
        dashboard = TableauDashboard.from_dict(data)
        assert dashboard.panels == []
