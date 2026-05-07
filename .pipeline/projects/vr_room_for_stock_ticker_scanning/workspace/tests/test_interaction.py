"""Tests for VR interaction system — gaze, pointer, scroll, and keyboard inputs."""

from __future__ import annotations

import pytest
from src.interaction import (
    GazeInput,
    PointerInput,
    ScrollInput,
    KeyboardInput,
    InteractionManager,
)
from src.ticker import Ticker
from src.ticker_display import TickerPanel, TickerBoard
from src.navigation import VRNavigator


class TestGazeInput:
    """Tests for GazeInput."""

    def test_create_gaze_input(self):
        gaze = GazeInput()
        assert gaze.target is None
        assert gaze.is_active is False
        assert gaze.dwell_time == 0.0
        assert gaze.dwell_threshold == 2.0

    def test_gaze_target(self):
        gaze = GazeInput()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        gaze.target = panel
        assert gaze.target == panel

    def test_gaze_activate(self):
        gaze = GazeInput()
        gaze.activate()
        assert gaze.is_active is True

    def test_gaze_deactivate(self):
        gaze = GazeInput()
        gaze.activate()
        gaze.deactivate()
        assert gaze.is_active is False

    def test_gaze_update_dwell_time(self):
        gaze = GazeInput()
        gaze.activate()
        gaze.update_dwell_time(0.5)
        assert gaze.dwell_time == pytest.approx(0.5)

    def test_gaze_dwell_threshold_reached(self):
        gaze = GazeInput()
        gaze.dwell_threshold = 1.0
        gaze.activate()
        gaze.update_dwell_time(1.0)
        assert gaze.dwell_threshold_reached is True

    def test_gaze_dwell_threshold_not_reached(self):
        gaze = GazeInput()
        gaze.dwell_threshold = 1.0
        gaze.activate()
        gaze.update_dwell_time(0.5)
        assert gaze.dwell_threshold_reached is False

    def test_gaze_reset_dwell_time(self):
        gaze = GazeInput()
        gaze.activate()
        gaze.update_dwell_time(0.5)
        gaze.reset_dwell_time()
        assert gaze.dwell_time == pytest.approx(0.0)
        assert gaze.dwell_threshold_reached is False


class TestPointerInput:
    """Tests for PointerInput."""

    def test_create_pointer_input(self):
        pointer = PointerInput()
        assert pointer.position == (0.0, 0.0, 0.0)
        assert pointer.is_active is False
        assert pointer.is_pressed is False

    def test_pointer_activate(self):
        pointer = PointerInput()
        pointer.activate()
        assert pointer.is_active is True

    def test_pointer_deactivate(self):
        pointer = PointerInput()
        pointer.activate()
        pointer.deactivate()
        assert pointer.is_active is False

    def test_pointer_set_position(self):
        pointer = PointerInput()
        pointer.set_position((1.0, 2.0, 3.0))
        assert pointer.position == (1.0, 2.0, 3.0)

    def test_pointer_press(self):
        pointer = PointerInput()
        pointer.press()
        assert pointer.is_pressed is True

    def test_pointer_release(self):
        pointer = PointerInput()
        pointer.press()
        pointer.release()
        assert pointer.is_pressed is False


class TestScrollInput:
    """Tests for ScrollInput."""

    def test_create_scroll_input(self):
        scroll = ScrollInput()
        assert scroll.delta == 0.0
        assert scroll.is_active is False

    def test_scroll_activate(self):
        scroll = ScrollInput()
        scroll.activate()
        assert scroll.is_active is True

    def test_scroll_deactivate(self):
        scroll = ScrollInput()
        scroll.activate()
        scroll.deactivate()
        assert scroll.is_active is False

    def test_scroll_update_delta(self):
        scroll = ScrollInput()
        scroll.update_delta(0.5)
        assert scroll.delta == pytest.approx(0.5)

    def test_scroll_reset_delta(self):
        scroll = ScrollInput()
        scroll.update_delta(0.5)
        scroll.reset_delta()
        assert scroll.delta == pytest.approx(0.0)


class TestKeyboardInput:
    """Tests for KeyboardInput."""

    def test_create_keyboard_input(self):
        keyboard = KeyboardInput()
        assert keyboard.keys_pressed == set()
        assert keyboard.is_active is False

    def test_keyboard_activate(self):
        keyboard = KeyboardInput()
        keyboard.activate()
        assert keyboard.is_active is True

    def test_keyboard_deactivate(self):
        keyboard = KeyboardInput()
        keyboard.activate()
        keyboard.deactivate()
        assert keyboard.is_active is False

    def test_keyboard_press_key(self):
        keyboard = KeyboardInput()
        keyboard.press_key("w")
        assert "w" in keyboard.keys_pressed

    def test_keyboard_release_key(self):
        keyboard = KeyboardInput()
        keyboard.press_key("w")
        keyboard.release_key("w")
        assert "w" not in keyboard.keys_pressed

    def test_keyboard_is_key_pressed(self):
        keyboard = KeyboardInput()
        keyboard.press_key("w")
        assert keyboard.is_key_pressed("w") is True
        assert keyboard.is_key_pressed("a") is False

    def test_keyboard_multiple_keys(self):
        keyboard = KeyboardInput()
        keyboard.press_key("w")
        keyboard.press_key("a")
        assert "w" in keyboard.keys_pressed
        assert "a" in keyboard.keys_pressed

    def test_keyboard_clear_keys(self):
        keyboard = KeyboardInput()
        keyboard.press_key("w")
        keyboard.press_key("a")
        keyboard.clear_keys()
        assert keyboard.keys_pressed == set()


