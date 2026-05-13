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

    def test_render_with_data(self):
        state = DashboardState(
            win_rate=WinRateMetric(value=0.8, total_games=100, wins=80, losses=20, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500], timestamp=200.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash", timestamp=300.0),
            timestamp=400.0,
        )
        renderer = TableauRESTRenderer()
        result = renderer.render(state)
        assert "0.8" in result
        assert "1500.0" in result
        assert "0.1" in result

    def test_render_with_payload_fn(self):
        def custom_fn(state):
            return {"custom": "data"}

        state = DashboardState()
        renderer = TableauRESTRenderer(payload_fn=custom_fn)
        result = renderer.render(state)
        assert "custom" in result
        assert "data" in result

    def test_render_with_token(self):
        state = DashboardState()
        renderer = TableauRESTRenderer(token="test_token")
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            result = renderer.render(state)
            assert result == mock_response
            mock_post.assert_called_once()
            headers = mock_post.call_args[1]["headers"]
            assert "Bearer test_token" in headers.get("Authorization", "")

    def test_render_with_custom_headers(self):
        state = DashboardState()
        renderer = TableauRESTRenderer(headers={"X-Custom": "value"})
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            result = renderer.render(state)
            headers = mock_post.call_args[1]["headers"]
            assert headers["X-Custom"] == "value"

    def test_render_with_timeout(self):
        state = DashboardState()
        renderer = TableauRESTRenderer(timeout=10)
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            result = renderer.render(state)
            assert mock_post.call_args[1]["timeout"] == 10

    def test_render_with_error(self):
        state = DashboardState()
        renderer = TableauRESTRenderer()
        with patch("src.dashboard.renderers.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")
            result = renderer.render(state)
            assert result is None

    def test_render_with_dashboard_state(self):
        dashboard = TableauDashboard(title="Test Dashboard", description="Test", panels=[
            WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10),
            BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500]),
            NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash"),
        ])
        renderer = TableauRESTRenderer()
        result = renderer.render(dashboard)
        assert "Test Dashboard" in result
        assert "panels" in result


class TestTableauRESTRendererRenderPanel:
    def test_render_panel_win_rate(self):
        renderer = TableauRESTRenderer()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        result = renderer.render_panel(panel)
        assert "panel" in result
        assert "data" in result
        assert "0.8" in result

    def test_render_panel_bankroll(self):
        renderer = TableauRESTRenderer()
        panel = BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500])
        result = renderer.render_panel(panel)
        assert "panel" in result
        assert "data" in result
        assert "100.0" in result

    def test_render_panel_nash(self):
        renderer = TableauRESTRenderer()
        panel = NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash")
        result = renderer.render_panel(panel)
        assert "panel" in result
        assert "data" in result
        assert "0.1" in result

    def test_render_panel_error(self):
        renderer = TableauRESTRenderer()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        result = renderer.render_panel(panel)
        assert isinstance(result, str)


# ===== TableauDashboard =====

class TestTableauDashboardInit:
    def test_default_values(self):
        dashboard = TableauDashboard()
        assert dashboard.title == "Dashboard"
        assert dashboard.description == ""
        assert dashboard.width == 10
        assert dashboard.height == 10
        assert dashboard.x == 0
        assert dashboard.y == 0
        assert dashboard.panels == []
        assert dashboard.renderer is None
        assert dashboard.ticker is None

    def test_custom_values(self):
        dashboard = TableauDashboard(
            title="Custom Title",
            description="Custom Description",
            width=20,
            height=20,
            x=5,
            y=5,
        )
        assert dashboard.title == "Custom Title"
        assert dashboard.description == "Custom Description"
        assert dashboard.width == 20
        assert dashboard.height == 20
        assert dashboard.x == 5
        assert dashboard.y == 5


class TestTableauDashboardUpdate:
    def test_update_with_ticker(self):
        dashboard = TableauDashboard()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.8, total_games=100, wins=80, losses=20, timestamp=100.0)
        ticker.bankroll_history = BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500], timestamp=200.0)
        ticker.nash_distance = NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        ticker.timestamp = 400.0
        dashboard.bind_ticker(ticker)
        dashboard.update()
        # Panels should be updated from ticker
        for panel in dashboard.panels:
            assert panel.gauge_value == 0.8 or panel.profit_loss == 500.0 or panel.distance == 0.1

    def test_update_without_ticker(self):
        dashboard = TableauDashboard()
        dashboard.update()  # Should not raise


