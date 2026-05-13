"""Tests for tableau renderers."""

import pytest
from src.dashboard.renderers import (
    TableauRenderer,
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)
from src.dashboard.models import DashboardState, WinRateMetric, BankrollCurvePoint, NashEquilibriumShift
from src.dashboard.panels import WinRatePanel, BankrollCurvePanel, NashEquilibriumPanel
from src.dashboard.tickers import DashboardTicker


class TestTableauRenderer:
    """Tests for TableauRenderer base class."""

    def test_render_not_implemented(self):
        """Test that render raises NotImplementedError."""
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render(None)

    def test_render_panel_not_implemented(self):
        """Test that render_panel raises NotImplementedError."""
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render_panel(None)


class TestTableauCSVRenderer:
    """Tests for TableauCSVRenderer."""

    def test_render_with_dashboard_state(self):
        """Test rendering a DashboardState to CSV."""
        renderer = TableauCSVRenderer()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=100.0,
        )
        csv_str = renderer.render(state)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 2  # header + data
        assert "timestamp" in lines[0]
        assert "0.75" in lines[1]

    def test_render_with_dashboard(self):
        """Test rendering a TableauDashboard to CSV."""
        dashboard = TableauDashboard(title="Test Dashboard")
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        dashboard.add_panel(NashEquilibriumPanel())
        renderer = TableauCSVRenderer()
        csv_str = renderer.render(dashboard)
        lines = csv_str.strip().split("\n")
        # Header + data row (at least 2 lines)
        assert len(lines) >= 2
        # Header contains keys from all panels
        assert "gauge_value" in lines[0]
        assert "current_bankroll" in lines[0]
        assert "distance" in lines[0]

    def test_render_panel(self):
        """Test rendering a single panel to CSV."""
        renderer = TableauCSVRenderer()
        panel = WinRatePanel()
        csv_str = renderer.render_panel(panel)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 2  # header + data

    def test_render_with_custom_delimiter(self):
        """Test rendering with custom delimiter."""
        renderer = TableauCSVRenderer(delimiter=";")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=100.0,
        )
        csv_str = renderer.render(state)
        assert ";" in csv_str
        assert "," not in csv_str

    def test_render_without_header(self):
        """Test rendering without header."""
        renderer = TableauCSVRenderer(include_header=False)
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=100.0,
        )
        csv_str = renderer.render(state)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 1  # only data row

    def test_render_panel_without_header(self):
        """Test rendering a single panel without header."""
        renderer = TableauCSVRenderer(include_header=False)
        panel = WinRatePanel()
        csv_str = renderer.render_panel(panel)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 1  # only data row


class TestTableauRESTRenderer:
    """Tests for TableauRESTRenderer."""

    def test_render_with_dashboard_state(self):
        """Test rendering a DashboardState to JSON (no server, returns None)."""
        renderer = TableauRESTRenderer()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=100.0,
        )
        # Without a real server, render returns None due to connection failure
        result = renderer.render(state)
        assert result is None

    def test_render_with_dashboard(self):
        """Test rendering a TableauDashboard to JSON."""
        dashboard = TableauDashboard(title="Test Dashboard")
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        dashboard.add_panel(NashEquilibriumPanel())
        renderer = TableauRESTRenderer()
        result = renderer.render(dashboard)
        assert "title" in result
        assert "panels" in result

    def test_render_panel(self):
        """Test rendering a single panel to JSON."""
        renderer = TableauRESTRenderer()
        panel = WinRatePanel()
        result = renderer.render_panel(panel)
        assert "panel" in result
        assert "data" in result

    def test_render_with_custom_payload_fn(self):
        """Test rendering with custom payload function (no server, returns None)."""
        def custom_payload(state):
            return {"custom": "data"}

        renderer = TableauRESTRenderer(payload_fn=custom_payload)
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=100.0,
        )
        # Without a real server, render returns None due to connection failure
        result = renderer.render(state)
        assert result is None

    def test_render_with_token(self):
        """Test rendering with authentication token (no server, returns None)."""
        renderer = TableauRESTRenderer(token="test_token")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0),
            timestamp=100.0,
        )
        # Without a real server, render returns None due to connection failure
        result = renderer.render(state)
        assert result is None


class TestTableauDashboard:
    """Tests for TableauDashboard."""

    def test_default_values(self):
        """Test default values are correct."""
        dashboard = TableauDashboard()
        assert dashboard.title == "Dashboard"
        assert dashboard.description == ""
        assert dashboard.panels == []

    def test_add_panel(self):
        """Test adding a panel."""
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert len(dashboard.panels) == 1
        assert dashboard.panels[0] is panel

    def test_add_multiple_panels(self):
        """Test adding multiple panels."""
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        dashboard.add_panel(NashEquilibriumPanel())
        assert len(dashboard.panels) == 3

    def test_remove_panel(self):
        """Test removing a panel."""
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        dashboard.remove_panel(panel)
        assert len(dashboard.panels) == 0

    def test_remove_panel_not_found(self):
        """Test removing a panel that doesn't exist."""
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.remove_panel(panel)  # Should not raise
        assert len(dashboard.panels) == 0

    def test_to_dict(self):
        """Test serialization to dict."""
        dashboard = TableauDashboard(title="Test Dashboard", description="Test Description")
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        d = dashboard.to_dict()
        assert d["title"] == "Test Dashboard"
        assert d["description"] == "Test Description"
        assert len(d["panels"]) == 2

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "title": "Test Dashboard",
            "description": "Test Description",
            "panels": [
                {"symbol": "WIN_RATE", "title": "Win Rate", "width": 10, "height": 10, "x": 0, "y": 0},
                {"symbol": "BANKROLL_CURVE", "title": "Bankroll Curve", "width": 10, "height": 10, "x": 0, "y": 0},
            ],
        }
        dashboard = TableauDashboard.from_dict(data)
        assert dashboard.title == "Test Dashboard"
        assert dashboard.description == "Test Description"
        assert len(dashboard.panels) == 2

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = TableauDashboard(title="Test Dashboard", description="Test Description")
        original.add_panel(WinRatePanel())
        original.add_panel(BankrollCurvePanel())
        d = original.to_dict()
        restored = TableauDashboard.from_dict(d)
        assert restored.title == original.title
        assert restored.description == original.description
        assert len(restored.panels) == len(original.panels)
