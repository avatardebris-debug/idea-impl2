"""Tests for DashboardBoard, DashboardVizRenderer, and related layout classes.

Covers:
  - DashboardBoard creation and panel management
  - DashboardBoard serialization (to_dict / from_dict)
  - DashboardBoard update_from_ticker
  - DashboardBoard get_panel_by_type
  - DashboardVizRenderer creation and rendering
  - DashboardVizRenderer panel rendering methods
  - DashboardVizRenderer color conversion
  - DashboardVizRenderer empty board handling
"""

import pytest

from src.dashboard.panels import (
    BankrollCurvePanel,
    NashEquilibriumPanel,
    WinRatePanel,
)
from src.dashboard.layout import DashboardBoard
from src.dashboard.viz_renderer import DashboardVizRenderer
from src.vr_scene import VRScene, VRGeometry


# ===== DashboardBoard =====

class TestDashboardBoardCreation:
    def test_default_initialization(self):
        board = DashboardBoard()
        assert board.layout_width == 10.0
        assert board.layout_height == 10.0
        assert board.win_rate_panel is None
        assert board.bankroll_panel is None
        assert board.nash_panel is None
        assert board.panels == []

    def test_custom_initialization(self):
        board = DashboardBoard(layout_width=20.0, layout_height=15.0)
        assert board.layout_width == 20.0
        assert board.layout_height == 15.0

    def test_add_win_rate_panel(self):
        panel = WinRatePanel(
            panel_id="wr1",
            gauge_value=0.6,
            gauge_color="green",
            x=0.0,
            y=0.0,
            width=4.0,
            height=2.0,
        )
        board = DashboardBoard()
        board.add_win_rate_panel(panel)
        assert board.win_rate_panel is panel
        assert len(board.panels) == 1

    def test_add_bankroll_panel(self):
        panel = BankrollCurvePanel(
            panel_id="bk1",
            bankroll_points=[{"value": 1000.0}, {"value": 1100.0}],
            shading_color="blue",
            x=0.0,
            y=0.0,
            width=6.0,
            height=3.0,
        )
        board = DashboardBoard()
        board.add_bankroll_panel(panel)
        assert board.bankroll_panel is panel
        assert len(board.panels) == 1

    def test_add_nash_panel(self):
        panel = NashEquilibriumPanel(
            panel_id="ne1",
            heatmap_values=[[0.5, 0.3], [0.2, 0.8]],
            heatmap_colors=[["white", "red"], ["red", "green"]],
            dimensions=["A", "B"],
            x=0.0,
            y=0.0,
            width=4.0,
            height=4.0,
        )
        board = DashboardBoard()
        board.add_nash_panel(panel)
        assert board.nash_panel is panel
        assert len(board.panels) == 1

    def test_add_all_panel_types(self):
        board = DashboardBoard()
        wr = WinRatePanel(panel_id="wr1", gauge_value=0.5, gauge_color="white")
        bk = BankrollCurvePanel(panel_id="bk1", bankroll_points=[{"value": 100.0}])
        ne = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[[0.5]], heatmap_colors=[["white"]], dimensions=["A"])
        board.add_win_rate_panel(wr)
        board.add_bankroll_panel(bk)
        board.add_nash_panel(ne)
        assert board.win_rate_panel is wr
        assert board.bankroll_panel is bk
        assert board.nash_panel is ne
        assert len(board.panels) == 3