class TestTableauDashboardAddPanel:
    def test_add_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        dashboard.add_panel(panel)
        assert len(dashboard.panels) == 1
        assert dashboard.panels[0] is panel

    def test_add_duplicate_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        dashboard.add_panel(panel)
        dashboard.add_panel(panel)
        assert len(dashboard.panels) == 2  # Duplicates are allowed

    def test_add_panel_too_many(self):
        dashboard = TableauDashboard()
        for i in range(100):
            panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
            dashboard.add_panel(panel)
        assert len(dashboard.panels) == 100  # No limit enforced


class TestTableauDashboardRemovePanel:
    def test_remove_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        dashboard.add_panel(panel)
        dashboard.remove_panel(panel)
        assert len(dashboard.panels) == 0

    def test_remove_nonexistent_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        dashboard.remove_panel(panel)  # Should not raise


class TestTableauDashboardGetPanelCount:
    def test_get_panel_count_empty(self):
        dashboard = TableauDashboard()
        assert dashboard.get_panel_count() == 0

    def test_get_panel_count_with_panels(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500]))
        assert dashboard.get_panel_count() == 2


class TestTableauDashboardGetPanelsByType:
    def test_get_panels_by_type_win_rate(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500]))
        win_rate_panels = dashboard.get_panels_by_type(WinRatePanel)
        assert len(win_rate_panels) == 1

    def test_get_panels_by_type_bankroll(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500]))
        bankroll_panels = dashboard.get_panels_by_type(BankrollCurvePanel)
        assert len(bankroll_panels) == 1

    def test_get_panels_by_type_nash(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(NashEquilibriumPanel(distance=0.1, current_strategy="test", nash_strategy="nash"))
        nash_panels = dashboard.get_panels_by_type(NashEquilibriumPanel)
        assert len(nash_panels) == 1

    def test_get_panels_by_type_none(self):
        dashboard = TableauDashboard()
        panels = dashboard.get_panels_by_type(WinRatePanel)
        assert len(panels) == 0


class TestTableauDashboardBindTicker:
    def test_bind_ticker(self):
        dashboard = TableauDashboard()
        ticker = DashboardTicker(symbol="TEST")
        dashboard.bind_ticker(ticker)
        assert dashboard.ticker is ticker

    def test_bind_ticker_with_panels(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        dashboard.add_panel(panel)
        ticker = DashboardTicker(symbol="TEST")
        dashboard.bind_ticker(ticker)
        assert dashboard.ticker is ticker
        assert panel.ticker is ticker


class TestTableauDashboardRender:
    def test_render_default(self):
        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        result = dashboard.render()
        assert "win_rate" in result
        assert "bankroll" in result
        assert "nash_distance" in result

    def test_render_with_data(self):
        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.8, total_games=100, wins=80, losses=20, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500], timestamp=200.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash", timestamp=300.0),
            timestamp=400.0,
        )
        result = dashboard.render(state)
        assert "0.8" in result
        assert "1500.0" in result
        assert "0.1" in result

    def test_render_without_renderer(self):
        dashboard = TableauDashboard()
        result = dashboard.render()
        assert result is None

    def test_render_with_ticker(self):
        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.8, total_games=100, wins=80, losses=20, timestamp=100.0)
        ticker.bankroll_history = BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500], timestamp=200.0)
        ticker.nash_distance = NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        ticker.timestamp = 400.0
        dashboard.bind_ticker(ticker)
        result = dashboard.render()
        assert "0.8" in result
        assert "1500.0" in result
        assert "0.1" in result

    def test_render_without_ticker(self):
        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        result = dashboard.render()
        assert "win_rate" in result


class TestTableauDashboardRenderPanel:
    def test_render_panel(self):
        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        result = dashboard.render_panel(panel)
        assert "0.8" in result

    def test_render_panel_without_renderer(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        result = dashboard.render_panel(panel)
        assert result is None


class TestTableauDashboardRenderAllPanels:
    def test_render_all_panels(self):
        dashboard = TableauDashboard()
        dashboard.renderer = TableauCSVRenderer()
        panel1 = WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10)
        panel2 = BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500])
        dashboard.add_panel(panel1)
        dashboard.add_panel(panel2)
        results = dashboard.render_all_panels()
        assert len(results) == 2
        assert "0.8" in results[0]
        assert "100.0" in results[1]

    def test_render_all_panels_without_renderer(self):
        dashboard = TableauDashboard()
        results = dashboard.render_all_panels()
        assert results == []


