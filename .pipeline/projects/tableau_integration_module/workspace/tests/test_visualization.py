"""Tests for Tableau visualization helpers.

Covers:
  - TableauRenderer base class interface
  - TableauCSVRenderer CSV output, panel rendering
  - TableauRESTRenderer payload construction
  - TableauDashboard orchestration
"""

import csv
import io
from unittest.mock import MagicMock, patch

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
    DashboardState,
)
from src.dashboard.visualization import (
    TableauRenderer,
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)


# ===== TableauRenderer (base class) =====

class TestTableauRendererBase:
    def test_abstract_methods(self):
        """TableauRenderer should not be instantiable directly."""
        with pytest.raises(TypeError):
            TableauRenderer()

    def test_bind_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker()
        panel.bind_ticker(ticker)
        assert panel._ticker is ticker

    def test_update_from_bound_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=10, wins=6, losses=4, timestamp=100.0)
        )
        panel.bind_ticker(ticker)
        panel.update_from_bound_ticker()
        assert panel.gauge_value == 0.6

    def test_update_from_bound_ticker_no_ticker(self):
        panel = WinRatePanel()
        # Should not raise
        panel.update_from_bound_ticker()


# ===== TableauCSVRenderer =====

class TestTableauCSVRendererCreation:
    def test_default_values(self):
        renderer = TableauCSVRenderer()
        assert renderer.delimiter == ","
        assert renderer.include_header is True
        assert renderer._csv_buffer is None

    def test_custom_values(self):
        renderer = TableauCSVRenderer(delimiter=";", include_header=False)
        assert renderer.delimiter == ";"
        assert renderer.include_header is False


class TestTableauCSVRendererRender:
    def test_render_returns_string(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauCSVRenderer()
        result = renderer.render(state)
        assert isinstance(result, str)

    def test_render_includes_header(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauCSVRenderer(include_header=True)
        result = renderer.render(state)
        assert "timestamp" in result
        assert "win_rate" in result

    def test_render_no_header(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauCSVRenderer(include_header=False)
        result = renderer.render(state)
        lines = result.strip().split("\n")
        assert len(lines) == 1  # only data row
        assert "timestamp" not in lines[0]

    def test_render_data_row(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauCSVRenderer(include_header=False)
        result = renderer.render(state)
        lines = result.strip().split("\n")
        assert len(lines) == 1
        fields = lines[0].split(",")
        assert len(fields) == 11

    def test_render_stores_csv_buffer(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauCSVRenderer()
        renderer.render(state)
        assert renderer.get_csv_buffer() is not None
        assert renderer.get_csv_buffer() == renderer._csv_buffer


class TestTableauCSVRendererRenderPanel:
    def test_render_win_rate_panel(self):
        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0)
        )
        panel = WinRatePanel()
        panel.update(ticker)
        renderer = TableauCSVRenderer(include_header=False)
        result = renderer.render_panel(panel)
        assert isinstance(result, str)
        assert "0.6" in result

    def test_render_bankroll_panel(self):
        ticker = DashboardTicker(
            bankroll_history=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0)
        )
        panel = BankrollCurvePanel()
        panel.update(ticker)
        renderer = TableauCSVRenderer(include_header=False)
        result = renderer.render_panel(panel)
        assert isinstance(result, str)
        assert "1100.0" in result

    def test_render_nash_panel(self):
        ticker = DashboardTicker(
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0)
        )
        panel = NashEquilibriumPanel()
        panel.update(ticker)
        renderer = TableauCSVRenderer(include_header=False)
        result = renderer.render_panel(panel)
        assert isinstance(result, str)
        assert "0.1" in result

    def test_render_unknown_panel(self):
        class UnknownPanel(DashboardPanel):
            def update(self, ticker):
                pass
            def render_data(self):
                return {}
            def get_visual_encoding(self):
                return {}
        panel = UnknownPanel()
        renderer = TableauCSVRenderer()
        result = renderer.render_panel(panel)
        assert result == ""


# ===== TableauRESTRenderer =====

class TestTableauRESTRendererCreation:
    def test_default_values(self):
        renderer = TableauRESTRenderer()
        assert renderer.server_url == ""
        assert renderer.username == ""
        assert renderer.password == ""
        assert renderer.site_id == ""
        assert renderer.content_url == ""
        assert renderer.timeout == 30
        assert renderer.last_response is None

    def test_custom_values(self):
        renderer = TableauRESTRenderer(
            server_url="https://tableau.example.com",
            site_id="site123",
            content_url="content456",
            timeout=60,
        )
        assert renderer.server_url == "https://tableau.example.com"
        assert renderer.site_id == "site123"
        assert renderer.content_url == "content456"
        assert renderer.timeout == 60


class TestTableauRESTRendererRender:
    @patch("src.dashboard.visualization.requests.post")
    def test_render_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauRESTRenderer(
            server_url="https://tableau.example.com",
            site_id="site123",
            content_url="content456",
        )
        result = renderer.render(state)

        assert result is mock_response
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["win_rate"] == 0.6
        assert kwargs["json"]["total_games"] == 100
        assert kwargs["json"]["bankroll"] == 1100.0
        assert kwargs["json"]["nash_distance"] == 0.1

    @patch("src.dashboard.visualization.requests.post")
    def test_render_stores_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauRESTRenderer()
        renderer.render(state)
        assert renderer.get_last_response() is mock_response

    @patch("src.dashboard.visualization.requests.post")
    def test_render_handles_exception(self, mock_post):
        mock_post.side_effect = Exception("Network error")

        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        renderer = TableauRESTRenderer()
        result = renderer.render(state)
        assert result is None
        assert renderer.get_last_response() is None


class TestTableauRESTRendererRenderPanel:
    @patch("src.dashboard.visualization.requests.post")
    def test_render_panel_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0)
        )
        panel = WinRatePanel()
        panel.update(ticker)

        renderer = TableauRESTRenderer()
        result = renderer.render_panel(panel)

        assert result is mock_response
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["panel"] == "WIN_RATE"
        assert kwargs["json"]["data"]["gauge_value"] == 0.6

    @patch("src.dashboard.visualization.requests.post")
    def test_render_panel_stores_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0)
        )
        panel = WinRatePanel()
        panel.update(ticker)

        renderer = TableauRESTRenderer()
        renderer.render_panel(panel)
        assert renderer.get_last_response() is mock_response


