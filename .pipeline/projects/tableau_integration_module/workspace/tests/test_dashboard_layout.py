"""Additional tests for src.dashboard.renderers and src.dashboard.tickers."""

import csv
import io
import time
import pytest
from unittest.mock import patch, MagicMock

from src.dashboard.renderers import (
    TableauRenderer,
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)
from src.dashboard.tickers import DashboardTicker
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
    DashboardPanel,
)


# ===== TableauRenderer (abstract) =====

class TestTableauRenderer:
    def test_base_render_raises(self):
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render(None)

    def test_base_render_panel_raises(self):
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render_panel(None)

    def test_render_panels(self):
        renderer = TableauRenderer()
        # render_panels calls render_panel which raises
        with pytest.raises(NotImplementedError):
            renderer.render_panels([])


# ===== TableauCSVRenderer =====

class TestTableauCSVRendererRender:
    def test_render_default(self):
        renderer = TableauCSVRenderer()
        state = DashboardState()
        result = renderer.render(state)
        lines = result.strip().split("\n")
        assert len(lines) == 2  # header + data row
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 2
        assert len(rows[0]) == 12  # header columns
        assert len(rows[1]) == 12  # data columns

    def test_render_custom_delimiter(self):
        renderer = TableauCSVRenderer(delimiter=";")
        state = DashboardState()
        result = renderer.render(state)
        assert ";" in result

    def test_render_no_header(self):
        renderer = TableauCSVRenderer(include_header=False)
        state = DashboardState()
        result = renderer.render(state)
        lines = result.strip().split("\n")
        assert len(lines) == 1  # only data row

    def test_render_with_data(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1200, 1500], timestamp=200.0),
            nash_distance=NashEquilibriumShift(distance=0.05, current_strategy="test", nash_strategy="nash", timestamp=300.0),
            timestamp=400.0,
        )
        renderer = TableauCSVRenderer()
        result = renderer.render(state)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        data = rows[1]
        assert data[1] == "0.75"  # win_rate_value
        assert data[2] == "100"  # total_games
        assert data[3] == "75"  # wins
        assert data[4] == "25"  # losses
        assert data[5] == "10"  # bankroll step
        assert data[6] == "1500.0"  # bankroll
        assert data[9] == "0.05"  # nash distance
        assert data[11] == "400.0"  # timestamp


class TestTableauCSVRendererRenderPanel:
    def test_render_panel_win_rate(self):
        renderer = TableauCSVRenderer()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        result = renderer.render_panel(panel)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert rows[1][1] == "0.8"

    def test_render_panel_bankroll(self):
        renderer = TableauCSVRenderer()
        panel = BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500])
        result = renderer.render_panel(panel)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert rows[1][1] == "100.0"

    def test_render_panel_nash(self):
        renderer = TableauCSVRenderer()
        panel = NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash")
        result = renderer.render_panel(panel)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert rows[1][1] == "0.1"


# ===== TableauRESTRenderer =====

class TestTableauRESTRendererRender:
    def test_render_default(self):
        renderer = TableauRESTRenderer()
        state = DashboardState()
        result = renderer.render(state)
        assert "win_rate" in result
        assert "bankroll" in result
        assert "nash_distance" in result
        assert "timestamp" in result

    def test_render_custom_format(self):
        renderer = TableauRESTRenderer(format="json")
        state = DashboardState()
        result = renderer.render(state)
        assert "win_rate" in result
        assert "bankroll" in result

    def test_render_with_data(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1200, 1500], timestamp=200.0),
            nash_distance=NashEquilibriumShift(distance=0.05, current_strategy="test", nash_strategy="nash", timestamp=300.0),
            timestamp=400.0,
        )
        renderer = TableauRESTRenderer()
        result = renderer.render(state)
        assert "0.75" in result
        assert "1500.0" in result
        assert "0.05" in result
        assert "400.0" in result


class TestTableauRESTRendererRenderPanel:
    def test_render_panel_win_rate(self):
        renderer = TableauRESTRenderer()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        result = renderer.render_panel(panel)
        assert "gauge_value" in result
        assert "0.8" in result

    def test_render_panel_bankroll(self):
        renderer = TableauRESTRenderer()
        panel = BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500])
        result = renderer_render_panel(panel)
        assert "profit_loss" in result
        assert "100.0" in result

    def test_render_panel_nash(self):
        renderer = TableauRESTRenderer()
        panel = NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash")
        result = renderer.render_panel(panel)
        assert "distance" in result
        assert "0.1" in result


# ===== TableauDashboard =====

