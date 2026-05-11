"""Integration tests for the tableau_integration_module dashboard system."""

import csv
import io
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
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)
from src.dashboard.tickers import DashboardTicker


class TestEndToEndDashboard:
    """Test the full dashboard pipeline: ticker -> state -> panels -> dashboard -> renderer."""

    def test_full_pipeline_csv(self):
        """Simulate a complete dashboard update cycle."""
        # 1. Create ticker with data
        ticker = DashboardTicker(symbol="AGENT_1")
        wr = WinRateMetric(value=0.75, total_games=200, wins=150, losses=50, timestamp=100.0)
        bp = BankrollCurvePoint(step=20, bankroll=1750.0, peak_bankroll=2000.0, drawdown=-250.0, history=[1000, 1200, 1500, 1750], timestamp=200.0)
        ne = NashEquilibriumShift(distance=0.08, current_strategy="balanced", nash_strategy="nash_optimal", timestamp=300.0)
        ticker.update(wr, bp, ne, 400.0)

        # 2. Create dashboard state
        state = DashboardState(
            win_rate=wr,
            bankroll=bp,
            nash_distance=ne,
            timestamp=400.0,
        )

        # 3. Create dashboard with panels
        dashboard = TableauDashboard(title="Agent 1 Dashboard", width=100, height=100)
        dashboard.add_panel(WinRatePanel(gauge_value=0.75, total_games=200, wins=150, losses=50))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=750.0, peak_bankroll=2000.0, drawdown=-250.0, history=[1000, 1200, 1500, 1750]))
        dashboard.add_panel(NashEquilibriumPanel(distance=0.08, current_strategy="balanced", nash_strategy="nash_optimal"))

        # 4. Render with CSV renderer
        renderer = TableauCSVRenderer()
        result = dashboard.render(state, renderer)

        # 5. Verify output
        lines = result.strip().split("\n")
        assert len(lines) == 2  # header + data
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 2
        assert len(rows[0]) == 12  # header columns
        assert len(rows[1]) == 12  # data columns
        assert "0.75" in result
        assert "1750.0" in result
        assert "0.08" in result

    def test_full_pipeline_rest(self):
        """Simulate a complete dashboard update cycle with REST renderer."""
        # 1. Create ticker with data
        ticker = DashboardTicker(symbol="AGENT_2")
        wr = WinRateMetric(value=0.6, total_games=100, wins=60, losses=40, timestamp=100.0)
        bp = BankrollCurvePoint(step=10, bankroll=1200.0, peak_bankroll=1500.0, drawdown=-300.0, history=[1000, 1200], timestamp=200.0)
        ne = NashEquilibriumShift(distance=0.15, current_strategy="aggressive", nash_strategy="nash_balanced", timestamp=300.0)
        ticker.update(wr, bp, ne, 400.0)

        # 2. Create dashboard state
        state = DashboardState(
            win_rate=wr,
            bankroll=bp,
            nash_distance=ne,
            timestamp=400.0,
        )

        # 3. Create dashboard with panels
        dashboard = TableauDashboard(title="Agent 2 Dashboard", width=80, height=60)
        dashboard.add_panel(WinRatePanel(gauge_value=0.6, total_games=100, wins=60, losses=40))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=200.0, peak_bankroll=1500.0, drawdown=-300.0, history=[1000, 1200]))
        dashboard.add_panel(NashEquilibriumPanel(distance=0.15, current_strategy="aggressive", nash_strategy="nash_balanced"))

        # 4. Render with REST renderer
        renderer = TableauRESTRenderer()
        result = dashboard.render(state, renderer)

        # 5. Verify output
        assert "0.6" in result
        assert "1200.0" in result
        assert "0.15" in result
        assert "AGENT_2" in result

    def test_empty_dashboard(self):
        """Test dashboard with no panels."""
        dashboard = TableauDashboard()
        state = DashboardState()
        renderer = TableauCSVRenderer()
        result = dashboard.render(state, renderer)
        assert result == ""

    def test_single_panel_dashboard(self):
        """Test dashboard with a single panel."""
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        state = DashboardState()
        renderer = TableauCSVRenderer()
        result = dashboard.render(state, renderer)
        assert "WIN_RATE" in result
        assert "0.8" in result


