"""Tests for src.dashboard.panels."""

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

class TestDashboardPanelInit:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError, match="Cannot instantiate abstract class"):
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

    def test_custom_values(self):
        panel = WinRatePanel(
            title="Custom Title",
            description="Custom Desc",
            width=20,
            height=15,
            x=5,
            y=10,
        )
        assert panel.title == "Custom Title"
        assert panel.description == "Custom Desc"
        assert panel.width == 20
        assert panel.height == 15
        assert panel.x == 5
        assert panel.y == 10


class TestDashboardPanelUpdate:
    def test_update_sets_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        panel.update(ticker)
        assert panel._ticker is ticker

    def test_update_with_none(self):
        panel = WinRatePanel()
        panel.update(None)
        assert panel._ticker is None


class TestDashboardPanelRenderData:
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
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.6)
        panel.update(ticker)
        data = panel.render_data()
        assert "ticker" in data
        assert data["ticker"]["symbol"] == "TEST"


class TestDashboardPanelGetVisualEncoding:
    def test_base_returns_empty(self):
        panel = WinRatePanel()
        encoding = panel.get_visual_encoding()
        assert encoding == {}

    def test_win_rate_panel_encoding(self):
        panel = WinRatePanel(gauge_value=0.6)
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "gauge"
        assert encoding["color"] == "green"
        assert encoding["symbol"] == "WIN_RATE"

    def test_bankroll_panel_encoding(self):
        panel = BankrollCurvePanel(profit_loss=50.0)
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "sparkline"
        assert encoding["color"] == "green"
        assert encoding["symbol"] == "BANKROLL"

    def test_nash_panel_encoding(self):
        panel = NashEquilibriumPanel(distance=0.03)
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "heatmap"
        assert encoding["color"] == "green"
        assert encoding["symbol"] == "NASH_DIST"


class TestDashboardPanelRender:
    def test_base_render_raises(self):
        panel = WinRatePanel()
        with pytest.raises(NotImplementedError):
            panel.render(None)


class TestDashboardPanelToDict:
    def test_to_dict(self):
        panel = WinRatePanel(title="Test", width=5, height=5, x=1, y=2)
        d = panel.to_dict()
        assert d["symbol"] == "WIN_RATE"
        assert d["title"] == "Test"
        assert d["width"] == 5
        assert d["height"] == 5
        assert d["x"] == 1
        assert d["y"] == 2


class TestDashboardPanelFromDict:
    def test_from_dict(self):
        data = {
            "symbol": "WIN_RATE",
            "title": "From Dict",
            "description": "Desc",
            "width": 8,
            "height": 6,
            "x": 2,
            "y": 3,
        }
        panel = WinRatePanel.from_dict(data)
        assert panel.symbol == "WIN_RATE"
        assert panel.title == "From Dict"
        assert panel.width == 8
        assert panel.height == 6
        assert panel.x == 2
        assert panel.y == 3

    def test_from_dict_defaults(self):
        data = {}
        panel = WinRatePanel.from_dict(data)
        assert panel.symbol == ""
        assert panel.title == ""
        assert panel.width == 10
        assert panel.height == 10
        assert panel.x == 0
        assert panel.y == 0


class TestDashboardPanelBindTicker:
    def test_bind_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="BIND")
        panel.bind_ticker(ticker)
        assert panel._ticker is ticker

    def test_update_from_bound_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="BOUND")
        ticker.current_win_rate = WinRateMetric(value=0.7)
        panel.bind_ticker(ticker)
        panel.update_from_bound_ticker()
        assert panel._ticker is ticker


# ===== WinRatePanel =====

