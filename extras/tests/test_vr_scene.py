"""Tests for the VRScene."""

from __future__ import annotations

import pytest
from src.vr_scene import VRScene
from src.ticker import Ticker
from src.data_source import MockDataSource
from src.panels import TickerPanel, TickerBoard
from src.navigation import VRNavigator


class TestVRSceneCreation:
    """Tests for VRScene creation and initialization."""

    def test_create_default_scene(self):
        scene = VRScene()
        assert scene.name == "VR Stock Ticker Scene"
        assert scene.tickers == []
        assert scene.boards == {}
        assert scene.data_source is None
        assert scene.navigator is None
        assert scene.is_running is False

    def test_create_scene_with_custom_name(self):
        scene = VRScene(name="My Scene")
        assert scene.name == "My Scene"


class TestVRSceneTickerManagement:
    """Tests for ticker management in VRScene."""

    def test_add_ticker(self):
        scene = VRScene()
        ticker = Ticker(symbol="AAPL", price=100.0)
        scene.add_ticker(ticker)
        assert len(scene.tickers) == 1
        assert scene.tickers[0].symbol == "AAPL"

    def test_add_ticker_updates_data_source(self):
        ds = MockDataSource()
        scene = VRScene(data_source=ds)
        ticker = Ticker(symbol="AAPL", price=100.0)
        scene.add_ticker(ticker)
        assert ds.get_ticker("AAPL") is not None
        assert ds.get_ticker("AAPL").price == 100.0

    def test_remove_ticker(self):
        scene = VRScene()
        ticker = Ticker(symbol="AAPL", price=100.0)
        scene.add_ticker(ticker)
        assert scene.remove_ticker("AAPL") is True
        assert len(scene.tickers) == 0

    def test_remove_nonexistent_ticker(self):
        scene = VRScene()
        assert scene.remove_ticker("AAPL") is False

    def test_get_ticker(self):
        scene = VRScene()
        ticker = Ticker(symbol="AAPL", price=100.0)
        scene.add_ticker(ticker)
        assert scene.get_ticker("AAPL") == ticker

    def test_get_nonexistent_ticker(self):
        scene = VRScene()
        assert scene.get_ticker("AAPL") is None

    def test_get_all_ticker_symbols(self):
        scene = VRScene()
        scene.add_ticker(Ticker(symbol="AAPL", price=100.0))
        scene.add_ticker(Ticker(symbol="GOOGL", price=200.0))
        symbols = scene.get_all_ticker_symbols()
        assert "AAPL" in symbols
        assert "GOOGL" in symbols
        assert len(symbols) == 2


class TestVRSceneBoardManagement:
    """Tests for board management in VRScene."""

    def test_add_board(self):
        scene = VRScene()
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        assert "Test Board" in scene.boards
        assert scene.boards["Test Board"] == board

    def test_add_board_with_position(self):
        scene = VRScene()
        board = TickerBoard(name="Test Board")
        scene.add_board(board, position=(1.0, 2.0, 3.0))
        assert scene.boards["Test Board"].position == (1.0, 2.0, 3.0)

    def test_add_board_with_rotation(self):
        scene = VRScene()
        board = TickerBoard(name="Test Board")
        scene.add_board(board, rotation=(0.0, 45.0, 0.0))
        assert scene.boards["Test Board"].rotation == (0.0, 45.0, 0.0)

    def test_add_board_with_size(self):
        scene = VRScene()
        board = TickerBoard(name="Test Board")
        scene.add_board(board, size=(12.0, 8.0, 0.1))
        assert scene.boards["Test Board"].size == (12.0, 8.0, 0.1)

    def test_add_duplicate_board(self):
        scene = VRScene()
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        scene.add_board(board)  # Should not add duplicate
        assert len(scene.boards) == 1

    def test_remove_board(self):
        scene = VRScene()
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        assert scene.remove_board("Test Board") is True
        assert len(scene.boards) == 0

    def test_remove_nonexistent_board(self):
        scene = VRScene()
        assert scene.remove_board("Test Board") is False

    def test_get_board(self):
        scene = VRScene()
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        assert scene.get_board("Test Board") == board

    def test_get_nonexistent_board(self):
        scene = VRScene()
        assert scene.get_board("Test Board") is None

    def test_get_all_board_names(self):
        scene = VRScene()
        scene.add_board(TickerBoard(name="Board1"))
        scene.add_board(TickerBoard(name="Board2"))
        names = scene.get_all_board_names()
        assert "Board1" in names
        assert "Board2" in names
        assert len(names) == 2


