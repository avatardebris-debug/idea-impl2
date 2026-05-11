"""Tests for dashboard panels."""

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


class TestDashboardPanel:
    """Tests for DashboardPanel base class."""

    def test_cannot_instantiate_directly(self):
        """Test that DashboardPanel cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Cannot instantiate abstract class"):
            DashboardPanel()

    def test_subclass_instantiation(self):
        """Test that subclasses can be instantiated."""
        panel = WinRatePanel()
        assert panel.symbol == "WIN_RATE"

    def test_default_values(self):
        """Test default values are correct."""
        panel = WinRatePanel()
        assert panel.symbol == "WIN_RATE"
        assert panel.title == "Win Rate"
        assert panel.description == "Shows the win rate of the agent."
        assert panel.width == 10
        assert panel.height == 10
        assert panel.x == 0
        assert panel.y == 0

    def test_to_dict(self):
        """Test serialization to dict."""
        panel = WinRatePanel(title="Custom Title", width=20, height=15, x=5, y=10)
        d = panel.to_dict()
        assert d["symbol"] == "WIN_RATE"
        assert d["title"] == "Custom Title"
        assert d["width"] == 20
        assert d["height"] == 15
        assert d["x"] == 5
        assert d["y"] == 10

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "symbol": "WIN_RATE",
            "title": "Custom Title",
            "width": 20,
            "height": 15,
            "x": 5,
            "y": 10,
        }
        panel = WinRatePanel.from_dict(data)
        assert panel.symbol == "WIN_RATE"
        assert panel.title == "Custom Title"
        assert panel.width == 20
        assert panel.height == 15
        assert panel.x == 5
        assert panel.y == 10

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {"symbol": "WIN_RATE"}
        panel = WinRatePanel.from_dict(data)
        assert panel.symbol == "WIN_RATE"
        assert panel.title == "Win Rate"
        assert panel.width == 10
        assert panel.height == 10

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = WinRatePanel(title="Test", width=15, height=12, x=3, y=7)
        d = original.to_dict()
        restored = WinRatePanel.from_dict(d)
        assert restored.symbol == original.symbol
        assert restored.title == original.title
        assert restored.width == original.width
        assert restored.height == original.height
        assert restored.x == original.x
        assert restored.y == original.y


class TestWinRatePanel:
    """Tests for WinRatePanel."""

    def test_default_values(self):
        """Test default values are correct."""
        panel = WinRatePanel()
        assert panel.symbol == "WIN_RATE"
        assert panel.title == "Win Rate"
        assert panel.description == "Shows the win rate of the agent."
        assert panel.width == 10
        assert panel.height == 10

    def test_render_data_empty_ticker(self):
        """Test render_data with empty ticker."""
        panel = WinRatePanel()
        panel.ticker = DashboardTicker(symbol="TEST")
        data = panel.render_data()
        assert data["value"] == 0.0
        assert data["total_games"] == 0
        assert data["wins"] == 0
        assert data["losses"] == 0
        assert data["ci_lower"] == 0.0
        assert data["ci_upper"] == 0.0

    def test_render_data_with_ticker(self):
        """Test render_data with populated ticker."""
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.75, total_games=100, wins=75, losses=25, timestamp=100.0)
        panel.ticker = ticker
        data = panel.render_data()
        assert data["value"] == 0.75
        assert data["total_games"] == 100
        assert data["wins"] == 75
        assert data["losses"] == 25
        assert data["ci_lower"] < 0.75
        assert data["ci_upper"] > 0.75

    def test_render_data_no_ticker(self):
        """Test render_data with no ticker."""
        panel = WinRatePanel()
        panel.ticker = None
        data = panel.render_data()
        assert data["value"] == 0.0
        assert data["total_games"] == 0

    def test_update(self):
        """Test update method."""
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.8, total_games=50, wins=40, losses=10, timestamp=100.0)
        panel.bind_ticker(ticker)
        panel.update(ticker)
        assert panel.ticker is ticker

    def test_bind_ticker(self):
        """Test bind_ticker method."""
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.bind_ticker(ticker)
        assert panel.ticker is ticker

    def test_unbind_ticker(self):
        """Test unbind_ticker method."""
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.bind_ticker(ticker)
        panel.unbind_ticker()
        assert panel.ticker is None


class TestBankrollCurvePanel:
    """Tests for BankrollCurvePanel."""

    def test_default_values(self):
        """Test default values are correct."""
        panel = BankrollCurvePanel()
        assert panel.symbol == "BANKROLL_CURVE"
        assert panel.title == "Bankroll Curve"
        assert panel.description == "Shows the bankroll curve of the agent."
        assert panel.width == 10
        assert panel.height == 10

    def test_render_data_empty_ticker(self):
        """Test render_data with empty ticker."""
        panel = BankrollCurvePanel()
        panel.ticker = DashboardTicker(symbol="TEST")
        data = panel.render_data()
        assert data["step"] == 0
        assert data["bankroll"] == 0.0
        assert data["peak_bankroll"] == 0.0
        assert data["drawdown"] == 0.0
        assert data["history"] == []

    def test_render_data_with_ticker(self):
        """Test render_data with populated ticker."""
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.bankroll_history = BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0)
        panel.ticker = ticker
        data = panel.render_data()
        assert data["step"] == 5
        assert data["bankroll"] == 1500.0
        assert data["peak_bankroll"] == 1600.0
        assert data["drawdown"] == -100.0
        assert data["history"] == [1000.0, 1500.0]

    def test_render_data_no_ticker(self):
        """Test render_data with no ticker."""
        panel = BankrollCurvePanel()
        panel.ticker = None
        data = panel.render_data()
        assert data["step"] == 0
        assert data["bankroll"] == 0.0
        assert data["history"] == []

    def test_update(self):
        """Test update method."""
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.bankroll_history = BankrollCurvePoint(step=5, bankroll=1500.0, peak_bankroll=1600.0, drawdown=-100.0, history=[1000.0, 1500.0], timestamp=100.0)
        panel.bind_ticker(ticker)
        panel.update(ticker)
        assert panel.ticker is ticker

    def test_bind_ticker(self):
        """Test bind_ticker method."""
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.bind_ticker(ticker)
        assert panel.ticker is ticker

    def test_unbind_ticker(self):
        """Test unbind_ticker method."""
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.bind_ticker(ticker)
        panel.unbind_ticker()
        assert panel.ticker is None


class TestNashEquilibriumPanel:
    """Tests for NashEquilibriumPanel."""

    def test_default_values(self):
        """Test default values are correct."""
        panel = NashEquilibriumPanel()
        assert panel.symbol == "NASH_DISTANCE"
        assert panel.title == "Nash Equilibrium Distance"
        assert panel.description == "Shows the distance from the Nash Equilibrium."
        assert panel.width == 10
        assert panel.height == 10

    def test_render_data_empty_ticker(self):
        """Test render_data with empty ticker."""
        panel = NashEquilibriumPanel()
        panel.ticker = DashboardTicker(symbol="TEST")
        data = panel.render_data()
        assert data["distance"] == 0.0
        assert data["current_strategy"] == "unknown"
        assert data["nash_strategy"] == "nash_equilibrium"

    def test_render_data_with_ticker(self):
        """Test render_data with populated ticker."""
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0)
        panel.ticker = ticker
        data = panel.render_data()
        assert data["distance"] == 0.1
        assert data["current_strategy"] == "bluff"
        assert data["nash_strategy"] == "nash_equilibrium"

    def test_render_data_no_ticker(self):
        """Test render_data with no ticker."""
        panel = NashEquilibriumPanel()
        panel.ticker = None
        data = panel.render_data()
        assert data["distance"] == 0.0
        assert data["current_strategy"] == "unknown"

    def test_update(self):
        """Test update method."""
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.1, current_strategy="bluff", nash_strategy="nash_equilibrium", timestamp=100.0)
        panel.bind_ticker(ticker)
        panel.update(ticker)
        assert panel.ticker is ticker

    def test_bind_ticker(self):
        """Test bind_ticker method."""
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.bind_ticker(ticker)
        assert panel.ticker is ticker

    def test_unbind_ticker(self):
        """Test unbind_ticker method."""
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.bind_ticker(ticker)
        panel.unbind_ticker()
        assert panel.ticker is None