class TestDashboardBoardSerialization:
    def test_to_dict_has_expected_keys(self):
        board = DashboardBoard()
        d = board.to_dict()
        assert "layout_width" in d
        assert "layout_height" in d
        assert "panels" in d
        assert "win_rate_panel" in d
        assert "bankroll_panel" in d
        assert "nash_panel" in d

    def test_to_dict_panels_list(self):
        board = DashboardBoard()
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.5, gauge_color="white")
        board.add_win_rate_panel(panel)
        d = board.to_dict()
        assert len(d["panels"]) == 1
        assert d["panels"][0]["panel_id"] == "wr1"

    def test_from_dict_restores_board(self):
        board = DashboardBoard(layout_width=20.0, layout_height=15.0)
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.6, gauge_color="green")
        board.add_win_rate_panel(panel)
        d = board.to_dict()
        board2 = DashboardBoard.from_dict(d)
        assert board2.layout_width == 20.0
        assert board2.layout_height == 15.0
        assert len(board2.panels) == 1
        assert board2.panels[0].panel_id == "wr1"

    def test_from_dict_with_all_panel_types(self):
        board = DashboardBoard()
        wr = WinRatePanel(panel_id="wr1", gauge_value=0.5, gauge_color="white")
        bk = BankrollCurvePanel(panel_id="bk1", bankroll_points=[{"value": 100.0}])
        ne = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[[0.5]], heatmap_colors=[["white"]], dimensions=["A"])
        board.add_win_rate_panel(wr)
        board.add_bankroll_panel(bk)
        board.add_nash_panel(ne)
        d = board.to_dict()
        board2 = DashboardBoard.from_dict(d)
        assert board2.win_rate_panel is not None
        assert board2.bankroll_panel is not None
        assert board2.nash_panel is not None
        assert board2.win_rate_panel.panel_id == "wr1"
        assert board2.bankroll_panel.panel_id == "bk1"
        assert board2.nash_panel.panel_id == "ne1"

    def test_roundtrip_preserves_data(self):
        board = DashboardBoard(layout_width=12.0, layout_height=8.0)
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.75, gauge_color="green")
        board.add_win_rate_panel(panel)
        d = board.to_dict()
        board2 = DashboardBoard.from_dict(d)
        assert board2.layout_width == 12.0
        assert board2.layout_height == 8.0
        assert board2.win_rate_panel.gauge_value == 0.75
        assert board2.win_rate_panel.gauge_color == "green"


class TestDashboardBoardUpdateFromTicker:
    def test_update_from_ticker_updates_win_rate(self):
        board = DashboardBoard()
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.0, gauge_color="white")
        board.add_win_rate_panel(panel)
        ticker_data = {"current_win_rate": {"value": 0.65, "total_games": 100, "wins": 65, "losses": 35, "timestamp": 100.0}}
        board.update_from_ticker(ticker_data)
        assert board.win_rate_panel.gauge_value == 0.65
        assert board.win_rate_panel.gauge_color == "green"

    def test_update_from_ticker_updates_bankroll(self):
        board = DashboardBoard()
        panel = BankrollCurvePanel(panel_id="bk1", bankroll_points=[], shading_color="blue")
        board.add_bankroll_panel(panel)
        ticker_data = {"bankroll_history": {"bankroll": 1100.0, "peak_bankroll": 1100.0, "drawdown": 0.0, "timestamp": 100.0}}
        board.update_from_ticker(ticker_data)
        assert len(board.bankroll_panel.bankroll_points) == 1
        assert board.bankroll_panel.bankroll_points[0]["value"] == 1100.0

    def test_update_from_ticker_updates_nash(self):
        board = DashboardBoard()
        panel = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[], heatmap_colors=[], dimensions=[])
        board.add_nash_panel(panel)
        ticker_data = {"nash_distance": {"distance": 0.15, "current_strategy": "s1", "nash_strategy": "nash", "timestamp": 100.0}}
        board.update_from_ticker(ticker_data)
        assert board.nash_panel.heatmap_values == [[0.15]]
        assert board.nash_panel.heatmap_colors == [["red"]]
        assert board.nash_panel.dimensions == ["s1"]

    def test_update_from_ticker_with_empty_board(self):
        board = DashboardBoard()
        ticker_data = {"current_win_rate": {"value": 0.5, "total_games": 10, "wins": 5, "losses": 5, "timestamp": 100.0}}
        board.update_from_ticker(ticker_data)
        # Should not raise
        assert board.win_rate_panel is None

    def test_update_from_ticker_updates_all_panels(self):
        board = DashboardBoard()
        wr = WinRatePanel(panel_id="wr1", gauge_value=0.0, gauge_color="white")
        bk = BankrollCurvePanel(panel_id="bk1", bankroll_points=[], shading_color="blue")
        ne = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[], heatmap_colors=[], dimensions=[])
        board.add_win_rate_panel(wr)
        board.add_bankroll_panel(bk)
        board.add_nash_panel(ne)
        ticker_data = {
            "current_win_rate": {"value": 0.6, "total_games": 10, "wins": 6, "losses": 4, "timestamp": 100.0},
            "bankroll_history": {"bankroll": 1050.0, "peak_bankroll": 1050.0, "drawdown": 0.0, "timestamp": 100.0},
            "nash_distance": {"distance": 0.1, "current_strategy": "s1", "nash_strategy": "nash", "timestamp": 100.0},
        }
        board.update_from_ticker(ticker_data)
        assert board.win_rate_panel.gauge_value == 0.6
        assert board.bankroll_panel.bankroll_points[0]["value"] == 1050.0
        assert board.nash_panel.heatmap_values == [[0.1]]