class TestInteractionManager:
    """Tests for InteractionManager."""

    def test_create_interaction_manager(self):
        manager = InteractionManager()
        assert manager.gaze is not None
        assert manager.pointer is not None
        assert manager.scroll is not None
        assert manager.keyboard is not None

    def test_interaction_manager_gaze_target(self):
        manager = InteractionManager()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        manager.gaze.target = panel
        assert manager.gaze_target == panel

    def test_interaction_manager_gaze_threshold_reached(self):
        manager = InteractionManager()
        manager.gaze.dwell_threshold = 1.0
        manager.gaze.activate()
        manager.gaze.update_dwell_time(1.0)
        assert manager.gaze_threshold_reached is True

    def test_interaction_manager_pointer_position(self):
        manager = InteractionManager()
        manager.pointer.set_position((1.0, 2.0, 3.0))
        assert manager.pointer_position == (1.0, 2.0, 3.0)

    def test_interaction_manager_pointer_pressed(self):
        manager = InteractionManager()
        manager.pointer.press()
        assert manager.pointer_pressed is True

    def test_interaction_manager_scroll_delta(self):
        manager = InteractionManager()
        manager.scroll.update_delta(0.5)
        assert manager.scroll_delta == pytest.approx(0.5)

    def test_interaction_manager_is_key_pressed(self):
        manager = InteractionManager()
        manager.keyboard.press_key("w")
        assert manager.is_key_pressed("w") is True
        assert manager.is_key_pressed("a") is False

    def test_interaction_manager_get_all_inputs(self):
        manager = InteractionManager()
        inputs = manager.get_all_inputs()
        assert "gaze" in inputs
        assert "pointer" in inputs
        assert "scroll" in inputs
        assert "keyboard" in inputs

    def test_interaction_manager_reset_all(self):
        manager = InteractionManager()
        manager.gaze.activate()
        manager.gaze.update_dwell_time(1.0)
        manager.pointer.activate()
        manager.pointer.press()
        manager.scroll.activate()
        manager.scroll.update_delta(0.5)
        manager.keyboard.activate()
        manager.keyboard.press_key("w")
        manager.reset_all()
        assert manager.gaze.is_active is False
        assert manager.pointer.is_active is False
        assert manager.scroll.is_active is False
        assert manager.keyboard.is_active is False

    def test_interaction_manager_update_gaze(self):
        manager = InteractionManager()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        manager.gaze.target = panel
        manager.gaze.activate()
        manager.gaze.update_dwell_time(0.5)
        manager.update_gaze()
        assert manager.gaze_target == panel

    def test_interaction_manager_update_pointer(self):
        manager = InteractionManager()
        manager.pointer.set_position((1.0, 2.0, 3.0))
        manager.pointer.press()
        manager.update_pointer()
        assert manager.pointer_position == (1.0, 2.0, 3.0)
        assert manager.pointer_pressed is True

    def test_interaction_manager_update_scroll(self):
        manager = InteractionManager()
        manager.scroll.update_delta(0.5)
        manager.update_scroll()
        assert manager.scroll_delta == pytest.approx(0.5)

    def test_interaction_manager_update_keyboard(self):
        manager = InteractionManager()
        manager.keyboard.press_key("w")
        manager.update_keyboard()
        assert manager.is_key_pressed("w") is True

    def test_interaction_manager_update_all(self):
        manager = InteractionManager()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        manager.gaze.target = panel
        manager.gaze.activate()
        manager.gaze.update_dwell_time(0.5)
        manager.pointer.set_position((1.0, 2.0, 3.0))
        manager.pointer.press()
        manager.scroll.update_delta(0.5)
        manager.keyboard.press_key("w")
        manager.update_all()
        assert manager.gaze_target == panel
        assert manager.pointer_position == (1.0, 2.0, 3.0)
        assert manager.pointer_pressed is True
        assert manager.scroll_delta == pytest.approx(0.5)
        assert manager.is_key_pressed("w") is True


class TestInteractionEdgeCases:
    """Tests for edge cases and error handling."""

    def test_gaze_dwell_threshold_zero(self):
        gaze = GazeInput()
        gaze.dwell_threshold = 0.0
        gaze.activate()
        gaze.update_dwell_time(0.0)
        assert gaze.dwell_threshold_reached is True

    def test_gaze_dwell_threshold_negative(self):
        gaze = GazeInput()
        gaze.dwell_threshold = -1.0
        gaze.activate()
        gaze.update_dwell_time(0.0)
        assert gaze.dwell_threshold_reached is True

    def test_pointer_position_negative(self):
        pointer = PointerInput()
        pointer.set_position((-1.0, -2.0, -3.0))
        assert pointer.position == (-1.0, -2.0, -3.0)

    def test_scroll_delta_negative(self):
        scroll = ScrollInput()
        scroll.update_delta(-0.5)
        assert scroll.delta == pytest.approx(-0.5)

    def test_keyboard_special_keys(self):
        keyboard = KeyboardInput()
        keyboard.press_key("Escape")
        keyboard.press_key("Shift")
        keyboard.press_key("Ctrl")
        assert "Escape" in keyboard.keys_pressed
        assert "Shift" in keyboard.keys_pressed
        assert "Ctrl" in keyboard.keys_pressed

    def test_interaction_manager_gaze_no_target(self):
        manager = InteractionManager()
        assert manager.gaze_target is None

    def test_interaction_manager_pointer_no_position(self):
        manager = InteractionManager()
        assert manager.pointer_position == (0.0, 0.0, 0.0)

    def test_interaction_manager_scroll_no_delta(self):
        manager = InteractionManager()
        assert manager.scroll_delta == pytest.approx(0.0)

    def test_interaction_manager_keyboard_no_keys(self):
        manager = InteractionManager()
        assert manager.is_key_pressed("w") is False
