"""Tests for src.dashboard.layout."""

import pytest
from src.dashboard.layout import DashboardBoard
from src.dashboard.panels import (
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)


# ===== DashboardBoard =====

class TestDashboardBoard:
    def test_default_values(self):
        board = DashboardBoard()
        assert board.panels == []
        assert board.rows == 1
        assert board.columns == 1
        assert board.title is None

    def test_add_panel(self):
        board = DashboardBoard()
        panel = WinRatePanel()
        board.add_panel(panel)
        assert panel in board.panels

    def test_remove_panel(self):
        board = DashboardBoard()
        panel = WinRatePanel()
        board.add_panel(panel)
        board.remove_panel(panel)
        assert panel not in board.panels

    def test_remove_nonexistent_panel(self):
        board = DashboardBoard()
        panel = WinRatePanel()
        # Should not raise
        board.remove_panel(panel)

    def test_get_panel_at(self):
        board = DashboardBoard(rows=2, columns=2)
        panel = WinRatePanel()
        board.add_panel(panel)
        assert board.get_panel_at(0, 0) is panel
        assert board.get_panel_at(0, 1) is None
        assert board.get_panel_at(1, 0) is None

    def test_get_panel_at_out_of_bounds(self):
        board = DashboardBoard(rows=2, columns=2)
        assert board.get_panel_at(0, 0) is None
        assert board.get_panel_at(5, 5) is None

    def test_get_grid_dimensions(self):
        board = DashboardBoard(rows=3, columns=4)
        assert board.get_grid_dimensions() == (3, 4)

    def test_set_grid_dimensions(self):
        board = DashboardBoard()
        board.set_grid_dimensions(3, 4)
        assert board.rows == 3
        assert board.columns == 4

    def test_set_grid_dimensions_too_small(self):
        board = DashboardBoard()
        panel1 = WinRatePanel()
        panel2 = BankrollCurvePanel()
        board.add_panel(panel1)
        board.add_panel(panel2)
        # Should not raise
        board.set_grid_dimensions(1, 1)

    def test_to_dict(self):
        board = DashboardBoard(rows=2, columns=2, title="Test Board")
        panel = WinRatePanel()
        board.add_panel(panel)
        d = board.to_dict()
        assert d["rows"] == 2
        assert d["columns"] == 2
        assert d["title"] == "Test Board"
        assert len(d["panels"]) == 1

    def test_from_dict(self):
        data = {
            "rows": 2,
            "columns": 2,
            "title": "Test Board",
            "panels": [
                {
                    "symbol": "WIN_RATE",
                    "title": "Win Rate",
                    "description": "Shows the win rate of the agent.",
                    "width": 10,
                    "height": 10,
                    "x": 0,
                    "y": 0,
                }
            ],
        }
        board = DashboardBoard.from_dict(data)
        assert board.rows == 2
        assert board.columns == 2
        assert board.title == "Test Board"
        assert len(board.panels) == 1
        assert board.panels[0].symbol == "WIN_RATE"

    def test_from_dict_empty(self):
        data = {"rows": 1, "columns": 1, "panels": []}
        board = DashboardBoard.from_dict(data)
        assert board.panels == []

    def test_render(self):
        board = DashboardBoard(rows=1, columns=1, title="Test Board")
        panel = WinRatePanel()
        board.add_panel(panel)
        # Should not raise
        output = board.render()
        assert "Test Board" in output

    def test_render_empty(self):
        board = DashboardBoard()
        # Should not raise
        output = board.render()
        assert "Empty Dashboard" in output

    def test_add_panel_too_many(self):
        board = DashboardBoard(rows=1, columns=1)
        panel1 = WinRatePanel()
        panel2 = BankrollCurvePanel()
        board.add_panel(panel1)
        board.add_panel(panel2)
        # Should not raise, but panel2 should not be added
        assert len(board.panels) == 1

    def test_grid_dimensions_consistency(self):
        board = DashboardBoard(rows=2, columns=3)
        assert board.rows == 2
        assert board.columns == 3
        assert board.get_grid_dimensions() == (2, 3)

    def test_panel_positions(self):
        board = DashboardBoard(rows=2, columns=2)
        panel1 = WinRatePanel()
        panel2 = BankrollCurvePanel()
        board.add_panel(panel1)
        board.add_panel(panel2)
        assert board.get_panel_at(0, 0) is panel1
        assert board.get_panel_at(0, 1) is panel2
        assert board.get_panel_at(1, 0) is None
        assert board.get_panel_at(1, 1) is None
