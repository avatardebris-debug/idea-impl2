"""Tests for VR navigation system — camera movement, panel zoom/pan, and multi-board management."""

from __future__ import annotations

import pytest
from src.navigation import CameraState, VRNavigator
from src.ticker_display import TickerBoard, TickerPanel
from src.ticker import Ticker


class TestCameraState:
    """Tests for CameraState creation and serialization."""

    def test_create_camera_state_defaults(self):
        state = CameraState()
        assert state.position == (0.0, 1.6, 0.0)
        assert state.rotation == (0.0, 0.0, 0.0)
        assert state.zoom_level == 1.0
        assert state.is_focused is False
        assert state.focus_target is None

    def test_create_camera_state_custom(self):
        state = CameraState(
            position=(1.0, 2.0, 3.0),
            rotation=(10.0, 20.0, 30.0),
            zoom_level=2.5,
            is_focused=True,
            focus_target="AAPL",
        )
        assert state.position == (1.0, 2.0, 3.0)
        assert state.rotation == (10.0, 20.0, 30.0)
        assert state.zoom_level == 2.5
        assert state.is_focused is True
        assert state.focus_target == "AAPL"

    def test_camera_state_to_dict(self):
        state = CameraState(
            position=(1.0, 2.0, 3.0),
            rotation=(10.0, 20.0, 30.0),
            zoom_level=2.5,
            is_focused=True,
            focus_target="AAPL",
        )
        data = state.to_dict()
        assert data["position"] == [1.0, 2.0, 3.0]
        assert data["rotation"] == [10.0, 20.0, 30.0]
        assert data["zoom_level"] == 2.5
        assert data["is_focused"] is True
        assert data["focus_target"] == "AAPL"

    def test_camera_state_from_dict(self):
        data = {
            "position": [1.0, 2.0, 3.0],
            "rotation": [10.0, 20.0, 30.0],
            "zoom_level": 2.5,
            "is_focused": True,
            "focus_target": "AAPL",
        }
        state = CameraState.from_dict(data)
        assert state.position == (1.0, 2.0, 3.0)
        assert state.rotation == (10.0, 20.0, 30.0)
        assert state.zoom_level == 2.5
        assert state.is_focused is True
        assert state.focus_target == "AAPL"

    def test_camera_state_round_trip(self):
        state = CameraState(
            position=(1.0, 2.0, 3.0),
            rotation=(10.0, 20.0, 30.0),
            zoom_level=2.5,
            is_focused=True,
            focus_target="AAPL",
        )
        data = state.to_dict()
        state2 = CameraState.from_dict(data)
        assert state.position == state2.position
        assert state.rotation == state2.rotation
        assert state.zoom_level == state2.zoom_level
        assert state.is_focused == state2.is_focused
        assert state.focus_target == state2.focus_target

    def test_camera_state_from_dict_defaults(self):
        data = {"position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0]}
        state = CameraState.from_dict(data)
        assert state.zoom_level == 1.0
        assert state.is_focused is False
        assert state.focus_target is None


class TestNavigatorBoardManagement:
    """Tests for VRNavigator board management."""

    def test_create_navigator(self):
        navigator = VRNavigator()
        assert len(navigator._boards) == 0
        assert navigator._current_board_index == 0
        assert len(navigator._board_names) == 0

    def test_add_board(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        result = navigator.add_board(board, "Test Board")
        assert result is True
        assert len(navigator._boards) == 1
        assert "Test Board" in navigator._board_names

    def test_add_board_auto_name(self):
        navigator = VRNavigator()
        board = TickerBoard()
        result = navigator.add_board(board)
        assert result is True
        assert "Board 1" in navigator._board_names

    def test_add_board_duplicate_name(self):
        navigator = VRNavigator()
        board1 = TickerBoard(name="My Board")
        board2 = TickerBoard(name="My Board")
        navigator.add_board(board1, "My Board")
        result = navigator.add_board(board2)
        assert result is True
        # Second board should have a suffix
        assert "My Board" in navigator._board_names
        assert "My Board (1)" in navigator._board_names

    def test_add_board_max_reached(self):
        navigator = VRNavigator()
        for i in range(10):
            board = TickerBoard(name=f"Board {i}")
            navigator.add_board(board, f"Board {i}")
        board = TickerBoard(name="Overflow")
        result = navigator.add_board(board, "Overflow")
        assert result is False
        assert len(navigator._boards) == 10

    def test_remove_board(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        navigator.add_board(board, "Test Board")
        result = navigator.remove_board("Test Board")
        assert result is True
        assert len(navigator._boards) == 0
        assert "Test Board" not in navigator._board_names

    def test_remove_nonexistent_board(self):
        navigator = VRNavigator()
        result = navigator.remove_board("Nonexistent")
        assert result is False

    def test_switch_board(self):
        navigator = VRNavigator()
        board1 = TickerBoard(name="Board 1")
        board2 = TickerBoard(name="Board 2")
        navigator.add_board(board1, "Board 1")
        navigator.add_board(board2, "Board 2")
        result = navigator.switch_board("Board 2")
        assert result is True
        assert navigator.current_board == board2

    def test_switch_board_nonexistent(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Board 1")
        navigator.add_board(board, "Board 1")
        result = navigator.switch_board("Nonexistent")
        assert result is False

    def test_get_board(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        navigator.add_board(board, "Test Board")
        result = navigator.get_board("Test Board")
        assert result == board

    def test_get_board_nonexistent(self):
        navigator = VRNavigator()
        result = navigator.get_board("Nonexistent")
        assert result is None

    def test_get_current_board(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        navigator.add_board(board, "Test Board")
        assert navigator.current_board == board

    def test_get_current_board_none(self):
        navigator = VRNavigator()
        assert navigator.current_board is None

    def test_get_board_names(self):
        navigator = VRNavigator()
        board1 = TickerBoard(name="Board 1")
        board2 = TickerBoard(name="Board 2")
        navigator.add_board(board1, "Board 1")
        navigator.add_board(board2, "Board 2")
        names = navigator.get_board_names()
        assert "Board 1" in names
        assert "Board 2" in names

    def test_clear_boards(self):
        navigator = VRNavigator()
        board1 = TickerBoard(name="Board 1")
        board2 = TickerBoard(name="Board 2")
        navigator.add_board(board1, "Board 1")
        navigator.add_board(board2, "Board 2")
        navigator.clear_boards()
        assert len(navigator._boards) == 0
        assert len(navigator._board_names) == 0


class TestNavigatorCameraMovement:
    """Tests for VRNavigator camera movement."""

    def test_pan_forward(self):
        navigator = VRNavigator()
        navigator.pan_forward(1.0)
        assert navigator._camera.position[2] == pytest.approx(-1.0)

    def test_pan_backward(self):
        navigator = VRNavigator()
        navigator.pan_backward(1.0)
        assert navigator._camera.position[2] == pytest.approx(1.0)

    def test_pan_left(self):
        navigator = VRNavigator()
        navigator.pan_left(1.0)
        assert navigator._camera.position[0] == pytest.approx(-1.0)

    def test_pan_right(self):
        navigator = VRNavigator()
        navigator.pan_right(1.0)
        assert navigator._camera.position[0] == pytest.approx(1.0)

    def test_rotate_up(self):
        navigator = VRNavigator()
        navigator.rotate_up(10.0)
        assert navigator._camera.rotation[0] == pytest.approx(10.0)

    def test_rotate_down(self):
        navigator = VRNavigator()
        navigator.rotate_down(10.0)
        assert navigator._camera.rotation[0] == pytest.approx(-10.0)

    def test_rotate_left(self):
        navigator = VRNavigator()
        navigator.rotate_left(10.0)
        assert navigator._camera.rotation[1] == pytest.approx(10.0)

    def test_rotate_right(self):
        navigator = VRNavigator()
        navigator.rotate_right(10.0)
        assert navigator._camera.rotation[1] == pytest.approx(-10.0)

    def test_zoom_in(self):
        navigator = VRNavigator()
        navigator.zoom_in(0.5)
        assert navigator._camera.zoom_level == pytest.approx(1.5)

    def test_zoom_out(self):
        navigator = VRNavigator()
        navigator.zoom_out(0.5)
        assert navigator._camera.zoom_level == pytest.approx(0.5)

    def test_zoom_to(self):
        navigator = VRNavigator()
        navigator.zoom_to(2.0)
        assert navigator._camera.zoom_level == pytest.approx(2.0)

    def test_zoom_to_clamped(self):
        navigator = VRNavigator()
        navigator.zoom_to(0.1)
        assert navigator._camera.zoom_level == pytest.approx(0.5)
        navigator.zoom_to(10.0)
        assert navigator._camera.zoom_level == pytest.approx(5.0)


class TestNavigatorFocusAndZoom:
    """Tests for VRNavigator focus and zoom interactions."""

    def test_focus_panel(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        result = navigator.focus_panel(panel)
        assert result is True
        assert navigator._is_zoomed is True
        assert navigator._zoom_target == panel

    def test_focus_panel_no_board(self):
        navigator = VRNavigator()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        result = navigator.focus_panel(panel)
        assert result is False

    def test_focus_panel_panel_not_in_board(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        navigator.add_board(board, "Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        result = navigator.focus_panel(panel)
        assert result is False

    def test_unfocus_panel(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        navigator.focus_panel(panel)
        result = navigator.unfocus_panel()
        assert result is True
        assert navigator._is_zoomed is False
        assert navigator._zoom_target is None

    def test_unfocus_when_not_zoomed(self):
        navigator = VRNavigator()
        result = navigator.unfocus_panel()
        assert result is False

    def test_is_focused_panel(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        navigator.focus_panel(panel)
        assert navigator.is_focused_panel(panel) is True
        ticker2 = Ticker(symbol="GOOGL", price=100.0)
        panel2 = TickerPanel(ticker2)
        assert navigator.is_focused_panel(panel2) is False

    def test_get_zoom_target(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        navigator.focus_panel(panel)
        assert navigator.get_zoom_target() == panel

    def test_get_zoom_target_none(self):
        navigator = VRNavigator()
        assert navigator.get_zoom_target() is None


class TestNavigatorPan:
    """Tests for VRNavigator panel panning."""

    def test_pan_panel(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        navigator.focus_panel(panel)
        result = navigator.pan_panel(panel, (0.1, 0.1, 0.0))
        assert result is True
        assert panel.position == pytest.approx((1.1, 1.1, 0.0))

    def test_pan_panel_not_zoomed(self):
        navigator = VRNavigator()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        result = navigator.pan_panel(panel, (0.1, 0.1, 0.0))
        assert result is False

    def test_pan_panel_panel_not_zoomed(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        ticker2 = Ticker(symbol="GOOGL", price=100.0)
        panel2 = TickerPanel(ticker2)
        navigator.focus_panel(panel)
        result = navigator.pan_panel(panel2, (0.1, 0.1, 0.0))
        assert result is False


class TestNavigatorStatus:
    """Tests for VRNavigator status reporting."""

    def test_get_status(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        navigator.add_board(board, "Test Board")
        status = navigator.get_status()
        assert "camera_position" in status
        assert "camera_rotation" in status
        assert "zoom_level" in status
        assert "is_zoomed" in status
        assert "zoom_target" in status
        assert "boards" in status

    def test_get_status_with_zoom(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        navigator.focus_panel(panel)
        status = navigator.get_status()
        assert status["is_zoomed"] is True
        assert status["zoom_target"] == panel

    def test_get_boards_status(self):
        navigator = VRNavigator()
        board1 = TickerBoard(name="Board 1")
        board2 = TickerBoard(name="Board 2")
        navigator.add_board(board1, "Board 1")
        navigator.add_board(board2, "Board 2")
        status = navigator.get_boards_status()
        assert "Board 1" in status
        assert "Board 2" in status
        assert status["Board 1"]["panel_count"] == 0
        assert status["Board 1"]["selected_panel"] is None


class TestNavigatorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_pan_with_zero_distance(self):
        navigator = VRNavigator()
        navigator.pan_forward(0.0)
        assert navigator._camera.position[2] == pytest.approx(0.0)

    def test_rotate_with_zero_angle(self):
        navigator = VRNavigator()
        navigator.rotate_up(0.0)
        assert navigator._camera.rotation[0] == pytest.approx(0.0)

    def test_zoom_with_zero_amount(self):
        navigator = VRNavigator()
        navigator.zoom_in(0.0)
        assert navigator._camera.zoom_level == pytest.approx(1.0)

    def test_switch_to_current_board(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        navigator.add_board(board, "Test Board")
        result = navigator.switch_board("Test Board")
        assert result is True
        assert navigator.current_board == board

    def test_remove_current_board(self):
        navigator = VRNavigator()
        board1 = TickerBoard(name="Board 1")
        board2 = TickerBoard(name="Board 2")
        navigator.add_board(board1, "Board 1")
        navigator.add_board(board2, "Board 2")
        navigator.switch_board("Board 1")
        result = navigator.remove_board("Board 1")
        assert result is True
        assert navigator.current_board == board2

    def test_remove_last_board(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        navigator.add_board(board, "Test Board")
        result = navigator.remove_board("Test Board")
        assert result is True
        assert navigator.current_board is None

    def test_focus_panel_with_multiple_boards(self):
        navigator = VRNavigator()
        board1 = TickerBoard(name="Board 1")
        board2 = TickerBoard(name="Board 2")
        ticker1 = Ticker(symbol="AAPL", price=100.0)
        panel1 = TickerPanel(ticker1, position=(1.0, 1.0, 0.0))
        board1.add_panel(panel1)
        navigator.add_board(board1, "Board 1")
        navigator.add_board(board2, "Board 2")
        result = navigator.focus_panel(panel1)
        assert result is True
        assert navigator._is_zoomed is True

    def test_pan_panel_with_large_offset(self):
        navigator = VRNavigator()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker, position=(1.0, 1.0, 0.0))
        board.add_panel(panel)
        navigator.add_board(board, "Test Board")
        navigator.focus_panel(panel)
        result = navigator.pan_panel(panel, (100.0, 100.0, 0.0))
        assert result is True
        assert panel.position == pytest.approx((101.0, 101.0, 0.0))
