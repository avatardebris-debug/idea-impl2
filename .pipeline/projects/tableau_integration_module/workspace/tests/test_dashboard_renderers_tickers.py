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
        result = renderer.render_panel(panel)
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

    def test_custom_values(self):
        dashboard = TableauDashboard(
            title="Custom Title",
            description="Custom Desc",
            width=80,
            height=60,
        )
        assert dashboard.title == "Custom Title"
        assert dashboard.description == "Custom Desc"
        assert dashboard.width == 80
        assert dashboard.height == 60
        assert dashboard.panels == []


class TestTableauDashboardAddPanel:
    def test_add_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert panel in dashboard.panels

    def test_add_multiple_panels(self):
        dashboard = TableauDashboard()
        panel1 = WinRatePanel()
        panel2 = BankrollCurvePanel()
        panel3 = NashEquilibriumPanel()
        dashboard.add_panel(panel1)
        dashboard.add_panel(panel2)
        dashboard.add_panel(panel3)
        assert len(dashboard.panels) == 3
        assert panel1 in dashboard.panels
        assert panel2 in dashboard.panels
        assert panel3 in dashboard.panels


class TestTableauDashboardRender:
    def test_render_csv(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25))
        renderer = TableauCSVRenderer()
        state = DashboardState()
        result = dashboard.render(state, renderer)
        assert "WIN_RATE" in result

    def test_render_rest(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25))
        renderer = TableauRESTRenderer()
        state = DashboardState()
        result = dashboard.render(state, renderer)
        assert "WIN_RATE" in result

    def test_render_no_panels(self):
        dashboard = TableauDashboard()
        renderer = TableauCSVRenderer()
        state = DashboardState()
        result = dashboard.render(state, renderer)
        assert result == ""


class TestTableauDashboardRenderPanels:
    def test_render_panels(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=100.0))
        renderer = TableauCSVRenderer()
        state = DashboardState()
        result = dashboard.render_panels(state, renderer)
        assert "WIN_RATE" in result
        assert "BANKROLL" in result


class TestTableauDashboardToDict:
    def test_to_dict(self):
        dashboard = TableauDashboard(
            title="Test",
            description="Desc",
            width=50,
            height=40,
        )
        dashboard.add_panel(WinRatePanel(gauge_value=0.5, total_games=50, wins=25, losses=25))
        d = dashboard.to_dict()
        assert d["title"] == "Test"
        assert d["description"] == "Desc"
        assert d["width"] == 50
        assert d["height"] == 40
        assert len(d["panels"]) == 1


class TestTableauDashboardFromDict:
    def test_from_dict(self):
        data = {
            "title": "From Dict",
            "description": "Desc",
            "width": 60,
            "height": 50,
            "panels": [
                {
                    "symbol": "WIN_RATE",
                    "title": "Test",
                    "description": "Desc",
                    "width": 10,
                    "height": 10,
                    "x": 0,
                    "y": 0,
                    "gauge_value": 0.5,
                    "total_games": 50,
                    "wins": 25,
                    "losses": 25,
                }
            ],
        }
        dashboard = TableauDashboard.from_dict(data)
        assert dashboard.title == "From Dict"
        assert dashboard.description == "Desc"
        assert dashboard.width == 60
        assert dashboard.height == 50
        assert len(dashboard.panels) == 1
        assert isinstance(dashboard.panels[0], WinRatePanel)


# ===== DashboardTicker =====

class TestDashboardTickerInit:
    def test_default_values(self):
        ticker = DashboardTicker(symbol="TEST")
        assert ticker.symbol == "TEST"
        assert ticker.current_win_rate is None
        assert ticker.current_bankroll is None
        assert ticker.nash_distance is None
        assert ticker.timestamp is None

    def test_custom_values(self):
        wr = WinRateMetric(value=0.8)
        bp = BankrollCurvePoint(bankroll=1000.0)
        ne = NashEquilibriumShift(distance=0.01)
        ticker = DashboardTicker(
            symbol="CUSTOM",
            current_win_rate=wr,
            current_bankroll=bp,
            nash_distance=ne,
            timestamp=100.0,
        )
        assert ticker.symbol == "CUSTOM"
        assert ticker.current_win_rate.value == 0.8
        assert ticker.current_bankroll.bankroll == 1000.0
        assert ticker.nash_distance.distance == 0.01
        assert ticker.timestamp == 100.0


