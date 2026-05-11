"""Tests for src.dashboard.visualization."""

import csv
import io
import pytest
from unittest.mock import patch, MagicMock

from src.dashboard.visualization import (
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
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


# ===== TableauRenderer =====

class TestTableauRenderer:
    def test_bind_ticker(self):
        class ConcreteRenderer(TableauRenderer):
            def render(self, state):
                return {}
            def render_panel(self, panel):
                return {}

        r = ConcreteRenderer()
        ticker = DashboardTicker(symbol="TEST")
        r.bind_ticker(ticker)
        assert r._ticker is ticker


# ===== TableauCSVRenderer =====

class TestTableauCSVRenderer:
    def test_render(self):
        renderer = TableauCSVRenderer()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=10, wins=6, losses=4),
            bankroll=BankrollCurvePoint(step=5, bankroll=100.0, peak_bankroll=120.0, drawdown=-20.0),
            nash_distance=NashEquilibriumShift(distance=0.3, current_strategy="test"),
            timestamp=1000.0,
        )
        result = renderer.render(state)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 2  # header + data
        assert rows[1][0] == "1000.0"
        assert rows[1][1] == "0.6"
        assert rows[1][2] == "10"
        assert rows[1][3] == "6"
        assert rows[1][4] == "4"
        assert rows[1][5] == "100.0"
        assert rows[1][6] == "120.0"
        assert rows[1][7] == "-20.0"
        assert rows[1][8] == "0.3"
        assert rows[1][9] == "test"
        assert rows[1][10] == "nash_equilibrium"

    def test_render_no_header(self):
        renderer = TableauCSVRenderer(include_header=False)
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        result = renderer.render(state)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 1  # no header
        assert rows[0][0] == "0.5"

    def test_render_panel_win_rate(self):
        renderer = TableauCSVRenderer()
        panel = WinRatePanel()
        panel.gauge_value = 0.75
        result = renderer.render_panel(panel)
        assert result == "0.75"

    def test_render_panel_bankroll(self):
        renderer = TableauCSVRenderer()
        panel = BankrollCurvePanel()
        panel.bankroll = 150.0
        result = renderer.render_panel(panel)
        assert result == "150.0"

    def test_render_panel_nash(self):
        renderer = TableauCSVRenderer()
        panel = NashEquilibriumPanel()
        panel.distance = 0.4
        result = renderer.render_panel(panel)
        assert result == "0.4"

    def test_csv_buffer(self):
        renderer = TableauCSVRenderer()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        renderer.render(state)
        assert "0.5" in renderer._csv_buffer.getvalue()


# ===== TableauRESTRenderer =====

class TestTableauRESTRenderer:
    def test_render(self):
        renderer = TableauRESTRenderer(method="POST", url="http://test.com/api")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=10, wins=6, losses=4),
            bankroll=BankrollCurvePoint(step=5, bankroll=100.0, peak_bankroll=120.0, drawdown=-20.0),
            nash_distance=NashEquilibriumShift(distance=0.3, current_strategy="test"),
            timestamp=1000.0,
        )
        with patch("src.dashboard.visualization.requests.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"success": True}
            mock_req.return_value = mock_resp
            result = renderer.render(state)
            assert result == {"success": True}
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args
            assert call_kwargs[1]["method"] == "POST"
            assert call_kwargs[1]["url"] == "http://test.com/api"
            assert call_kwargs[1]["json"]["timestamp"] == 1000.0
            assert call_kwargs[1]["json"]["win_rate"]["value"] == 0.6

    def test_render_failure(self):
        renderer = TableauRESTRenderer(method="POST", url="http://test.com/api")
        state = DashboardState()
        with patch("src.dashboard.visualization.requests.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_req.return_value = mock_resp
            result = renderer.render(state)
            assert result == {}

    def test_render_panel(self):
        renderer = TableauRESTRenderer(method="POST", url="http://test.com/api")
        panel = WinRatePanel()
        panel.gauge_value = 0.8
        with patch("src.dashboard.visualization.requests.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"ok": True}
            mock_req.return_value = mock_resp
            result = renderer.render_panel(panel)
            assert result == {"ok": True}
            call_kwargs = mock_req.call_args
            assert call_kwargs[1]["json"]["gauge_value"] == 0.8

    def test_last_response(self):
        renderer = TableauRESTRenderer(method="POST", url="http://test.com/api")
        state = DashboardState()
        with patch("src.dashboard.visualization.requests.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"data": "test"}
            mock_req.return_value = mock_resp
            renderer.render(state)
            assert renderer.last_response is mock_resp


# ===== TableauDashboard =====

class TestTableauDashboard:
    def test_add_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert panel in dashboard._panels

    def test_add_renderer(self):
        dashboard = TableauDashboard()
        renderer = TableauCSVRenderer()
        dashboard.add_renderer(renderer)
        assert renderer in dashboard._renderers

    def test_bind_ticker(self):
        dashboard = TableauDashboard()
        ticker = DashboardTicker(symbol="TEST")
        panel = WinRatePanel()
        renderer = TableauCSVRenderer()
        dashboard.add_panel(panel)
        dashboard.add_renderer(renderer)
        dashboard.bind_ticker(ticker)
        assert dashboard._ticker is ticker
        assert panel._ticker is ticker
        assert renderer._ticker is ticker

    def test_update_panels(self):
        dashboard = TableauDashboard()
        ticker = DashboardTicker(symbol="TEST")
        panel = WinRatePanel()
        ticker.current_win_rate = WinRateMetric(value=0.7)
        dashboard.add_panel(panel)
        dashboard.bind_ticker(ticker)
        dashboard.update_panels()
        assert panel.gauge_value == 0.7

    def test_render(self):
        dashboard = TableauDashboard()
        renderer = TableauCSVRenderer()
        dashboard.add_renderer(renderer)
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        results = dashboard.render(state)
        assert len(results) == 1
        assert "0.5" in results[0]

    def test_render_panel(self):
        dashboard = TableauDashboard()
        renderer = TableauCSVRenderer()
        dashboard.add_renderer(renderer)
        panel = WinRatePanel()
        panel.gauge_value = 0.6
        results = dashboard.render_panel(panel)
        assert len(results) == 1
        assert results[0] == "0.6"

    def test_get_panel_data(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        panel.gauge_value = 0.75
        dashboard.add_panel(panel)
        data = dashboard.get_panel_data()
        assert "WinRatePanel" in data
        assert data["WinRatePanel"]["gauge_value"] == 0.75

    def test_get_visual_encodings(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        panel.gauge_value = 0.8
        dashboard.add_panel(panel)
        encodings = dashboard.get_visual_encodings()
        assert "WinRatePanel" in encodings
        assert encodings["WinRatePanel"]["type"] == "gauge"
        assert encodings["WinRatePanel"]["value"] == 0.8