class TestDashboardSerialization:
    """Test dashboard serialization and deserialization."""

    def test_dashboard_to_dict_from_dict(self):
        """Test that dashboard can be serialized and deserialized."""
        dashboard = TableauDashboard(title="Test", description="Desc", width=50, height=40)
        dashboard.add_panel(WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=500.0, peak_bankroll=1500.0, drawdown=-200.0, history=[1000, 1500]))

        # Serialize
        d = dashboard.to_dict()
        assert d["title"] == "Test"
        assert d["description"] == "Desc"
        assert d["width"] == 50
        assert d["height"] == 40
        assert len(d["panels"]) == 2

        # Deserialize
        dashboard2 = TableauDashboard.from_dict(d)
        assert dashboard2.title == "Test"
        assert dashboard2.description == "Desc"
        assert dashboard2.width == 50
        assert dashboard2.height == 40
        assert len(dashboard2.panels) == 2
        assert isinstance(dashboard2.panels[0], WinRatePanel)
        assert isinstance(dashboard2.panels[1], BankrollCurvePanel)


class TestTickerStateConversion:
    """Test ticker to state conversion."""

    def test_ticker_to_state(self):
        """Test that ticker data can be converted to dashboard state."""
        ticker = DashboardTicker(symbol="TEST")
        wr = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0)
        bp = BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1200, 1500], timestamp=200.0)
        ne = NashEquilibriumShift(distance=0.05, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        ticker.update(wr, bp, ne, 400.0)

        state = ticker.to_state()
        assert state.win_rate.value == 0.75
        assert state.bankroll.bankroll == 1500.0
        assert state.nash_distance.distance == 0.05
        assert state.timestamp == 400.0

    def test_ticker_roundtrip(self):
        """Test that ticker can be serialized and deserialized."""
        ticker = DashboardTicker(symbol="TEST")
        wr = WinRateMetric(value=0.8, total_games=50, wins=40, losses=10, timestamp=100.0)
        bp = BankrollCurvePoint(step=5, bankroll=1200.0, peak_bankroll=1500.0, drawdown=-300.0, history=[1000, 1200], timestamp=200.0)
        ne = NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        ticker.update(wr, bp, ne, 400.0)

        d = ticker.to_dict()
        ticker2 = DashboardTicker.from_dict(d)
        assert ticker2.symbol == ticker.symbol
        assert ticker2.current_win_rate.value == ticker.current_win_rate.value
        assert ticker2.current_bankroll.bankroll == ticker.current_bankroll.bankroll
        assert ticker2.nash_distance.distance == ticker.nash_distance.distance
        assert ticker2.timestamp == ticker.timestamp


class TestPanelRenderData:
    """Test panel render_data methods."""

    def test_win_rate_panel_render_data(self):
        """Test WinRatePanel render_data."""
        panel = WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25)
        data = panel.render_data()
        assert data["gauge_value"] == 0.75
        assert data["total_games"] == 100
        assert data["wins"] == 75
        assert data["losses"] == 25
        assert "confidence_interval" in data
        assert "trend_arrow" in data

    def test_bankroll_panel_render_data(self):
        """Test BankrollCurvePanel render_data."""
        panel = BankrollCurvePanel(profit_loss=500.0, peak_bankroll=1500.0, drawdown=-200.0, history=[1000, 1500])
        data = panel.render_data()
        assert data["profit_loss"] == 500.0
        assert data["peak_bankroll"] == 1500.0
        assert data["drawdown"] == -200.0
        assert data["history"] == [1000, 1500]

    def test_nash_panel_render_data(self):
        """Test NashEquilibriumPanel render_data."""
        panel = NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash")
        data = panel.render_data()
        assert data["distance"] == 0.1
        assert data["current_strategy"] == "test"
        assert data["nash_strategy"] == "nash"


class TestDashboardPanelLayout:
    """Test dashboard panel layout."""

    def test_panels_fit_in_dashboard(self):
        """Test that panels can be laid out in a dashboard."""
        dashboard = TableauDashboard(width=100, height=100)
        panel1 = WinRatePanel(width=50, height=50, x=0, y=0)
        panel2 = BankrollCurvePanel(width=50, height=50, x=50, y=0)
        panel3 = NashEquilibriumPanel(width=50, height=50, x=0, y=50)
        panel4 = WinRatePanel(width=50, height=50, x=50, y=50)
        dashboard.add_panel(panel1)
        dashboard.add_panel(panel2)
        dashboard.add_panel(panel3)
        dashboard.add_panel(panel4)
        assert len(dashboard.panels) == 4

    def test_panels_overlap(self):
        """Test that overlapping panels are allowed (validation is optional)."""
        dashboard = TableauDashboard(width=100, height=100)
        panel1 = WinRatePanel(width=50, height=50, x=0, y=0)
        panel2 = BankrollCurvePanel(width=50, height=50, x=25, y=25)  # overlaps
        dashboard.add_panel(panel1)
        dashboard.add_panel(panel2)
        assert len(dashboard.panels) == 2
