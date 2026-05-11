"""Tests for the VRNavigator."""

from __future__ import annotations

import pytest
from src.navigation import VRNavigator


class TestVRNavigatorCreation:
    """Tests for VRNavigator creation and initialization."""

    def test_create_default_navigator(self):
        navigator = VRNavigator()
        assert navigator.position == (0.0, 1.6, 0.0)
        assert navigator.rotation == (0.0, 0.0, 0.0)
        assert navigator.velocity == (0.0, 0.0, 0.0)
        assert navigator.is_moving is False

    def test_create_navigator_with_custom_position(self):
        navigator = VRNavigator(position=(1.0, 2.0, 3.0))
        assert navigator.position == (1.0, 2.0, 3.0)

    def test_create_navigator_with_custom_rotation(self):
        navigator = VRNavigator(rotation=(10.0, 20.0, 30.0))
        assert navigator.rotation == (10.0, 20.0, 30.0)

    def test_create_navigator_with_custom_velocity(self):
        navigator = VRNavigator(velocity=(0.5, 0.5, 0.5))
        assert navigator.velocity == (0.5, 0.5, 0.5)


class TestVRNavigatorMovement:
    """Tests for navigator movement."""

    def test_move_forward(self):
        navigator = VRNavigator()
        navigator.move((0.0, 0.0, -1.0))
        assert navigator.position[2] < 0.0  # Moving forward in VR means negative Z

    def test_move_backward(self):
        navigator = VRNavigator()
        navigator.move((0.0, 0.0, 1.0))
        assert navigator.position[2] > 0.0  # Moving backward in VR means positive Z

    def test_move_left(self):
        navigator = VRNavigator()
        navigator.move((-1.0, 0.0, 0.0))
        assert navigator.position[0] < 0.0  # Moving left means negative X

    def test_move_right(self):
        navigator = VRNavigator()
        navigator.move((1.0, 0.0, 0.0))
        assert navigator.position[0] > 0.0  # Moving right means positive X

    def test_move_up(self):
        navigator = VRNavigator()
        navigator.move((0.0, 1.0, 0.0))
        assert navigator.position[1] > 1.6  # Moving up means positive Y

    def test_move_down(self):
        navigator = VRNavigator()
        navigator.move((0.0, -1.0, 0.0))
        assert navigator.position[1] < 1.6  # Moving down means negative Y

    def test_move_multiple_times(self):
        navigator = VRNavigator()
        navigator.move((1.0, 0.0, 0.0))
        navigator.move((1.0, 0.0, 0.0))
        assert navigator.position[0] == 2.0

    def test_move_diagonal(self):
        navigator = VRNavigator()
        navigator.move((1.0, 1.0, -1.0))
        assert navigator.position == (1.0, 2.6, -1.0)


class TestVRNavigatorRotation:
    """Tests for navigator rotation."""

    def test_rotate_yaw(self):
        navigator = VRNavigator()
        navigator.rotate((0.0, 10.0, 0.0))
        assert navigator.rotation[1] == 10.0

    def test_rotate_pitch(self):
        navigator = VRNavigator()
        navigator.rotate((10.0, 0.0, 0.0))
        assert navigator.rotation[0] == 10.0

    def test_rotate_roll(self):
        navigator = VRNavigator()
        navigator.rotate((0.0, 0.0, 10.0))
        assert navigator.rotation[2] == 10.0

    def test_rotate_multiple_times(self):
        navigator = VRNavigator()
        navigator.rotate((10.0, 0.0, 0.0))
        navigator.rotate((10.0, 0.0, 0.0))
        assert navigator.rotation[0] == 20.0


class TestVRNavigatorPositionSetters:
    """Tests for position and rotation setters."""

    def test_set_position(self):
        navigator = VRNavigator()
        navigator.set_position((5.0, 5.0, 5.0))
        assert navigator.position == (5.0, 5.0, 5.0)

    def test_set_rotation(self):
        navigator = VRNavigator()
        navigator.set_rotation((90.0, 45.0, 0.0))
        assert navigator.rotation == (90.0, 45.0, 0.0)


class TestVRNavigatorMovementState:
    """Tests for movement state management."""

    def test_start_moving(self):
        navigator = VRNavigator()
        navigator.start_moving()
        assert navigator.is_moving is True

    def test_stop_moving(self):
        navigator = VRNavigator()
        navigator.start_moving()
        navigator.stop_moving()
        assert navigator.is_moving is False

    def test_stop_moving_when_not_moving(self):
        navigator = VRNavigator()
        navigator.stop_moving()  # Should not raise
        assert navigator.is_moving is False


class TestVRNavigatorLookAt:
    """Tests for look-at calculation."""

    def test_get_look_at_default(self):
        navigator = VRNavigator()
        look_at = navigator.get_look_at()
        assert len(look_at) == 3
        # With default rotation (0,0,0), look_at should be in front of position
        assert look_at[2] < navigator.position[2]  # Looking in negative Z direction

    def test_get_look_at_with_rotation(self):
        navigator = VRNavigator()
        navigator.rotate((0.0, 90.0, 0.0))  # Turn 90 degrees right
        look_at = navigator.get_look_at()
        # Should be looking in positive X direction
        assert look_at[0] > navigator.position[0]


class TestVRNavigatorSerialization:
    """Tests for navigator serialization."""

    def test_to_dict(self):
        navigator = VRNavigator(position=(1.0, 2.0, 3.0), rotation=(10.0, 20.0, 30.0))
        data = navigator.to_dict()
        assert data["position"] == [1.0, 2.0, 3.0]
        assert data["rotation"] == [10.0, 20.0, 30.0]
        assert data["velocity"] == [0.0, 0.0, 0.0]
        assert data["is_moving"] is False

    def test_from_dict(self):
        data = {
            "position": [1.0, 2.0, 3.0],
            "rotation": [10.0, 20.0, 30.0],
            "velocity": [0.5, 0.5, 0.5],
            "is_moving": True,
        }
        navigator = VRNavigator.from_dict(data)
        assert navigator.position == (1.0, 2.0, 3.0)
        assert navigator.rotation == (10.0, 20.0, 30.0)
        assert navigator.velocity == (0.5, 0.5, 0.5)
        assert navigator.is_moving is True

    def test_from_dict_with_defaults(self):
        data = {}
        navigator = VRNavigator.from_dict(data)
        assert navigator.position == (0.0, 1.6, 0.0)
        assert navigator.rotation == (0.0, 0.0, 0.0)
        assert navigator.velocity == (0.0, 0.0, 0.0)
        assert navigator.is_moving is False

    def test_roundtrip(self):
        navigator = VRNavigator(position=(1.0, 2.0, 3.0), rotation=(10.0, 20.0, 30.0), is_moving=True)
        data = navigator.to_dict()
        navigator2 = VRNavigator.from_dict(data)
        assert navigator2.position == navigator.position
        assert navigator2.rotation == navigator.rotation
        assert navigator2.velocity == navigator.velocity
        assert navigator2.is_moving == navigator.is_moving


class TestVRNavigatorStatus:
    """Tests for navigator status reporting."""

    def test_get_status(self):
        navigator = VRNavigator(position=(1.0, 2.0, 3.0), rotation=(10.0, 20.0, 30.0))
        navigator.start_moving()
        status = navigator.get_status()
        assert status["position"] == (1.0, 2.0, 3.0)
        assert status["rotation"] == (10.0, 20.0, 30.0)
        assert status["is_moving"] is True
        assert "look_at" in status
        assert len(status["look_at"]) == 3
