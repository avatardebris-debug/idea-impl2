"""Tests for the TickerPanel and TickerBoard display components."""

from __future__ import annotations

import pytest
from src.panels import TickerPanel, TickerBoard
from src.ticker import Ticker


class TestTickerPanel:
    """Tests for TickerPanel creation and properties."""

    def test_create_panel_with_ticker(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        assert panel.ticker == ticker
        assert panel.is_selected is False
        assert panel.is_highlighted is False
        assert panel.position == (0.0, 0.0, 0.0)
        assert panel.size == (1.0, 0.6, 0.05)

    def test_create_panel_with_custom_position(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 2.0, 3.0))
        assert panel.position == (1.0, 2.0, 3.0)

    def test_create_panel_with_custom_size(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, size=(2.0, 1.0, 0.1))
        assert panel.size == (2.0, 1.0, 0.1)

    def test_create_panel_with_custom_rotation(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, rotation=(0.0, 45.0, 0.0))
        assert panel.rotation == (0.0, 45.0, 0.0)

    def test_create_panel_with_custom_colors(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(
            ticker,
            color=(1.0, 0.0, 0.0),
            background_color=(0.0, 1.0, 0.0),
            text_color=(0.0, 0.0, 1.0),
        )
        assert panel.color == (1.0, 0.0, 0.0)
        assert panel.background_color == (0.0, 1.0, 0.0)
        assert panel.text_color == (0.0, 0.0, 1.0)

    def test_panel_gets_colors_from_ticker(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        panel = TickerPanel(ticker)
        assert panel.color == (0.0, 1.0, 0.0)  # Green for positive
        assert panel.background_color == (0.0, 0.5, 0.0)  # Dark green

    def test_panel_gets_colors_from_ticker_negative(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=-5.0, change_percent=-5.0)
        panel = TickerPanel(ticker)
        assert panel.color == (1.0, 0.0, 0.0)  # Red for negative
        assert panel.background_color == (0.5, 0.0, 0.0)  # Dark red


class TestTickerPanelState:
    """Tests for TickerPanel state management."""

    def test_select_panel(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        panel.select()
        assert panel.is_selected is True
        assert panel.is_highlighted is True

    def test_deselect_panel(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        panel.select()
        panel.deselect()
        assert panel.is_selected is False
        assert panel.is_highlighted is False

    def test_toggle_panel(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        panel.toggle()
        assert panel.is_selected is True
        panel.toggle()
        assert panel.is_selected is False

    def test_highlight_panel(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        panel.highlight()
        assert panel.is_highlighted is True
        panel.unhighlight()
        assert panel.is_highlighted is False


class TestTickerPanelUpdate:
    """Tests for TickerPanel ticker updates."""

    def test_update_panel_with_new_ticker(self):
        ticker1 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        ticker2 = Ticker(symbol="AAPL", price=105.0, change=10.0, change_percent=10.0)
        panel = TickerPanel(ticker1)
        panel.update_ticker(ticker2)
        assert panel.ticker == ticker2
        assert panel.color == (0.0, 1.0, 0.0)  # Green for positive
        assert panel.background_color == (0.0, 0.5, 0.0)  # Dark green

    def test_update_panel_with_negative_ticker(self):
        ticker1 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        ticker2 = Ticker(symbol="AAPL", price=95.0, change=-5.0, change_percent=-5.0)
        panel = TickerPanel(ticker1)
        panel.update_ticker(ticker2)
        assert panel.ticker == ticker2
        assert panel.color == (1.0, 0.0, 0.0)  # Red for negative
        assert panel.background_color == (0.5, 0.0, 0.0)  # Dark red


class TestTickerPanelSerialization:
    """Tests for TickerPanel serialization."""

    def test_panel_to_dict(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        panel = TickerPanel(
            ticker,
            position=(1.0, 2.0, 3.0),
            size=(2.0, 1.0, 0.1),
            rotation=(0.0, 45.0, 0.0),
            color=(1.0, 0.0, 0.0),
            background_color=(0.0, 1.0, 0.0),
            text_color=(0.0, 0.0, 1.0),
            is_selected=True,
            is_highlighted=True,
        )
        data = panel.to_dict()
        assert data["ticker"]["symbol"] == "AAPL"
        assert data["position"] == [1.0, 2.0, 3.0]
        assert data["size"] == [2.0, 1.0, 0.1]
        assert data["rotation"] == [0.0, 45.0, 0.0]
        assert data["color"] == [1.0, 0.0, 0.0]
        assert data["background_color"] == [0.0, 1.0, 0.0]
        assert data["text_color"] == [0.0, 0.0, 1.0]
        assert data["is_selected"] is True
        assert data["is_highlighted"] is True

    def test_panel_from_dict(self):
        data = {
            "ticker": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 100.0,
                "change": 5.0,
                "change_percent": 5.0,
                "volume": 1000000,
                "high": 105.0,
                "low": 95.0,
                "open_price": 98.0,
                "previous_close": 95.0,
            },
            "position": [1.0, 2.0, 3.0],
            "size": [2.0, 1.0, 0.1],
            "rotation": [0.0, 45.0, 0.0],
            "color": [1.0, 0.0, 0.0],
            "background_color": [0.0, 1.0, 0.0],
            "text_color": [0.0, 0.0, 1.0],
            "is_selected": True,
            "is_highlighted": True,
        }
        panel = TickerPanel.from_dict(data)
        assert panel.ticker.symbol == "AAPL"
        assert panel.position == (1.0, 2.0, 3.0)
        assert panel.size == (2.0, 1.0, 0.1)
        assert panel.rotation == (0.0, 45.0, 0.0)
        assert panel.color == (1.0, 0.0, 0.0)
        assert panel.background_color == (0.0, 1.0, 0.0)
        assert panel.text_color == (0.0, 0.0, 1.0)
        assert panel.is_selected is True
        assert panel.is_highlighted is True

    def test_panel_equality(self):
        ticker1 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        ticker2 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        panel1 = TickerPanel(ticker1, position=(1.0, 2.0, 3.0))
        panel2 = TickerPanel(ticker2, position=(1.0, 2.0, 3.0))
        assert panel1 == panel2

    def test_panel_inequality(self):
        ticker1 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        ticker2 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        panel1 = TickerPanel(ticker1, position=(1.0, 2.0, 3.0))
        panel2 = TickerPanel(ticker2, position=(4.0, 5.0, 6.0))
        assert panel1 != panel2


class TestTickerBoard:
    """Tests for TickerBoard creation and properties."""

    def test_create_board(self):
        board = TickerBoard(name="Test Board")
        assert board.name == "Test Board"
        assert board.panels == []
        assert board.position == (0.0, 1.6, 0.0)
        assert board.size == (10.0, 6.0, 0.05)

    def test_add_panel(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        assert len(board.panels) == 1
        assert board.panels[0] == panel

    def test_remove_panel(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        board.remove_panel("AAPL")
        assert len(board.panels) == 0

    def test_remove_nonexistent_panel(self):
        board = TickerBoard(name="Test Board")
        assert board.remove_panel("AAPL") is False

    def test_get_panel(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        assert board.get_panel("AAPL") == panel

    def test_get_nonexistent_panel(self):
        board = TickerBoard(name="Test Board")
        assert board.get_panel("AAPL") is None

    def test_update_panel(self):
        board = TickerBoard(name="Test Board")
        ticker1 = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        ticker2 = Ticker(symbol="AAPL", price=105.0, change=10.0, change_percent=10.0)
        panel = TickerPanel(ticker1)
        board.add_panel(panel)
        board.update_panel("AAPL", ticker2)
        assert board.panels[0].ticker == ticker2

    def test_update_nonexistent_panel(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        assert board.update_panel("AAPL", ticker) is False

    def test_get_all_ticker_symbols(self):
        board = TickerBoard(name="Test Board")
        ticker1 = Ticker(symbol="AAPL", price=100.0)
        ticker2 = Ticker(symbol="GOOGL", price=200.0)
        panel1 = TickerPanel(ticker1)
        panel2 = TickerPanel(ticker2)
        board.add_panel(panel1)
        board.add_panel(panel2)
        symbols = board.get_all_ticker_symbols()
        assert "AAPL" in symbols
        assert "GOOGL" in symbols
        assert len(symbols) == 2

    def test_get_panel_at_position(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 2.0, 3.0))
        board.add_panel(panel)
        assert board.get_panel_at_position((1.0, 2.0, 3.0)) == panel

    def test_get_nonexistent_panel_at_position(self):
        board = TickerBoard(name="Test Board")
        assert board.get_panel_at_position((1.0, 2.0, 3.0)) is None

    def test_get_selected_panel(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        panel.select()
        board.add_panel(panel)
        assert board.get_selected_panel() == panel

    def test_get_nonexistent_selected_panel(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        assert board.get_selected_panel() is None

    def test_clear_panels(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        board.clear_panels()
        assert board.panels == []


class TestTickerBoardSerialization:
    """Tests for TickerBoard serialization."""

    def test_board_to_dict(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        panel = TickerPanel(ticker, position=(1.0, 2.0, 3.0))
        board = TickerBoard(
            name="Test Board",
            position=(4.0, 5.0, 6.0),
            rotation=(0.0, 45.0, 0.0),
            size=(12.0, 8.0, 0.1),
        )
        board.add_panel(panel)
        data = board.to_dict()
        assert data["name"] == "Test Board"
        assert data["position"] == [4.0, 5.0, 6.0]
        assert data["rotation"] == [0.0, 45.0, 0.0]
        assert data["size"] == [12.0, 8.0, 0.1]
        assert len(data["panels"]) == 1
        assert data["panels"][0]["ticker"]["symbol"] == "AAPL"

    def test_board_from_dict(self):
        data = {
            "name": "Test Board",
            "position": [4.0, 5.0, 6.0],
            "rotation": [0.0, 45.0, 0.0],
            "size": [12.0, 8.0, 0.1],
            "panels": [
                {
                    "ticker": {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "price": 100.0,
                        "change": 5.0,
                        "change_percent": 5.0,
                        "volume": 1000000,
                        "high": 105.0,
                        "low": 95.0,
                        "open_price": 98.0,
                        "previous_close": 95.0,
                    },
                    "position": [1.0, 2.0, 3.0],
                    "size": [2.0, 1.0, 0.1],
                    "rotation": [0.0, 0.0, 0.0],
                    "color": [0.0, 1.0, 0.0],
                    "background_color": [0.0, 0.5, 0.0],
                    "text_color": [1.0, 1.0, 1.0],
                    "is_selected": False,
                    "is_highlighted": False,
                }
            ],
        }
        board = TickerBoard.from_dict(data)
        assert board.name == "Test Board"
        assert board.position == (4.0, 5.0, 6.0)
        assert board.rotation == (0.0, 45.0, 0.0)
        assert board.size == (12.0, 8.0, 0.1)
        assert len(board.panels) == 1
        assert board.panels[0].ticker.symbol == "AAPL"

    def test_board_equality(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        panel = TickerPanel(ticker, position=(1.0, 2.0, 3.0))
        board1 = TickerBoard(name="Test Board", position=(4.0, 5.0, 6.0))
        board2 = TickerBoard(name="Test Board", position=(4.0, 5.0, 6.0))
        board1.add_panel(panel)
        board2.add_panel(panel)
        assert board1 == board2

    def test_board_inequality(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0, change_percent=5.0)
        panel = TickerPanel(ticker, position=(1.0, 2.0, 3.0))
        board1 = TickerBoard(name="Test Board", position=(4.0, 5.0, 6.0))
        board2 = TickerBoard(name="Test Board", position=(7.0, 8.0, 9.0))
        board1.add_panel(panel)
        board2.add_panel(panel)
        assert board1 != board2