class TestWinRatePanelInit:
    def test_default_values(self):
        panel = WinRatePanel()
        assert panel.gauge_value == 0.0
        assert panel.confidence_interval == (0.0, 1.0)
        assert panel.trend_arrow == "→"
        assert panel.total_games == 0
        assert panel.wins == 0
        assert panel.losses == 0

    def test_custom_values(self):
        panel = WinRatePanel(
            gauge_value=0.75,
            confidence_interval=(0.6, 0.9),
            trend_arrow="↑",
            total_games=100,
            wins=75,
            losses=25,
        )
        assert panel.gauge_value == 0.75
        assert panel.confidence_interval == (0.6, 0.9)
        assert panel.trend_arrow == "↑"
        assert panel.total_games == 100
        assert panel.wins == 75
        assert panel.losses == 25


class TestWinRatePanelUpdate:
    def test_update_from_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.8, total_games=200, wins=160, losses=40)
        panel.update(ticker)
        assert panel.gauge_value == 0.8
        assert panel.total_games == 200
        assert panel.wins == 160
        assert panel.losses == 40
        # Confidence interval should be computed
        assert len(panel.confidence_interval) == 2
        assert 0.0 <= panel.confidence_interval[0] <= 1.0
        assert 0.0 <= panel.confidence_interval[1] <= 1.0

    def test_update_clamps_gauge_value(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=1.5, total_games=10)  # value > 1
        panel.update(ticker)
        assert panel.gauge_value == 1.0  # clamped

        ticker.current_win_rate = WinRateMetric(value=-0.5, total_games=10)  # value < 0
        panel.update(ticker)
        assert panel.gauge_value == 0.0  # clamped

    def test_update_trend_arrow_up(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.3, total_games=10)
        panel.update(ticker)
        ticker.current_win_rate = WinRateMetric(value=0.5, total_games=20)
        panel.update(ticker)
        assert panel.trend_arrow == "↑"

    def test_update_trend_arrow_down(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.5, total_games=10)
        panel.update(ticker)
        ticker.current_win_rate = WinRateMetric(value=0.3, total_games=20)
        panel.update(ticker)
        assert panel.trend_arrow == "↓"

    def test_update_trend_arrow_stable(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.5, total_games=10)
        panel.update(ticker)
        ticker.current_win_rate = WinRateMetric(value=0.5, total_games=20)
        panel.update(ticker)
        assert panel.trend_arrow == "→"

    def test_update_with_none_ticker(self):
        panel = WinRatePanel()
        panel.update(None)
        assert panel.gauge_value == 0.0
        assert panel.total_games == 0


class TestWinRatePanelRenderData:
    def test_render_data(self):
        panel = WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25)
        data = panel.render_data()
        assert data["gauge_value"] == 0.75
        assert data["total_games"] == 100
        assert data["wins"] == 75
        assert data["losses"] == 25
        assert data["trend_arrow"] == "→"
        assert len(data["confidence_interval"]) == 2


class TestWinRatePanelGetVisualEncoding:
    def test_encoding_with_ticker(self):
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.6)
        panel.update(ticker)
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "gauge"
        assert encoding["color"] == "green"
        assert encoding["symbol"] == "WIN_RATE"

    def test_encoding_color_red(self):
        panel = WinRatePanel(gauge_value=0.2)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "red"

    def test_encoding_color_yellow(self):
        panel = WinRatePanel(gauge_value=0.45)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "yellow"

    def test_encoding_color_green(self):
        panel = WinRatePanel(gauge_value=0.6)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "green"


class TestWinRatePanelRender:
    def test_render(self):
        panel = WinRatePanel(gauge_value=0.75, total_games=100, wins=75, losses=25)
        result = panel.render(None)
        assert "Win Rate" in result
        assert "75.00%" in result
        assert "100" in result
        assert "75" in result
        assert "25" in result


class TestWinRatePanelToDict:
    def test_to_dict(self):
        panel = WinRatePanel(gauge_value=0.5, total_games=50, wins=25, losses=25)
        d = panel.to_dict()
        assert d["gauge_value"] == 0.5
        assert d["total_games"] == 50
        assert d["wins"] == 25
        assert d["losses"] == 25