# ===== TableauDashboard =====

class TestTableauDashboardCreation:
    def test_default_panels(self):
        dashboard = TableauDashboard()
        assert len(dashboard.panels) == 3
        assert isinstance(dashboard.panels[0], WinRatePanel)
        assert isinstance(dashboard.panels[1], BankrollCurvePanel)
        assert isinstance(dashboard.panels[2], NashEquilibriumPanel)

    def test_custom_panels(self):
        panels = [WinRatePanel(), BankrollCurvePanel()]
        dashboard = TableauDashboard(panels=panels)
        assert len(dashboard.panels) == 2

    def test_no_renderer(self):
        dashboard = TableauDashboard()
        assert dashboard.renderer is None

    def test_no_ticker(self):
        dashboard = TableauDashboard()
        assert dashboard.ticker is None


class TestTableauDashboardUpdate:
    def test_update_with_ticker(self):
        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0)
        )
        dashboard = TableauDashboard()
        dashboard.bind_ticker(ticker)
        dashboard.update()
        wr_panel = dashboard.get_panels_by_type(WinRatePanel)[0]
        assert wr_panel.gauge_value == 0.6

    def test_update_without_ticker(self):
        dashboard = TableauDashboard()
        # Should not raise
        dashboard.update()


class TestTableauDashboardRender:
    def test_render_without_renderer(self):
        dashboard = TableauDashboard()
        result = dashboard.render()
        assert result is None

    def test_render_without_ticker(self):
        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        result = dashboard.render()
        assert result is None

    @patch("src.dashboard.visualization.requests.post")
    def test_render_with_rest_renderer(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll_history=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        dashboard = TableauDashboard()
        dashboard.bind_ticker(ticker)
        dashboard.renderer = TableauRESTRenderer()
        result = dashboard.render()
        assert result is mock_response

    def test_render_with_csv_renderer(self):
        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll_history=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        dashboard = TableauDashboard()
        dashboard.bind_ticker(ticker)
        dashboard.renderer = TableauCSVRenderer()
        result = dashboard.render()
        assert isinstance(result, str)
        assert "0.6" in result


class TestTableauDashboardRenderPanel:
    def test_render_panel_without_renderer(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        result = dashboard.render_panel(panel)
        assert result is None

    def test_render_panel_with_csv_renderer(self):
        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0)
        )
        panel = WinRatePanel()
        panel.update(ticker)

        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        result = dashboard.render_panel(panel)
        assert isinstance(result, str)
        assert "0.6" in result


class TestTableauDashboardRenderAllPanels:
    def test_render_all_panels_without_renderer(self):
        dashboard = TableauDashboard()
        result = dashboard.render_all_panels()
        assert result == []

    def test_render_all_panels_with_csv_renderer(self):
        ticker = DashboardTicker(
            current_win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0),
            bankroll_history=BankrollCurvePoint(step=1, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0),
            timestamp=100.0,
        )
        dashboard = TableauDashboard()
        dashboard.bind_ticker(ticker)
        dashboard.renderer = TableauCSVRenderer()
        result = dashboard.render_all_panels()
        assert len(result) == 3
        assert all(isinstance(r, str) for r in result)


class TestTableauDashboardPanelManagement:
    def test_bind_ticker(self):
        ticker = DashboardTicker()
        dashboard = TableauDashboard()
        dashboard.bind_ticker(ticker)
        assert dashboard.ticker is ticker
        for panel in dashboard.panels:
            assert panel._ticker is ticker

    def test_add_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert len(dashboard.panels) == 4
        assert panel in dashboard.panels

    def test_add_panel_with_ticker(self):
        ticker = DashboardTicker()
        dashboard = TableauDashboard()
        dashboard.bind_ticker(ticker)
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert panel._ticker is ticker

    def test_remove_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        dashboard.remove_panel(panel)
        assert len(dashboard.panels) == 3
        assert panel not in dashboard.panels

    def test_get_panel_count(self):
        dashboard = TableauDashboard()
        assert dashboard.get_panel_count() == 3
        dashboard.add_panel(WinRatePanel())
        assert dashboard.get_panel_count() == 4

    def test_get_panels_by_type(self):
        dashboard = TableauDashboard()
        wr_panels = dashboard.get_panels_by_type(WinRatePanel)
        assert len(wr_panels) == 1
        assert isinstance(wr_panels[0], WinRatePanel)

        bk_panels = dashboard.get_panels_by_type(BankrollCurvePanel)
        assert len(bk_panels) == 1
        assert isinstance(bk_panels[0], BankrollCurvePanel)

        ne_panels = dashboard.get_panels_by_type(NashEquilibriumPanel)
        assert len(ne_panels) == 1
        assert isinstance(ne_panels[0], NashEquilibriumPanel)