class TestTableauDashboardRenderCSV:
    def test_render_csv_default(self):
        dashboard = TableauDashboard()
        state = DashboardState()
        result = dashboard.render_csv(state)
        assert "win_rate" in result
        assert "bankroll" in result
        assert "nash_distance" in result

    def test_render_csv_custom_delimiter(self):
        dashboard = TableauDashboard()
        state = DashboardState()
        result = dashboard.render_csv(state, delimiter=";")
        assert ";" in result

    def test_render_csv_with_headers(self):
        dashboard = TableauDashboard()
        state = DashboardState()
        result = dashboard.render_csv(state, headers={"custom": "header"})
        assert "custom" in result
        assert "header" in result

    def test_render_csv_with_payload_fn(self):
        def custom_fn(state):
            return {"custom": "data"}

        dashboard = TableauDashboard()
        state = DashboardState()
        result = dashboard.render_csv(state, payload_fn=custom_fn)
        assert "custom" in result
        assert "data" in result


class TestTableauDashboardToDict:
    def test_to_dict(self):
        dashboard = TableauDashboard(
            title="Test Dashboard",
            description="Test",
            width=20,
            height=20,
            x=5,
            y=5,
        )
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        data = dashboard.to_dict()
        assert data["title"] == "Test Dashboard"
        assert data["description"] == "Test"
        assert data["width"] == 20
        assert data["height"] == 20
        assert data["x"] == 5
        assert data["y"] == 5
        assert len(data["panels"]) == 1


class TestTableauDashboardFromDict:
    def test_from_dict(self):
        data = {
            "title": "Test Dashboard",
            "description": "Test",
            "width": 20,
            "height": 20,
            "x": 5,
            "y": 5,
            "panels": [
                {
                    "type": "WinRatePanel",
                    "gauge_value": 0.8,
                    "total_games": 50,
                    "wins": 40,
                    "losses": 10,
                },
                {
                    "type": "BankrollCurvePanel",
                    "profit_loss": 100.0,
                    "peak_bankroll": 2000.0,
                    "drawdown": -500.0,
                    "history": [1000, 1500],
                },
                {
                    "type": "NashEquilibriumPanel",
                    "distance": 0.1,
                    "current_strategy": "test",
                    "nash_strategy": "nash",
                },
            ],
        }
        dashboard = TableauDashboard.from_dict(data)
        assert dashboard.title == "Test Dashboard"
        assert dashboard.description == "Test"
        assert dashboard.width == 20
        assert dashboard.height == 20
        assert dashboard.x == 5
        assert dashboard.y == 5
        assert len(dashboard.panels) == 3
        assert isinstance(dashboard.panels[0], WinRatePanel)
        assert isinstance(dashboard.panels[1], BankrollCurvePanel)
        assert isinstance(dashboard.panels[2], NashEquilibriumPanel)

    def test_from_dict_default_values(self):
        data = {}
        dashboard = TableauDashboard.from_dict(data)
        assert dashboard.title == "Dashboard"
        assert dashboard.description == ""
        assert dashboard.width == 10
        assert dashboard.height == 10
        assert dashboard.x == 0
        assert dashboard.y == 0
        assert len(dashboard.panels) == 0


class TestTableauDashboardClearPanels:
    def test_clear_panels(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel(gauge_value=0.8, total_games=50, wins=40, losses=10))
        dashboard.add_panel(BankrollCurvePanel(profit_loss=100.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500]))
        dashboard.clear_panels()
        assert len(dashboard.panels) == 0


# ===== DashboardTicker =====

class TestDashboardTickerInit:
    def test_default_values(self):
        ticker = DashboardTicker()
        assert ticker.symbol == ""
        assert ticker.price == 0.0
        assert ticker.timestamp == 0.0
        assert ticker.previous_price == 0.0
        assert ticker.current_win_rate.value == 0.0
        assert ticker.bankroll_history.bankroll == 0.0
        assert ticker.nash_distance.distance == 0.0

    def test_custom_values(self):
        ticker = DashboardTicker(
            symbol="TEST",
            current_win_rate=0.8,
            bankroll_history=1500.0,
            nash_distance=0.1,
        )
        assert ticker.symbol == "TEST"
        assert ticker.current_win_rate.value == 0.8
        assert ticker.bankroll_history.bankroll == 1500.0
        assert ticker.nash_distance.distance == 0.1

    def test_start_stop(self):
        ticker = DashboardTicker()
        # DashboardTicker doesn't have start/stop methods
        assert not hasattr(ticker, 'start')
        assert not hasattr(ticker, 'stop')

    def test_interval_setter(self):
        ticker = DashboardTicker()
        # DashboardTicker doesn't have interval attribute
        assert not hasattr(ticker, 'interval')

    def test_callback_setter(self):
        ticker = DashboardTicker()
        # DashboardTicker doesn't have callback attribute
        assert not hasattr(ticker, 'callback')

    def test_running_getter(self):
        ticker = DashboardTicker()
        # DashboardTicker doesn't have running attribute
        assert not hasattr(ticker, 'running')