class TestWinRatePanelFromDict:
    def test_from_dict(self):
        data = {
            "gauge_value": 0.8,
            "total_games": 200,
            "wins": 160,
            "losses": 40,
        }
        panel = WinRatePanel.from_dict(data)
        assert panel.gauge_value == 0.8
        assert panel.total_games == 200
        assert panel.wins == 160
        assert panel.losses == 40

    def test_from_dict_defaults(self):
        data = {}
        panel = WinRatePanel.from_dict(data)
        assert panel.gauge_value == 0.0
        assert panel.total_games == 0
        assert panel.wins == 0
        assert panel.losses == 0


# ===== BankrollCurvePanel =====

class TestBankrollCurvePanelInit:
    def test_default_values(self):
        panel = BankrollCurvePanel()
        assert panel.profit_loss == 0.0
        assert panel.peak_bankroll == 0.0
        assert panel.drawdown == 0.0
        assert panel.history == []

    def test_custom_values(self):
        panel = BankrollCurvePanel(
            profit_loss=100.0,
            peak_bankroll=2000.0,
            drawdown=-500.0,
            history=[1000, 1500, 2000],
        )
        assert panel.profit_loss == 100.0
        assert panel.peak_bankroll == 2000.0
        assert panel.drawdown == -500.0
        assert panel.history == [1000, 1500, 2000]


class TestBankrollCurvePanelUpdate:
    def test_update_from_ticker(self):
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_bankroll = BankrollCurvePoint(
            step=5,
            bankroll=1500.0,
            peak_bankroll=2000.0,
            drawdown=-500.0,
            history=[1000, 1200, 1500],
        )
        panel.update(ticker)
        assert panel.profit_loss == 500.0  # 1500 - 1000
        assert panel.peak_bankroll == 2000.0
        assert panel.drawdown == -500.0
        assert panel.history == [1000, 1200, 1500]

    def test_update_with_none_ticker(self):
        panel = BankrollCurvePanel()
        panel.update(None)
        assert panel.profit_loss == 0.0
        assert panel.peak_bankroll == 0.0
        assert panel.drawdown == 0.0
        assert panel.history == []


class TestBankrollCurvePanelRenderData:
    def test_render_data(self):
        panel = BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500])
        data = panel.render_data()
        assert data["profit_loss"] == 100.0
        assert data["peak_bankroll"] == 2000.0
        assert data["drawdown"] == -500.0
        assert data["history"] == [1000, 1500]


class TestBankrollCurvePanelGetVisualEncoding:
    def test_encoding_with_ticker(self):
        panel = BankrollCurvePanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_bankroll = BankrollCurvePoint(bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0)
        panel.update(ticker)
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "sparkline"
        assert encoding["color"] == "green"
        assert encoding["symbol"] == "BANKROLL"

    def test_encoding_color_red(self):
        panel = BankrollCurvePanel(profit_loss=-100.0)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "red"

    def test_encoding_color_yellow(self):
        panel = BankrollCurvePanel(profit_loss=-10.0)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "yellow"

    def test_encoding_color_green(self):
        panel = BankrollCurvePanel(profit_loss=10.0)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "green"


class TestBankrollCurvePanelRender:
    def test_render(self):
        panel = BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500, 2000])
        result = panel.render(None)
        assert "Bankroll" in result
        assert "100.00" in result
        assert "2000.00" in result
        assert "-500.00" in result


class TestBankrollCurvePanelToDict:
    def test_to_dict(self):
        panel = BankrollCurvePanel(profit_loss=50.0, peak_bankroll=1500.0, drawdown=-200.0, history=[1000, 1500])
        d = panel.to_dict()
        assert d["profit_loss"] == 50.0
        assert d["peak_bankroll"] == 1500.0
        assert d["drawdown"] == -200.0
        assert d["history"] == [1000, 1500]