class TestDashboardTickerUpdate:
    def test_update_all(self):
        ticker = DashboardTicker(symbol="TEST")
        wr = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0)
        bp = BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1200, 1500], timestamp=200.0)
        ne = NashEquilibriumShift(distance=0.05, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        ticker.update(wr, bp, ne, 400.0)
        assert ticker.current_win_rate.value == 0.75
        assert ticker.current_bankroll.bankroll == 1500.0
        assert ticker.nash_distance.distance == 0.05
        assert ticker.timestamp == 400.0

    def test_update_partial(self):
        ticker = DashboardTicker(symbol="TEST")
        wr = WinRateMetric(value=0.8)
        ticker.update(wr)
        assert ticker.current_win_rate.value == 0.8
        assert ticker.current_bankroll is None
        assert ticker.nash_distance is None
        assert ticker.timestamp is None


class TestDashboardTickerToDict:
    def test_to_dict(self):
        ticker = DashboardTicker(symbol="TEST")
        wr = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0)
        bp = BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1200, 1500], timestamp=200.0)
        ne = NashEquilibriumShift(distance=0.05, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        ticker.update(wr, bp, ne, 400.0)
        d = ticker.to_dict()
        assert d["symbol"] == "TEST"
        assert d["current_win_rate"]["value"] == 0.75
        assert d["current_bankroll"]["bankroll"] == 1500.0
        assert d["nash_distance"]["distance"] == 0.05
        assert d["timestamp"] == 400.0

    def test_to_dict_with_none_values(self):
        ticker = DashboardTicker(symbol="TEST")
        d = ticker.to_dict()
        assert d["symbol"] == "TEST"
        assert d["current_win_rate"] is None
        assert d["current_bankroll"] is None
        assert d["nash_distance"] is None
        assert d["timestamp"] is None


class TestDashboardTickerFromDict:
    def test_from_dict(self):
        d = {
            "symbol": "TEST",
            "current_win_rate": {"value": 0.75, "total_games": 100, "wins": 75, "losses": 25, "timestamp": 100.0},
            "current_bankroll": {"step": 10, "bankroll": 1500.0, "peak_bankroll": 2000.0, "drawdown": -500.0, "history": [1000, 1200, 1500], "timestamp": 200.0},
            "nash_distance": {"distance": 0.05, "current_strategy": "test", "nash_strategy": "nash", "timestamp": 300.0},
            "timestamp": 400.0,
        }
        ticker = DashboardTicker.from_dict(d)
        assert ticker.symbol == "TEST"
        assert ticker.current_win_rate.value == 0.75
        assert ticker.current_bankroll.bankroll == 1500.0
        assert ticker.nash_distance.distance == 0.05
        assert ticker.timestamp == 400.0

    def test_from_dict_with_none_values(self):
        d = {
            "symbol": "TEST",
            "current_win_rate": None,
            "current_bankroll": None,
            "nash_distance": None,
            "timestamp": None,
        }
        ticker = DashboardTicker.from_dict(d)
        assert ticker.symbol == "TEST"
        assert ticker.current_win_rate is None
        assert ticker.current_bankroll is None
        assert ticker.nash_distance is None
        assert ticker.timestamp is None

    def test_from_dict_partial(self):
        d = {"symbol": "TEST", "current_win_rate": {"value": 0.8}}
        ticker = DashboardTicker.from_dict(d)
        assert ticker.symbol == "TEST"
        assert ticker.current_win_rate.value == 0.8
        assert ticker.current_bankroll is None
        assert ticker.nash_distance is None
        assert ticker.timestamp is None


class TestDashboardTickerRoundtrip:
    def test_roundtrip(self):
        ticker = DashboardTicker(symbol="TEST")
        wr = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0)
        bp = BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1200, 1500], timestamp=200.0)
        ne = NashEquilibriumShift(distance=0.05, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        ticker.update(wr, bp, ne, 400.0)
        d = ticker.to_dict()
        ticker2 = DashboardTicker.from_dict(d)
        assert ticker2.symbol == ticker.symbol
        assert ticker2.current_win_rate.value == ticker.current_win_rate.value
        assert ticker2.current_bankroll.bankroll == ticker.current_bankroll.bankroll
        assert ticker2.nash_distance.distance == ticker.nash_distance.distance
        assert ticker2.timestamp == ticker.timestamp