class TestVRSceneNavigator:
    """Tests for navigator management in VRScene."""

    def test_set_navigator(self):
        scene = VRScene()
        navigator = VRNavigator()
        scene.set_navigator(navigator)
        assert scene.navigator == navigator

    def test_get_navigator(self):
        scene = VRScene()
        navigator = VRNavigator()
        scene.set_navigator(navigator)
        assert scene.get_navigator() == navigator

    def test_get_navigator_not_set(self):
        scene = VRScene()
        assert scene.get_navigator() is None


class TestVRSceneDataSync:
    """Tests for data synchronization in VRScene."""

    def test_update_tickers_with_data_source(self):
        ds = MockDataSource()
        ds.add_ticker("AAPL", 100.0)
        scene = VRScene(data_source=ds)
        scene.add_ticker(Ticker(symbol="AAPL", price=100.0))
        scene.update_tickers()
        assert len(scene.tickers) == 1
        assert scene.tickers[0].symbol == "AAPL"

    def test_update_tickers_updates_boards(self):
        ds = MockDataSource(volatility=0.1)
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board = TickerBoard(name="Test Board")
        board.add_panel(panel)
        scene = VRScene(data_source=ds)
        scene.add_board(board)
        scene.add_ticker(ticker)
        initial_price = ticker.price
        scene.update_tickers()
        # Price should have changed due to volatility
        assert scene.tickers[0].price != initial_price or scene.tickers[0].change != 0.0

    def test_update_tickers_with_no_data_source(self):
        scene = VRScene()
        scene.add_ticker(Ticker(symbol="AAPL", price=100.0))
        scene.update_tickers()  # Should not raise
        assert len(scene.tickers) == 1

    def test_update_tickers_with_no_tickers(self):
        ds = MockDataSource()
        scene = VRScene(data_source=ds)
        scene.update_tickers()  # Should not raise
        assert scene.tickers == []


class TestVRSceneSerialization:
    """Tests for VRScene serialization."""

    def test_scene_to_dict(self):
        scene = VRScene(name="Test Scene")
        scene.add_ticker(Ticker(symbol="AAPL", price=100.0))
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        data = scene.to_dict()
        assert data["name"] == "Test Scene"
        assert len(data["tickers"]) == 1
        assert data["tickers"][0]["symbol"] == "AAPL"
        assert len(data["boards"]) == 1
        assert data["boards"][0]["name"] == "Test Board"

    def test_scene_from_dict(self):
        data = {
            "name": "Test Scene",
            "tickers": [
                {
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
                }
            ],
            "boards": [
                {
                    "name": "Test Board",
                    "position": [0.0, 0.0, 0.0],
                    "rotation": [0.0, 0.0, 0.0],
                    "size": [10.0, 6.0, 0.1],
                    "panels": [],
                }
            ],
        }
        scene = VRScene.from_dict(data)
        assert scene.name == "Test Scene"
        assert len(scene.tickers) == 1
        assert scene.tickers[0].symbol == "AAPL"
        assert len(scene.boards) == 1
        assert scene.boards["Test Board"].name == "Test Board"

    def test_scene_equality(self):
        scene1 = VRScene(name="Test Scene")
        scene2 = VRScene(name="Test Scene")
        assert scene1 == scene2

    def test_scene_inequality(self):
        scene1 = VRScene(name="Test Scene")
        scene2 = VRScene(name="Other Scene")
        assert scene1 != scene2