class TestBankrollCurvePanelFromDict:
    def test_from_dict(self):
        data = {
            "profit_loss": 75.0,
            "peak_bankroll": 1800.0,
            "drawdown": -300.0,
            "history": [1000, 1200, 1700],
        }
        panel = BankrollCurvePanel.from_dict(data)
        assert panel.profit_loss == 75.0
        assert panel.peak_bankroll == 1800.0
        assert panel.drawdown == -300.0
        assert panel.history == [1000, 1200, 1700]

    def test_from_dict_defaults(self):
        data = {}
        panel = BankrollCurvePanel.from_dict(data)
        assert panel.profit_loss == 0.0
        assert panel.peak_bankroll == 0.0
        assert panel.drawdown == 0.0
        assert panel.history == []


# ===== NashEquilibriumPanel =====

class TestNashEquilibriumPanelInit:
    def test_default_values(self):
        panel = NashEquilibriumPanel()
        assert panel.distance == 0.0
        assert panel.current_strategy == "unknown"
        assert panel.nash_strategy == "nash_equilibrium"

    def test_custom_values(self):
        panel = NashEquilibriumPanel(
            distance=0.25,
            current_strategy="aggressive",
            nash_strategy="nash_balanced",
        )
        assert panel.distance == 0.25
        assert panel.current_strategy == "aggressive"
        assert panel.nash_strategy == "nash_balanced"


class TestNashEquilibriumPanelUpdate:
    def test_update_from_ticker(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(
            distance=0.15,
            current_strategy="defensive",
            nash_strategy="nash_optimal",
        )
        panel.update(ticker)
        assert panel.distance == 0.15
        assert panel.current_strategy == "defensive"
        assert panel.nash_strategy == "nash_optimal"

    def test_update_with_none_ticker(self):
        panel = NashEquilibriumPanel()
        panel.update(None)
        assert panel.distance == 0.0
        assert panel.current_strategy == "unknown"
        assert panel.nash_strategy == "nash_equilibrium"


class TestNashEquilibriumPanelRenderData:
    def test_render_data(self):
        panel = NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash")
        data = panel.render_data()
        assert data["distance"] == 0.1
        assert data["current_strategy"] == "test"
        assert data["nash_strategy"] == "nash"


class TestNashEquilibriumPanelGetVisualEncoding:
    def test_encoding_with_ticker(self):
        panel = NashEquilibriumPanel()
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.05)
        panel.update(ticker)
        encoding = panel.get_visual_encoding()
        assert encoding["type"] == "heatmap"
        assert encoding["color"] == "green"
        assert encoding["symbol"] == "NASH_DIST"

    def test_encoding_color_red(self):
        panel = NashEquilibriumPanel(distance=0.3)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "red"

    def test_encoding_color_yellow(self):
        panel = NashEquilibriumPanel(distance=0.15)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "yellow"

    def test_encoding_color_green(self):
        panel = NashEquilibriumPanel(distance=0.05)
        encoding = panel.get_visual_encoding()
        assert encoding["color"] == "green"


class TestNashEquilibriumPanelRender:
    def test_render(self):
        panel = NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash")
        result = panel.render(None)
        assert "Nash Distance" in result
        assert "0.10" in result
        assert "test" in result
        assert "nash" in result


class TestNashEquilibriumPanelToDict:
    def test_to_dict(self):
        panel = NashEquilibriumPanel(distance=0.2, current_strategy="a", nash_strategy="b")
        d = panel.to_dict()
        assert d["distance"] == 0.2
        assert d["current_strategy"] == "a"
        assert d["nash_strategy"] == "b"


class TestNashEquilibriumPanelFromDict:
    def test_from_dict(self):
        data = {
            "distance": 0.3,
            "current_strategy": "c",
            "nash_strategy": "d",
        }
        panel = NashEquilibriumPanel.from_dict(data)
        assert panel.distance == 0.3
        assert panel.current_strategy == "c"
        assert panel.nash_strategy == "d"

    def test_from_dict_defaults(self):
        data = {}
        panel = NashEquilibriumPanel.from_dict(data)
        assert panel.distance == 0.0
        assert panel.current_strategy == "unknown"
        assert panel.nash_strategy == "nash_equilibrium"