class TestDashboardBoardGetPanelByType:
    def test_get_panel_by_type_win_rate(self):
        board = DashboardBoard()
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.5, gauge_color="white")
        board.add_win_rate_panel(panel)
        result = board.get_panel_by_type("win_rate")
        assert result is panel

    def test_get_panel_by_type_bankroll(self):
        board = DashboardBoard()
        panel = BankrollCurvePanel(panel_id="bk1", bankroll_points=[{"value": 100.0}])
        board.add_bankroll_panel(panel)
        result = board.get_panel_by_type("bankroll")
        assert result is panel

    def test_get_panel_by_type_nash(self):
        board = DashboardBoard()
        panel = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[[0.5]], heatmap_colors=[["white"]], dimensions=["A"])
        board.add_nash_panel(panel)
        result = board.get_panel_by_type("nash")
        assert result is panel

    def test_get_panel_by_type_unknown(self):
        board = DashboardBoard()
        result = board.get_panel_by_type("unknown")
        assert result is None

    def test_get_panel_by_type_no_panel(self):
        board = DashboardBoard()
        result = board.get_panel_by_type("win_rate")
        assert result is None


# ===== DashboardVizRenderer =====

class TestDashboardVizRendererCreation:
    def test_default_initialization(self):
        renderer = DashboardVizRenderer()
        assert renderer.board is None
        assert renderer.resolution == (800, 600)
        assert renderer.is_rendered is False

    def test_custom_initialization(self):
        board = DashboardBoard()
        renderer = DashboardVizRenderer(board=board, resolution=(1920, 1080))
        assert renderer.board is board
        assert renderer.resolution == (1920, 1080)

    def test_set_board(self):
        renderer = DashboardVizRenderer()
        board = DashboardBoard()
        renderer.set_board(board)
        assert renderer.board is board

    def test_set_scene(self):
        renderer = DashboardVizRenderer()
        scene = VRScene()
        renderer.set_scene(scene)
        assert renderer.scene is scene


class TestDashboardVizRendererRendering:
    def test_render_returns_dict(self):
        board = DashboardBoard()
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert isinstance(result, dict)
        assert "scene" in result
        assert "resolution" in result
        assert "is_rendered" in result

    def test_render_sets_is_rendered(self):
        board = DashboardBoard()
        renderer = DashboardVizRenderer(board=board)
        renderer.render()
        assert renderer.is_rendered is True

    def test_render_with_empty_board(self):
        renderer = DashboardVizRenderer()
        result = renderer.render()
        assert result["is_rendered"] is True
        assert len(result["scene"]["geometries"]) == 0

    def test_render_with_win_rate_panel(self):
        board = DashboardBoard()
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.6, gauge_color="green")
        board.add_win_rate_panel(panel)
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 1
        assert result["scene"]["geometries"][0]["label"] == "Win Rate"

    def test_render_with_bankroll_panel(self):
        board = DashboardBoard()
        panel = BankrollCurvePanel(panel_id="bk1", bankroll_points=[{"value": 1000.0}], shading_color="blue")
        board.add_bankroll_panel(panel)
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 1
        assert result["scene"]["geometries"][0]["label"] == "Bankroll"

    def test_render_with_nash_panel(self):
        board = DashboardBoard()
        panel = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[[0.5]], heatmap_colors=[["white"]], dimensions=["A"])
        board.add_nash_panel(panel)
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 1
        assert result["scene"]["geometries"][0]["label"] == "Nash Equilibrium"

    def test_render_with_all_panel_types(self):
        board = DashboardBoard()
        wr = WinRatePanel(panel_id="wr1", gauge_value=0.5, gauge_color="white")
        bk = BankrollCurvePanel(panel_id="bk1", bankroll_points=[{"value": 100.0}], shading_color="blue")
        ne = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[[0.5]], heatmap_colors=[["white"]], dimensions=["A"])
        board.add_win_rate_panel(wr)
        board.add_bankroll_panel(bk)
        board.add_nash_panel(ne)
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 3

    def test_render_with_custom_resolution(self):
        board = DashboardBoard()
        renderer = DashboardVizRenderer(board=board, resolution=(1920, 1080))
        result = renderer.render()
        assert result["resolution"] == [1920, 1080]


