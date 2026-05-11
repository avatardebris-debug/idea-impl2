"""Tests for src.dashboard.renderers."""

import pytest
from src.dashboard.renderers import (
    TableauRenderer,
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)
from src.dashboard.panels import (
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
from src.dashboard.tickers import DashboardTicker


# ===== TableauRenderer =====

class TestTableauRenderer:
    def test_render_raises_not_implemented(self):
        renderer = TableauRenderer()
        with pytest.raises(NotImplementedError):
            renderer.render(DashboardState())

    def test_render_panel_raises_not_implemented(self):
        renderer = TableauRenderer()
        panel = WinRatePanel()
        with pytest.raises(NotImplementedError):
            renderer.render_panel(panel)

    def test_render_panels_calls_render_panel(self):
        renderer = TableauRenderer()
        panels = [WinRatePanel(), BankrollCurvePanel()]
        # Should raise NotImplementedError from render_panel
        with pytest.raises(NotImplementedError):
            renderer.render_panels(panels)


# ===== TableauCSVRenderer =====

class TestTableauCSVRenderer:
    def test_render(self):
        renderer = TableauCSVRenderer()
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6, total_games=100, wins=60, losses=40),
            bankroll=BankrollCurvePoint(step=10, bankroll=150.0, peak_bankroll=200.0, drawdown=-50.0),
            nash_distance=NashEquilibriumShift(distance=0.1, current_strategy="test", nash_strategy="nash"),
            timestamp=1000.0,
        )
        csv_str = renderer.render(state)
        assert "timestamp" in csv_str
        assert "0.6" in csv_str
        assert "100" in csv_str
        assert "150.0" in csv_str
        assert "0.1" in csv_str

    def test_render_with_custom_delimiter(self):
        renderer = TableauCSVRenderer(delimiter=";")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = renderer.render(state)
        assert ";" in csv_str
        assert "," not in csv_str

    def test_render_panel(self):
        renderer = TableauCSVRenderer()
        panel = WinRatePanel()
        ticker = DashboardTicker(symbol="TICKER")
        ticker.current_win_rate = WinRateMetric(value=0.6, total_games=100, wins=60, losses=40)
        ticker.bankroll_history = BankrollCurvePoint(step=1, bankroll=100.0)
        ticker.nash_distance = NashEquilibriumShift(distance=0.1)
        panel.bind_ticker(ticker)
        csv_str = renderer.render_panel(panel)
        assert "win_rate" in csv_str
        assert "0.6" in csv_str

    def test_render_without_header(self):
        renderer = TableauCSVRenderer(include_header=False)
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = renderer.render(state)
        assert "timestamp" not in csv_str


# ===== TableauRESTRenderer =====

class TestTableauRESTRenderer:
    def test_render(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        renderer = TableauRESTRenderer(url="http://test.com", token="test_token")
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        renderer.render(state)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["headers"]["Authorization"] == "Bearer test_token"
        assert call_kwargs[1]["json"]["timestamp"] == state.timestamp

    def test_render_with_custom_headers(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        renderer = TableauRESTRenderer(
            url="http://test.com",
            token="test_token",
            headers={"X-Custom": "value"},
        )
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        renderer.render(state)

        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["headers"]["X-Custom"] == "value"

    def test_render_with_custom_payload(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        def custom_payload(state):
            return {"custom": state.win_rate.value}

        renderer = TableauRESTRenderer(
            url="http://test.com",
            token="test_token",
            payload_fn=custom_payload,
        )
        state = DashboardState(
            win_rate=WinRateMetric(value=0.7),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        renderer.render(state)

        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["custom"] == 0.7


# ===== TableauDashboard =====

class TestTableauDashboard:
    def test_default_values(self):
        dashboard = TableauDashboard()
        assert dashboard.title == "Dashboard"
        assert dashboard.description == ""
        assert dashboard.width == 10
        assert dashboard.height == 10
        assert dashboard.x == 0
        assert dashboard.y == 0
        assert dashboard.panels == []

    def test_custom_values(self):
        dashboard = TableauDashboard(
            title="Test Dashboard",
            description="A test dashboard",
            width=20,
            height=20,
            x=5,
            y=5,
        )
        assert dashboard.title == "Test Dashboard"
        assert dashboard.description == "A test dashboard"
        assert dashboard.width == 20
        assert dashboard.height == 20
        assert dashboard.x == 5
        assert dashboard.y == 5

    def test_add_panel(self):
        dashboard = TableauDashboard()
        panel = WinRatePanel()
        dashboard.add_panel(panel)
        assert len(dashboard.panels) == 1
        assert dashboard.panels[0] is panel

    def test_render(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        dashboard.add_panel(NashEquilibriumPanel())
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        result = dashboard.render(state)
        assert isinstance(result, dict)
        assert "title" in result
        assert "description" in result
        assert "width" in result
        assert "height" in result
        assert "x" in result
        assert "y" in result
        assert "panels" in result
        assert len(result["panels"]) == 3

    def test_render_csv(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        dashboard.add_panel(BankrollCurvePanel())
        dashboard.add_panel(NashEquilibriumPanel())
        state = DashboardState(
            win_rate=WinRateMetric(value=0.6),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state)
        assert "win_rate" in csv_str
        assert "bankroll" in csv_str
        assert "nash_distance" in csv_str

    def test_render_csv_with_custom_delimiter(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state, delimiter=";")
        assert ";" in csv_str

    def test_render_csv_with_custom_headers(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state, headers={"X-Custom": "value"})
        assert "X-Custom" in csv_str

    def test_render_csv_with_custom_payload(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())

        def custom_payload(state):
            return {"custom": state.win_rate.value}

        state = DashboardState(
            win_rate=WinRateMetric(value=0.7),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state, payload_fn=custom_payload)
        assert "custom" in csv_str
        assert "0.7" in csv_str

    def test_render_csv_with_custom_delimiter_and_headers(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state, delimiter=";", headers={"X-Custom": "value"})
        assert ";" in csv_str
        assert "X-Custom" in csv_str

    def test_render_csv_with_custom_delimiter_and_payload(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())

        def custom_payload(state):
            return {"custom": state.win_rate.value}

        state = DashboardState(
            win_rate=WinRateMetric(value=0.7),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state, delimiter=";", payload_fn=custom_payload)
        assert ";" in csv_str
        assert "custom" in csv_str
        assert "0.7" in csv_str

    def test_render_csv_with_custom_headers_and_payload(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())

        def custom_payload(state):
            return {"custom": state.win_rate.value}

        state = DashboardState(
            win_rate=WinRateMetric(value=0.7),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state, headers={"X-Custom": "value"}, payload_fn=custom_payload)
        assert "X-Custom" in csv_str
        assert "custom" in csv_str
        assert "0.7" in csv_str

    def test_render_csv_with_all_custom_options(self):
        dashboard = TableauDashboard()
        dashboard.add_panel(WinRatePanel())

        def custom_payload(state):
            return {"custom": state.win_rate.value}

        state = DashboardState(
            win_rate=WinRateMetric(value=0.7),
            bankroll=BankrollCurvePoint(),
            nash_distance=NashEquilibriumShift(),
        )
        csv_str = dashboard.render_csv(state, delimiter=";", headers={"X-Custom": "value"}, payload_fn=custom_payload)
        assert ";" in csv_str
        assert "X-Custom" in csv_str
        assert "custom" in csv_str
        assert "0.7" in csv_str