class TestTableauDashboardInit:
    def test_default_values(self):
        dashboard = TableauDashboard()
        assert dashboard.title == "Agent Dashboard"
        assert dashboard.description == "Real-time agent performance metrics."
        assert dashboard.width == 100
        assert dashboard.height == 100
        assert dashboard.panels == []
        assert dashboard.renderers == []

    def test_custom_values(self):
        dashboard = TableauDashboard(
            title="Custom Title",
            description="Custom description.",
            width=80,
            height=60,
        )
        assert dashboard.title == "Custom Title"
        assert dashboard.description == "Custom description."
        assert dashboard.width == 80
        assert dashboard.height == 60
        assert dashboard.panels == []
        assert dashboard.renderers == []


class TestTableauDashboardAddPanel:
    def test_add_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert panel in dashboard.panels

    def test_add_duplicate_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        dashboard.add_panel(panel)
        assert dashboard.panels.count(panel) == 1

    def test_add_panel_too_many(self):
        dashboard = TableauDashboard(width=10, height=10)
        panel1 = WinRatePanel()
        panel2 = BankrollCurvePanel()
        dashboard.add_panel(panel1)
        dashboard.add_panel(panel2)
        assert len(dashboard.panels) == 1


class TestTableauDashboardAddRenderer:
    def test_add_renderer(self):
        dashboard = TableauDashboard()
        renderer = TableauCSVRenderer()
        dashboard.add_renderer(renderer)
        assert renderer in dashboard.renderers

    def test_add_duplicate_renderer(self):
        dashboard = TableauDashboard()
        renderer = TableauCSVRenderer()
        dashboard.add_renderer(renderer)
        dashboard.add_renderer(renderer)
        assert dashboard.renderers.count(renderer) == 1


class TestTableauDashboardRender:
    def test_render_default(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.add_renderer(TableauCSVRenderer())
        result = dashboard.render()
        assert isinstance(result, dict)
        assert "title" in result
        assert "description" in result
        assert "panels" in result
        assert "renderers" in result

    def test_render_with_data(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        dashboard.add_renderer(TableauCSVRenderer())
        result = dashboard.render()
        assert result["title"] == "Agent Dashboard"
        assert len(result["panels"]) == 1
        assert len(result["renderers"]) == 1


class TestTableauDashboardRenderPanel:
    def test_render_panel(self):
        dashboard = TableauDashboard()
        dashboard.add_renderer(TableauCSVRenderer())
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        result = dashboard.render_panel(panel)
        assert "gauge_value" in result
        assert "0.8" in result


class TestTableauDashboardRenderPanels:
    def test_render_panels(self):
        dashboard = TableauDashboard()
        dashboard.add_renderer(TableauCSVRenderer())
        panel1 = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        panel2 = BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500])
        dashboard.add_panel(panel1)
        dashboard.add_panel(panel2)
        result = dashboard.render_panels()
        assert len(result) == 2


class TestTableauDashboardRenderAll:
    def test_render_all(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        dashboard.add_renderer(TableauCSVRenderer())
        result = dashboard.render_all()
        assert isinstance(result, dict)
        assert "title" in result
        assert "description" in result
        assert "panels" in result
        assert "renderers" in result
        assert len(result["panels"]) == 1
        assert len(result["renderers"]) == 1


# ===== DashboardTicker =====

class TestDashboardTickerInit:
    def test_default_values(self):
        ticker = DashboardTicker()
        assert ticker.interval == 1.0
        assert ticker.running is False
        assert ticker.callback is None
        assert ticker.thread is None

    def test_custom_values(self):
        ticker = DashboardTicker(interval=2.0, callback=lambda: None)
        assert ticker.interval == 2.0
        assert ticker.running is False
        assert ticker.callback is not None
        assert ticker.thread is None


class TestDashboardTickerStartStop:
    def test_start_stop(self):
        ticker = DashboardTicker(interval=0.01, callback=lambda: None)
        ticker.start()
        assert ticker.running is True
        ticker.stop()
        assert ticker.running is False

    def test_start_twice(self):
        ticker = DashboardTicker(interval=0.01, callback=lambda: None)
        ticker.start()
        ticker.start()
        assert ticker.running is True
        ticker.stop()

    def test_stop_without_start(self):
        ticker = DashboardTicker(interval=0.01, callback=lambda: None)
        ticker.stop()
        assert ticker.running is False

    def test_callback_called(self):
        call_count = [0]
        def callback():
            call_count[0] += 1
        ticker = DashboardTicker(interval=0.01, callback=callback)
        ticker.start()
        time.sleep(0.05)
        ticker.stop()
        assert call_count[0] > 0


class TestDashboardTickerProperties:
    def test_interval_setter(self):
        ticker = DashboardTicker(interval=1.0)
        ticker.interval = 2.0
        assert ticker.interval == 2.0

    def test_callback_setter(self):
        ticker = DashboardTicker()
        ticker.callback = lambda: None
        assert ticker.callback is not None

    def test_running_getter(self):
        ticker = DashboardTicker()
        assert ticker.running is False
        ticker.start()
        assert ticker.running is True
        ticker.stop()
        assert ticker.running is False
