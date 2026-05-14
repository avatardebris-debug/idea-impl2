"""Tests for DashboardBoard and DashboardVizRenderer."""

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
        assert board.rows == 1
        assert board.columns == 1
        assert board.panels == []
        assert board.title is None

    def test_custom_initialization(self):
        board = DashboardBoard(rows=2, columns=2, title="Test")
        assert board.rows == 2
        assert board.columns == 2
        assert board.title == "Test"

    def test_add_panel(self):
        panel = WinRatePanel(symbol="wr1", gauge_value=0.6)
        board = DashboardBoard()
        board.add_panel(panel)
        assert len(board.panels) == 1
        assert board.panels[0] is panel

    def test_remove_panel(self):
        panel = WinRatePanel(symbol="wr1")
        board = DashboardBoard()
        board.add_panel(panel)
        board.remove_panel(panel)
        assert len(board.panels) == 0

    def test_get_panel_at(self):
        p1 = WinRatePanel(symbol="p1")
        p2 = BankrollCurvePanel(symbol="p2")
        board = DashboardBoard(panels=[p1, p2], rows=1, columns=2)
        assert board.get_panel_at(0, 0) is p1
        assert board.get_panel_at(0, 1) is p2

    def test_set_grid_dimensions(self):
        board = DashboardBoard()
        board.set_grid_dimensions(2, 3)
        assert board.rows == 2
        assert board.columns == 3


class TestDashboardBoardSerialization:
    def test_to_dict(self):
        p1 = WinRatePanel(symbol="p1")
        board = DashboardBoard(panels=[p1], rows=1, columns=1, title="T")
        d = board.to_dict()
        assert d["title"] == "T"
        assert d["rows"] == 1
        assert d["columns"] == 1
        assert len(d["panels"]) == 1

    def test_from_dict(self):
        d = {
            "title": "T",
            "rows": 2,
            "columns": 2,
            "panels": [{"symbol": "WIN_RATE", "type": "WinRatePanel", "gauge_value": 0.5}]
        }
        board = DashboardBoard.from_dict(d)
        assert board.title == "T"
        assert board.rows == 2
        assert board.columns == 2
        assert len(board.panels) == 1
        assert isinstance(board.panels[0], WinRatePanel)


# ===== DashboardVizRenderer =====

class TestDashboardVizRendererCreation:
    def test_default_initialization(self):
        renderer = DashboardVizRenderer()
        assert renderer.board is not None

class TestDashboardVizRendererRendering:
    def test_render_with_empty_board(self):
        renderer = DashboardVizRenderer()
        result = renderer.render()
        assert "scene" in result

    def test_render_with_panels(self):
        board = DashboardBoard()
        board.add_panel(WinRatePanel(symbol="wr1", gauge_value=0.6))
        board.add_panel(BankrollCurvePanel(symbol="bk1", sparkline=[1000.0, 1100.0]))
        board.add_panel(NashEquilibriumPanel(symbol="ne1", distance=0.1))
        renderer = DashboardVizRenderer(board=board)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) > 0