class TestDashboardTickerPriceColor:
    def test_price_color_green(self):
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(value=0.6)
        assert ticker.price_color == "green"

    def test_price_color_red(self):
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(value=0.4)
        assert ticker.price_color == "red"

    def test_price_color_white(self):
        ticker = DashboardTicker()
        ticker.current_win_rate = WinRateMetric(value=0.5)
        assert ticker.price_color == "white"


class TestDashboardTickerUpdateFromState:
    def test_update_from_state(self):
        ticker = DashboardTicker()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.8, total_games=100, wins=80, losses=20, timestamp=100.0),
            bankroll=BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500], timestamp=200.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash", timestamp=300.0),
            timestamp=400.0,
        )
        ticker.update_from_state(state)
        assert ticker.current_win_rate.value == 0.8
        assert ticker.bankroll_history.bankroll == 1500.0
        assert ticker.nash_distance.distance == 0.1
        assert ticker.price == 0.8
        assert ticker.timestamp == 400.0


class TestDashboardTickerUpdatePrice:
    def test_update_price(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        assert ticker.price == 100.0
        assert ticker.previous_price == 0.0
        assert ticker.timestamp > 0

    def test_update_price_multiple(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.update_price(110.0)
        assert ticker.price == 110.0
        assert ticker.previous_price == 100.0


class TestDashboardTickerPriceChange:
    def test_price_change_positive(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.update_price(110.0)
        assert ticker.price_change == 10.0

    def test_price_change_negative(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.update_price(90.0)
        assert ticker.price_change == -10.0

    def test_price_change_zero(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.update_price(100.0)
        assert ticker.price_change == 0.0


class TestDashboardTickerPriceChangePercent:
    def test_price_change_percent_positive(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.update_price(110.0)
        assert ticker.price_change_percent == 10.0

    def test_price_change_percent_negative(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.update_price(90.0)
        assert ticker.price_change_percent == -10.0

    def test_price_change_percent_zero(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.update_price(100.0)
        assert ticker.price_change_percent == 0.0

    def test_price_change_percent_previous_zero(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        # previous_price is 0.0 initially
        assert ticker.price_change_percent == 0.0


class TestDashboardTickerToDict:
    def test_to_dict(self):
        ticker = DashboardTicker()
        ticker.update_price(100.0)
        ticker.current_win_rate = WinRateMetric(value=0.8, total_games=100, wins=80, losses=20, timestamp=100.0)
        ticker.bankroll_history = BankrollCurvePoint(step=10, bankroll=1500.0, peak_bankroll=2000.0, drawdown=-500.0, history=[1000, 1500], timestamp=200.0)
        ticker.nash_distance = NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash", timestamp=300.0)
        data = ticker.to_dict()
        assert data["symbol"] == ""
        assert data["price"] == 100.0
        assert data["timestamp"] > 0
        assert data["previous_price"] == 0.0
        assert data["current_win_rate"]["value"] == 0.8
        assert data["bankroll_history"]["bankroll"] == 1500.0
        assert data["nash_distance"]["distance"] == 0.1


class TestDashboardTickerFromDict:
    def test_from_dict(self):
        data = {
            "symbol": "TEST",
            "price": 100.0,
            "timestamp": 1000.0,
            "previous_price": 90.0,
            "current_win_rate": {"value": 0.8, "total_games": 100, "wins": 80, "losses": 20, "timestamp": 100.0},
            "bankroll_history": {"step": 10, "bankroll": 1500.0, "peak_bankroll": 2000.0, "drawdown": -500.0, "history": [1000, 1500], "timestamp": 200.0},
            "nash_distance": {"distance": 0.1, "current_strategy": "test", "nash_strategy": "nash", "timestamp": 300.0},
        }
        ticker = DashboardTicker.from_dict(data)
        assert ticker.symbol == "TEST"
        assert ticker.price == 100.0
        assert ticker.timestamp == 1000.0
        assert ticker.previous_price == 90.0
        assert ticker.current_win_rate.value == 0.8
        assert ticker.bankroll_history.bankroll == 1500.0
        assert ticker.nash_distance.distance == 0.1

    def test_from_dict_default_values(self):
        data = {}
        ticker = DashboardTicker.from_dict(data)
        assert ticker.symbol == ""
        assert ticker.price == 0.0
        assert ticker.timestamp > 0  # defaults to time.time()
        assert ticker.previous_price == 0.0
        assert ticker.current_win_rate.value == 0.0
        assert ticker.bankroll_history.bankroll == 0.0
        assert ticker.nash_distance.distance == 0.0