class TestDashboardVizRendererPanelRendering:
    def test_render_win_rate_panel(self):
        board = DashboardBoard()
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.6, gauge_color="green")
        board.add_win_rate_panel(panel)
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 1
        geom = result["scene"]["geometries"][0]
        assert geom["geometry_type"] == "box"
        assert geom["label"] == "Win Rate"
        assert geom["color"] == [0.0, 1.0, 0.0]  # green

    def test_render_bankroll_panel(self):
        board = DashboardBoard()
        panel = BankrollCurvePanel(panel_id="bk1", bankroll_points=[{"value": 1000.0}], shading_color="blue")
        board.add_bankroll_panel(panel)
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 1
        geom = result["scene"]["geometries"][0]
        assert geom["geometry_type"] == "box"
        assert geom["label"] == "Bankroll"
        assert geom["color"] == [0.0, 0.0, 1.0]  # blue

    def test_render_nash_panel(self):
        board = DashboardBoard()
        panel = NashEquilibriumPanel(panel_id="ne1", heatmap_values=[[0.5]], heatmap_colors=[["white"]], dimensions=["A"])
        board.add_nash_panel(panel)
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 1
        geom = result["scene"]["geometries"][0]
        assert geom["geometry_type"] == "box"
        assert geom["label"] == "Nash Equilibrium"
        assert geom["color"] == [1.0, 1.0, 1.0]  # white


class TestDashboardVizRendererColorConversion:
    def test_color_name_to_rgb_green(self):
        assert DashboardVizRenderer._color_name_to_rgb("green") == (0.0, 1.0, 0.0)

    def test_color_name_to_rgb_red(self):
        assert DashboardVizRenderer._color_name_to_rgb("red") == (1.0, 0.0, 0.0)

    def test_color_name_to_rgb_white(self):
        assert DashboardVizRenderer._color_name_to_rgb("white") == (1.0, 1.0, 1.0)

    def test_color_name_to_rgb_blue(self):
        assert DashboardVizRenderer._color_name_to_rgb("blue") == (0.0, 0.0, 1.0)

    def test_color_name_to_rgb_yellow(self):
        assert DashboardVizRenderer._color_name_to_rgb("yellow") == (1.0, 1.0, 0.0)

    def test_color_name_to_rgb_default(self):
        assert DashboardVizRenderer._color_name_to_rgb("unknown") == (0.5, 0.5, 0.5)

    def test_color_name_to_rgb_case_insensitive(self):
        assert DashboardVizRenderer._color_name_to_rgb("GREEN") == (0.0, 1.0, 0.0)
        assert DashboardVizRenderer._color_name_to_rgb("Red") == (1.0, 0.0, 0.0)


class TestDashboardVizRendererSerialization:
    def test_to_dict_has_expected_keys(self):
        board = DashboardBoard()
        renderer = DashboardVizRenderer(board=board)
        d = renderer.to_dict()
        assert "board" in d
        assert "resolution" in d
        assert "is_rendered" in d

    def test_from_dict_restores_renderer(self):
        board = DashboardBoard()
        renderer = DashboardVizRenderer(board=board, resolution=(1920, 1080))
        d = renderer.to_dict()
        renderer2 = DashboardVizRenderer.from_dict(d)
        assert renderer2.resolution == (1920, 1080)
        assert renderer2.is_rendered == renderer.is_rendered

    def test_roundtrip_preserves_data(self):
        board = DashboardBoard()
        panel = WinRatePanel(panel_id="wr1", gauge_value=0.6, gauge_color="green")
        board.add_win_rate_panel(panel)
        renderer = DashboardVizRenderer(board=board, resolution=(1920, 1080))
        renderer.render()
        d = renderer.to_dict()
        renderer2 = DashboardVizRenderer.from_dict(d)
        assert renderer2.resolution == (1920, 1080)
        assert renderer2.is_rendered is True
