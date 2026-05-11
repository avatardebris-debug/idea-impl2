"""Tests for dashboard layout."""

import pytest
from src.dashboard.layout import DashboardBoard
from src.dashboard.panels import DashboardPanel, WinRatePanel, BankrollCurvePanel, NashEquilibriumPanel


class TestDashboardBoard:
    """Tests for DashboardBoard."""

    def test_default_values(self):
        """Test default values are correct."""
        board = DashboardBoard()
        assert board.panels == []
        assert board.rows == 1
        assert board.columns == 1
        assert board.title is None

    def test_add_panel(self):
        """Test adding a panel."""
        board = DashboardBoard()
        panel = WinRatePanel()
        board.add_panel(panel)
        assert len(board.panels) == 1
        assert board.panels[0] is panel

    def test_remove_panel(self):
        """Test removing a panel."""
        board = DashboardBoard()
        panel = WinRatePanel()
        board.add_panel(panel)
        board.remove_panel(panel)
        assert len(board.panels) == 0

    def test_remove_nonexistent_panel(self):
        """Test removing a panel that doesn't exist."""
        board = DashboardBoard()
        panel = WinRatePanel()
        board.remove_panel(panel)
        assert len(board.panels) == 0

    def test_get_panel_at(self):
        """Test getting a panel at a specific position."""
        board = DashboardBoard(rows=2, columns=2)
        panel1 = WinRatePanel()
        panel2 = BankrollCurvePanel()
        board.add_panel(panel1)
        board.add_panel(panel2)
        assert board.get_panel_at(0, 0) is panel1
        assert board.get_panel_at(0, 1) is panel2
        assert board.get_panel_at(1, 0) is None
        assert board.get_panel_at(1, 1) is None

    def test_get_panel_at_out_of_bounds(self):
        """Test getting a panel at an out-of-bounds position."""
        board = DashboardBoard()
        assert board.get_panel_at(0, 0) is None
        assert board.get_panel_at(1, 1) is None

    def test_get_grid_dimensions(self):
        """Test getting grid dimensions."""
        board = DashboardBoard(rows=3, columns=4)
        assert board.get_grid_dimensions() == (3, 4)

    def test_set_grid_dimensions(self):
        """Test setting grid dimensions."""
        board = DashboardBoard()
        board.set_grid_dimensions(2, 3)
        assert board.rows == 2
        assert board.columns == 3

    def test_set_grid_dimensions_too_small(self):
        """Test setting grid dimensions that are too small."""
        board = DashboardBoard()
        panel = WinRatePanel()
        board.add_panel(panel)
        with pytest.raises(ValueError, match="Cannot fit 1 panels"):
            board.set_grid_dimensions(0, 0)

    def test_set_grid_dimensions_too_small_multiple_panels(self):
        """Test setting grid dimensions that are too small for multiple panels."""
        board = DashboardBoard()
        board.add_panel(WinRatePanel())
        board.add_panel(BankrollCurvePanel())
        board.add_panel(NashEquilibriumPanel())
        with pytest.raises(ValueError, match="Cannot fit 3 panels"):
            board.set_grid_dimensions(1, 2)

    def test_validation_on_init(self):
        """Test validation on initialization."""
        with pytest.raises(ValueError, match="Cannot fit 5 panels"):
            DashboardBoard(rows=2, columns=2, panels=[WinRatePanel() for _ in range(5)])

    def test_get_layout_info(self):
        """Test getting layout info."""
        board = DashboardBoard(title="Test Board", rows=2, columns=3)
        board.add_panel(WinRatePanel())
        board.add_panel(BankrollCurvePanel())
        info = board.get_layout_info()
        assert info["title"] == "Test Board"
        assert info["rows"] == 2
        assert info["columns"] == 3
        assert len(info["panels"]) == 2

    def test_to_dict(self):
        """Test serialization to dict."""
        board = DashboardBoard(title="Test Board", rows=2, columns=3)
        board.add_panel(WinRatePanel())
        board.add_panel(BankrollCurvePanel())
        d = board.to_dict()
        assert d["title"] == "Test Board"
        assert d["rows"] == 2
        assert d["columns"] == 3
        assert len(d["panels"]) == 2
        assert d["panels"][0]["symbol"] == "WIN_RATE"
        assert d["panels"][1]["symbol"] == "BANKROLL_CURVE"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "title": "Test Board",
            "rows": 2,
            "columns": 3,
            "panels": [
                {"symbol": "WIN_RATE", "title": "Win Rate", "width": 10, "height": 10, "x": 0, "y": 0},
                {"symbol": "BANKROLL_CURVE", "title": "Bankroll Curve", "width": 10, "height": 10, "x": 0, "y": 0},
            ],
        }
        board = DashboardBoard.from_dict(data)
        assert board.title == "Test Board"
        assert board.rows == 2
        assert board.columns == 3
        assert len(board.panels) == 2
        assert board.panels[0].symbol == "WIN_RATE"
        assert board.panels[1].symbol == "BANKROLL_CURVE"

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {}
        board = DashboardBoard.from_dict(data)
        assert board.panels == []
        assert board.rows == 1
        assert board.columns == 1
        assert board.title is None

    def test_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = DashboardBoard(title="Test Board", rows=2, columns=3)
        original.add_panel(WinRatePanel())
        original.add_panel(BankrollCurvePanel())
        d = original.to_dict()
        restored = DashboardBoard.from_dict(d)
        assert restored.title == original.title
        assert restored.rows == original.rows
        assert restored.columns == original.columns
        assert len(restored.panels) == len(original.panels)
        assert restored.panels[0].symbol == original.panels[0].symbol
        assert restored.panels[1].symbol == original.panels[1].symbol

    def test_nested_objects_preserved(self):
        """Test that nested objects are preserved through roundtrip."""
        original = DashboardBoard(title="Test Board", rows=2, columns=3)
        panel = WinRatePanel(title="Custom Title", width=15, height=12, x=3, y=7)
        original.add_panel(panel)
        d = original.to_dict()
        restored = DashboardBoard.from_dict(d)
        assert restored.panels[0].title == original.panels[0].title
        assert restored.panels[0].width == original.panels[0].width
        assert restored.panels[0].height == original.panels[0].height
        assert restored.panels[0].x == original.panels[0].x
        assert restored.panels[0].y == original.panels[0].y
