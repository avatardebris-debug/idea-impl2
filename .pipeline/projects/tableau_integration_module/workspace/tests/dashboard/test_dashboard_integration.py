"""Integration tests for the Tableau dashboard module.

Tests the full pipeline: DataSource -> Ticker -> Panels -> Dashboard -> Renderer.
"""

import csv
import io
import json
import time
import pytest
from unittest.mock import patch, MagicMock

from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)
from src.dashboard.tickers import DashboardTicker
from src.dashboard.panels import (
    DashboardPanel,
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
from src.dashboard.layout import DashboardBoard
from src.dashboard.data_source import DashboardDataSource
from src.dashboard.visualization import (
    TableauRenderer,
    TableauCSVRenderer,
    TableauRESTRenderer,
    TableauDashboard,
)


# ===== DataSource -> Ticker Integration =====

class TestDataSourceToTicker:
    """Test that DashboardDataSource correctly updates the ticker."""

    def test_force_update_populates_win_rate(self):
        ds = DashboardDataSource(seed=42)
        state_dict = ds.force_update()
        assert state_dict["win_rate"]["value"] > 0.0
        assert state_dict["win_rate"]["total_games"] >= 1
        assert state_dict["win_rate"]["wins"] >= 0
        assert state_dict["win_rate"]["losses"] >= 0

    def test_force_update_populates_bankroll(self):
        ds = DashboardDataSource(seed=42)
        state_dict = ds.force_update()
        assert state_dict["bankroll"]["step"] >= 1
        assert state_dict["bankroll"]["bankroll"] >= 0.0
        assert state_dict["bankroll"]["peak_bankroll"] >= 0.0
        assert isinstance(state_dict["bankroll"]["history"], list)

    def test_force_update_populates_nash(self):
        ds = DashboardDataSource(seed=42)
        state_dict = ds.force_update()
        assert state_dict["nash_distance"]["distance"] > 0.0
        assert state_dict["nash_distance"]["current_strategy"] in ["bluff", "call", "fold"]
        assert state_dict["nash_distance"]["nash_strategy"] == "nash_equilibrium"

    def test_force_update_multiple_times(self):
        ds = DashboardDataSource(seed=42)
        state1 = ds.force_update()
        state2 = ds.force_update()
        assert state2["win_rate"]["total_games"] == state1["win_rate"]["total_games"] + 1
        assert state2["bankroll"]["step"] == state1["bankroll"]["step"] + 1

    def test_get_state_returns_dashboard_state(self):
        ds = DashboardDataSource(seed=42)
        ds.force_update()
        state = ds.get_state()
        assert isinstance(state, DashboardState)
        assert isinstance(state.win_rate, WinRateMetric)
        assert isinstance(state.bankroll, BankrollCurvePoint)
        assert isinstance(state.nash_distance, NashEquilibriumShift)

    def test_callbacks_are_invoked(self):
        ds = DashboardDataSource(seed=42)
        received_states = []

        def callback(state):
            received_states.append(state)

        ds.register_callback(callback)
        ds.force_update()
        assert len(received_states) == 1
        assert isinstance(received_states[0], DashboardState)

    def test_callbacks_receive_correct_state(self):
        ds = DashboardDataSource(seed=42)
        received_state = None

        def callback(state):
            nonlocal received_state
            received_state = state

        ds.register_callback(callback)
        ds.force_update()
        assert received_state is not None
        assert received_state.win_rate.value == ds.ticker.current_win_rate.value
        assert received_state.bankroll.bankroll == ds.ticker.bankroll_history.bankroll
        assert received_state.nash_distance.distance == ds.ticker.nash_distance.distance

    def test_ticker_price_matches_win_rate(self):
        ds = DashboardDataSource(seed=42)
        ds.force_update()
        assert ds.ticker.price == ds.ticker.current_win_rate.value


# ===== Ticker -> Panel Integration =====

class TestTickerToPanel:
    """Test that panels correctly update from a ticker."""

    def test_win_rate_panel_updates_from_ticker(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.65, total_games=100, wins=65, losses=35)
        panel = WinRatePanel()
        panel.update(ticker)
        assert panel.gauge_value == 0.65
        assert panel.total_games == 100
        assert panel.wins == 65
        assert panel.losses == 35

    def test_win_rate_panel_clamps_gauge(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=1.5)  # out of range
        panel = WinRatePanel()
        panel.update(ticker)
        assert panel.gauge_value == 1.0  # clamped

    def test_win_rate_panel_negative_gauge(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=-0.1)  # out of range
        panel = WinRatePanel()
        panel.update(ticker)
        assert panel.gauge_value == 0.0  # clamped

    def test_win_rate_panel_confidence_interval(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.5, total_games=100)
        panel = WinRatePanel()
        panel.update(ticker)
        lo, hi = panel.confidence_interval
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0
        assert lo <= hi

    def test_win_rate_panel_trend_arrow_up(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.4, total_games=10)
        panel = WinRatePanel()
        panel.update(ticker)
        # Set previous value lower
        ticker.current_win_rate = WinRateMetric(value=0.3, total_games=10)
        panel._ticker = ticker
        panel.update(ticker)
        assert panel.trend_arrow == "↑"

    def test_win_rate_panel_trend_arrow_down(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.6, total_games=10)
        panel = WinRatePanel()
        panel.update(ticker)
        # Set previous value higher
        ticker.current_win_rate = WinRateMetric(value=0.7, total_games=10)
        panel._ticker = ticker
        panel.update(ticker)
        assert panel.trend_arrow == "↓"

    def test_bankroll_panel_updates_from_ticker(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.bankroll_history = BankrollCurvePoint(
            step=5,
            bankroll=1200.0,
            peak_bankroll=1500.0,
            drawdown=-300.0,
            history=[1000, 1100, 1200, 1300, 1400, 1500, 1200],
        )
        panel = BankrollCurvePanel()
        panel.update(ticker)
        assert panel.current_bankroll == 1200.0
        assert panel.peak_bankroll == 1500.0
        assert panel.drawdown == -300.0
        assert len(panel.sparkline) == 7

    def test_bankroll_panel_profit_loss(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.bankroll_history = BankrollCurvePoint(bankroll=1200.0)
        panel = BankrollCurvePanel(initial_bankroll=1000.0)
        panel.update(ticker)
        assert panel.profit_loss == 200.0

    def test_nash_panel_updates_from_ticker(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(
            distance=0.03,
            current_strategy="bluff",
            nash_strategy="nash_equilibrium",
        )
        panel = NashEquilibriumPanel()
        panel.update(ticker)
        assert panel.distance == 0.03
        assert panel.current_strategy == "bluff"
        assert panel.nash_strategy == "nash_equilibrium"

    def test_nash_panel_heatmap_color_green(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.02)
        panel = NashEquilibriumPanel()
        panel.update(ticker)
        assert panel.heatmap_color == "green"

    def test_nash_panel_heatmap_color_yellow(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.1)
        panel = NashEquilibriumPanel()
        panel.update(ticker)
        assert panel.heatmap_color == "yellow"

    def test_nash_panel_heatmap_color_red(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.2)
        panel = NashEquilibriumPanel()
        panel.update(ticker)
        assert panel.heatmap_color == "red"

    def test_panel_bind_ticker(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.7)
        panel = WinRatePanel()
        panel.bind_ticker(ticker)
        panel.update_from_bound_ticker()
        assert panel.gauge_value == 0.7

    def test_panel_render_data_includes_ticker(self):
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.5)
        panel = WinRatePanel()
        panel.update(ticker)
        data = panel.render_data()
        assert "ticker" in data
        assert data["ticker"]["current_win_rate"]["value"] == 0.5


# ===== Panel -> Dashboard Integration =====

class TestPanelToDashboard:
    """Test that panels integrate correctly with DashboardBoard."""

    def test_board_adds_panel(self):
        board = DashboardBoard()
        panel = WinRatePanel()
        board.add_panel(panel)
        assert len(board.panels) == 1
        assert board.panels[0] is panel

    def test_board_removes_panel(self):
        board = DashboardBoard()
        panel = WinRatePanel()
        board.add_panel(panel)
        board.remove_panel(panel)
        assert len(board.panels) == 0

    def test_board_get_panel_at(self):
        board = DashboardBoard(rows=2, columns=2)
        p1 = WinRatePanel()
        p2 = BankrollCurvePanel()
        board.add_panel(p1)
        board.add_panel(p2)
        assert board.get_panel_at(0, 0) is p1
        assert board.get_panel_at(0, 1) is p2
        assert board.get_panel_at(1, 0) is None

    def test_board_grid_dimensions(self):
        board = DashboardBoard(rows=3, columns=4)
        assert board.get_grid_dimensions() == (3, 4)

    def test_board_set_grid_dimensions(self):
        board = DashboardBoard(rows=1, columns=1)
        board.set_grid_dimensions(2, 2)
        assert board.rows == 2
        assert board.columns == 2

    def test_board_set_grid_dimensions_too_small(self):
        board = DashboardBoard(rows=2, columns=2)
        board.add_panel(WinRatePanel())
        board.add_panel(BankrollCurvePanel())
        board.add_panel(NashEquilibriumPanel())
        with pytest.raises(ValueError):
            board.set_grid_dimensions(1, 1)

    def test_board_layout_info(self):
        board = DashboardBoard(title="Test Board", rows=2, columns=2)
        board.add_panel(WinRatePanel())
        board.add_panel(BankrollCurvePanel())
        info = board.get_layout_info()
        assert info["title"] == "Test Board"
        assert info["rows"] == 2
        assert info["columns"] == 2
        assert info["panel_count"] == 2
        assert len(info["panels"]) == 2

    def test_board_serialization_roundtrip(self):
        board = DashboardBoard(title="RoundTrip", rows=1, columns=2)
        board.add_panel(WinRatePanel())
        board.add_panel(BankrollCurvePanel())
        data = board.to_dict()
        restored = DashboardBoard.from_dict(data)
        assert restored.title == "RoundTrip"
        assert restored.rows == 1
        assert restored.columns == 2
        assert len(restored.panels) == 2
        assert isinstance(restored.panels[0], WinRatePanel)
        assert isinstance(restored.panels[1], BankrollCurvePanel)


# ===== Full Pipeline: DataSource -> Ticker -> Panels -> Dashboard =====

class TestFullPipeline:
    """Test the complete data flow from DataSource through to Dashboard."""

    def test_full_pipeline_data_flow(self):
        """Test that data flows correctly from DataSource to Dashboard."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        ticker = ds.ticker
        assert ticker.current_win_rate.value > 0.0
        assert ticker.bankroll_history.bankroll >= 0.0
        assert ticker.nash_distance.distance > 0.0

        # Create panels
        wr_panel = WinRatePanel()
        br_panel = BankrollCurvePanel()
        ne_panel = NashEquilibriumPanel()

        # Update panels from ticker
        wr_panel.update(ticker)
        br_panel.update(ticker)
        ne_panel.update(ticker)

        # Verify panel data
        assert wr_panel.gauge_value == ticker.current_win_rate.value
        assert br_panel.current_bankroll == ticker.bankroll_history.bankroll
        assert ne_panel.distance == ticker.nash_distance.distance

        # Create dashboard
        dashboard = TableauDashboard()
        dashboard.add_panel(wr_panel)
        dashboard.add_panel(br_panel)
        dashboard.add_panel(ne_panel)

        # Verify dashboard has panels
        assert len(dashboard.panels) == 3

    def test_full_pipeline_with_board(self):
        """Test full pipeline with DashboardBoard."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        ticker = ds.ticker
        board = DashboardBoard(rows=2, columns=2)

        wr_panel = WinRatePanel()
        wr_panel.update(ticker)
        board.add_panel(wr_panel)

        br_panel = BankrollCurvePanel()
        br_panel.update(ticker)
        board.add_panel(br_panel)

        ne_panel = NashEquilibriumPanel()
        ne_panel.update(ticker)
        board.add_panel(ne_panel)

        dashboard = TableauDashboard()
        dashboard.add_board(board)

        assert len(dashboard.panels) == 3

    def test_full_pipeline_multiple_updates(self):
        """Test that multiple updates produce different data."""
        ds = DashboardDataSource(seed=42)
        state1 = ds.force_update()
        state2 = ds.force_update()

        assert state1["win_rate"]["total_games"] == 1
        assert state2["win_rate"]["total_games"] == 2
        assert state1["bankroll"]["step"] == 1
        assert state2["bankroll"]["step"] == 2

    def test_full_pipeline_with_callbacks(self):
        """Test that callbacks receive correct data at each step."""
        ds = DashboardDataSource(seed=42)
        received_states = []

        def callback(state):
            received_states.append(state)

        ds.register_callback(callback)
        ds.force_update()

        assert len(received_states) == 1
        assert received_states[0].win_rate.value == ds.ticker.current_win_rate.value
        assert received_states[0].bankroll.bankroll == ds.ticker.bankroll_history.bankroll

    def test_full_pipeline_ticker_to_dict(self):
        """Test that ticker serialization works correctly."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        ticker_dict = ds.ticker.to_dict()
        assert "symbol" in ticker_dict
        assert "price" in ticker_dict
        assert "timestamp" in ticker_dict
        assert "current_win_rate" in ticker_dict
        assert "bankroll_history" in ticker_dict
        assert "nash_distance" in ticker_dict

    def test_full_pipeline_state_to_dict(self):
        """Test that DashboardState serialization works correctly."""
        ds = DashboardDataSource(seed=42)
        state_dict = ds.force_update()

        assert "win_rate" in state_dict
        assert "bankroll" in state_dict
        assert "nash_distance" in state_dict
        assert "timestamp" in state_dict

    def test_full_pipeline_roundtrip(self):
        """Test that data can be serialized and deserialized correctly."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        # Serialize
        state_dict = ds.get_state().to_dict()

        # Deserialize
        restored_state = DashboardState.from_dict(state_dict)

        assert restored_state.win_rate.value == ds.ticker.current_win_rate.value
        assert restored_state.bankroll.bankroll == ds.ticker.bankroll_history.bankroll
        assert restored_state.nash_distance.distance == ds.ticker.nash_distance.distance


# ===== Visualization Integration =====

class TestVisualizationIntegration:
    """Test that visualization components work correctly with dashboard data."""

    def test_tableau_renderer_creates_dashboard(self):
        """Test that TableauRenderer creates a valid dashboard."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        renderer = TableauRenderer()
        dashboard = renderer.create_dashboard()

        assert isinstance(dashboard, TableauDashboard)
        assert len(dashboard.panels) > 0

    def test_csv_renderer_outputs_valid_csv(self):
        """Test that TableauCSVRenderer outputs valid CSV."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        renderer = TableauCSVRenderer()
        dashboard = renderer.create_dashboard()

        output = renderer.render(dashboard)
        assert isinstance(output, str)
        assert len(output) > 0

        # Parse CSV to verify it's valid
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) > 0

    def test_csv_renderer_contains_expected_columns(self):
        """Test that CSV output contains expected columns."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        renderer = TableauCSVRenderer()
        dashboard = renderer.create_dashboard()

        output = renderer.render(dashboard)
        reader = csv.reader(io.StringIO(output))
        header = next(reader)

        assert "symbol" in header
        assert "title" in header
        assert "type" in header

    def test_rest_renderer_returns_json(self):
        """Test that TableauRESTRenderer returns valid JSON."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        renderer = TableauRESTRenderer()
        dashboard = renderer.create_dashboard()

        output = renderer.render(dashboard)
        data = json.loads(output)

        assert "panels" in data
        assert "layout" in data
        assert len(data["panels"]) > 0

    def test_rest_renderer_panel_data(self):
        """Test that REST renderer panel data is correct."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        renderer = TableauRESTRenderer()
        dashboard = renderer.create_dashboard()

        output = renderer.render(dashboard)
        data = json.loads(output)

        panel = data["panels"][0]
        assert "symbol" in panel
        assert "title" in panel
        assert "render_data" in panel

    def test_dashboard_serialization(self):
        """Test that TableauDashboard serialization works."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        dashboard = TableauDashboard()
        wr_panel = WinRatePanel()
        wr_panel.update(ds.ticker)
        dashboard.add_panel(wr_panel)

        data = dashboard.to_dict()
        assert "panels" in data
        assert "layout" in data
        assert len(data["panels"]) == 1

    def test_dashboard_deserialization(self):
        """Test that TableauDashboard deserialization works."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        dashboard = TableauDashboard()
        wr_panel = WinRatePanel()
        wr_panel.update(ds.ticker)
        dashboard.add_panel(wr_panel)

        data = dashboard.to_dict()
        restored = TableauDashboard.from_dict(data)

        assert len(restored.panels) == 1
        assert isinstance(restored.panels[0], WinRatePanel)

    def test_visual_encoding_integration(self):
        """Test that visual encoding is correctly computed for all panel types."""
        ds = DashboardDataSource(seed=42)
        ds.force_update()

        wr_panel = WinRatePanel()
        wr_panel.update(ds.ticker)
        wr_encoding = wr_panel.get_visual_encoding()
        assert wr_encoding["type"] == "gauge"
        assert "color" in wr_encoding

        br_panel = BankrollCurvePanel()
        br_panel.update(ds.ticker)
        br_encoding = br_panel.get_visual_encoding()
        assert br_encoding["type"] == "sparkline"
        assert "color" in br_encoding

        ne_panel = NashEquilibriumPanel()
        ne_panel.update(ds.ticker)
        ne_encoding = ne_panel.get_visual_encoding()
        assert ne_encoding["type"] == "heatmap"
        assert "color" in ne_encoding


# ===== Edge Cases and Error Handling =====

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_board(self):
        """Test that an empty board works correctly."""
        board = DashboardBoard()
        assert len(board.panels) == 0
        assert board.get_layout_info()["panel_count"] == 0

    def test_panel_with_no_ticker(self):
        """Test that panel handles missing ticker gracefully."""
        panel = WinRatePanel()
        data = panel.render_data()
        assert "ticker" not in data or data.get("ticker") is None

    def test_win_rate_panel_zero_games(self):
        """Test win rate panel with zero games."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.0, total_games=0)
        panel = WinRatePanel()
        panel.update(ticker)
        assert panel.gauge_value == 0.0

    def test_bankroll_panel_zero_bankroll(self):
        """Test bankroll panel with zero bankroll."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.bankroll_history = BankrollCurvePoint(bankroll=0.0, peak_bankroll=0.0)
        panel = BankrollCurvePanel()
        panel.update(ticker)
        assert panel.current_bankroll == 0.0

    def test_nash_panel_zero_distance(self):
        """Test Nash panel with zero distance."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.nash_distance = NashEquilibriumShift(distance=0.0)
        panel = NashEquilibriumPanel()
        panel.update(ticker)
        assert panel.distance == 0.0
        assert panel.heatmap_color == "green"

    def test_board_with_max_panels(self):
        """Test board with maximum number of panels for its grid."""
        board = DashboardBoard(rows=2, columns=2)
        for i in range(4):
            board.add_panel(WinRatePanel())
        assert len(board.panels) == 4

    def test_board_with_more_panels_than_cells(self):
        """Test that board raises error when panels exceed grid cells."""
        board = DashboardBoard(rows=1, columns=1)
        board.add_panel(WinRatePanel())
        board.add_panel(BankrollCurvePanel())
        with pytest.raises(ValueError):
            board.set_grid_dimensions(1, 1)

    def test_ticker_from_dict(self):
        """Test ticker deserialization."""
        ticker = DashboardTicker(symbol="TEST")
        ticker.current_win_rate = WinRateMetric(value=0.5, total_games=100)
        ticker.bankroll_history = BankrollCurvePoint(bankroll=1000.0)
        ticker.nash_distance = NashEquilibriumShift(distance=0.1)
        ticker.price = 0.5
        ticker.timestamp = time.time()

        ticker_dict = ticker.to_dict()
        restored = DashboardTicker.from_dict(ticker_dict)

        assert restored.symbol == "TEST"
        assert restored.current_win_rate.value == 0.5
        assert restored.bankroll_history.bankroll == 1000.0
        assert restored.nash_distance.distance == 0.1

    def test_panel_from_dict(self):
        """Test panel deserialization."""
        panel = WinRatePanel(
            symbol="TEST",
            title="Test Panel",
            gauge_value=0.5,
            width=10,
            height=10,
        )
        panel_dict = panel.to_dict()
        restored = WinRatePanel.from_dict(panel_dict)

        assert restored.symbol == "TEST"
        assert restored.title == "Test Panel"
        assert restored.width == 10
        assert restored.height == 10

    def test_state_from_dict(self):
        """Test DashboardState deserialization."""
        state = DashboardState(
            win_rate=WinRateMetric(value=0.5, total_games=100),
            bankroll=BankrollCurvePoint(bankroll=1000.0),
            nash_distance=NashEquilibriumShift(distance=0.1),
        )
        state_dict = state.to_dict()
        restored = DashboardState.from_dict(state_dict)

        assert restored.win_rate.value == 0.5
        assert restored.bankroll.bankroll == 1000.0
        assert restored.nash_distance.distance == 0.1


# ===== Threading Integration =====

class TestThreadingIntegration:
    """Test threading-related functionality."""

    def test_data_source_start_stop(self):
        """Test that data source can be started and stopped."""
        ds = DashboardDataSource(seed=42, interval=0.1)
        ds.start()
        time.sleep(0.3)
        ds.stop()
        assert not ds._running

    def test_data_source_updates_during_thread(self):
        """Test that data source updates during background thread."""
        ds = DashboardDataSource(seed=42, interval=0.1)
        initial_games = ds.ticker.current_win_rate.total_games
        ds.start()
        time.sleep(0.3)
        ds.stop()
        assert ds.ticker.current_win_rate.total_games > initial_games

    def test_data_source_callbacks_during_thread(self):
        """Test that callbacks are invoked during background updates."""
        ds = DashboardDataSource(seed=42, interval=0.1)
        received_states = []

        def callback(state):
            received_states.append(state)

        ds.register_callback(callback)
        ds.start()
        time.sleep(0.3)
        ds.stop()
        assert len(received_states) > 0


# ===== Comprehensive End-to-End Test =====

class TestComprehensiveEndToEnd:
    """Comprehensive end-to-end test covering the entire dashboard pipeline."""

    def test_complete_dashboard_workflow(self):
        """Test the complete dashboard workflow from data generation to rendering."""
        # 1. Generate data
        ds = DashboardDataSource(seed=42)
        for _ in range(10):
            ds.force_update()

        # 2. Create ticker
        ticker = ds.ticker
        assert ticker.current_win_rate.value > 0.0
        assert ticker.bankroll_history.bankroll >= 0.0

        # 3. Create and update panels
        wr_panel = WinRatePanel()
        br_panel = BankrollCurvePanel()
        ne_panel = NashEquilibriumPanel()

        wr_panel.update(ticker)
        br_panel.update(ticker)
        ne_panel.update(ticker)

        # 4. Verify panel data
        assert wr_panel.gauge_value == ticker.current_win_rate.value
        assert br_panel.current_bankroll == ticker.bankroll_history.bankroll
        assert ne_panel.distance == ticker.nash_distance.distance

        # 5. Create board
        board = DashboardBoard(rows=2, columns=2)
        board.add_panel(wr_panel)
        board.add_panel(br_panel)
        board.add_panel(ne_panel)

        # 6. Create dashboard
        dashboard = TableauDashboard()
        dashboard.add_board(board)

        # 7. Render to CSV
        csv_renderer = TableauCSVRenderer()
        csv_output = csv_renderer.render(dashboard)
        assert len(csv_output) > 0

        # 8. Render to REST
        rest_renderer = TableauRESTRenderer()
        rest_output = rest_renderer.render(dashboard)
        rest_data = json.loads(rest_output)
        assert "panels" in rest_data
        assert len(rest_data["panels"]) == 3

        # 9. Verify serialization roundtrip
        dashboard_dict = dashboard.to_dict()
        restored_dashboard = TableauDashboard.from_dict(dashboard_dict)
        assert len(restored_dashboard.panels) == 3

        # 10. Verify all panel types are present
        panel_types = [type(p).__name__ for p in restored_dashboard.panels]
        assert "WinRatePanel" in panel_types
        assert "BankrollCurvePanel" in panel_types
        assert "NashEquilibriumPanel" in panel_types
