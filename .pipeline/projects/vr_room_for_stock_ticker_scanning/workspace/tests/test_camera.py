"""Tests for Vector3 and Camera modules."""

from __future__ import annotations

import math
import pytest
from src.camera import Vector3, Camera


class TestVector3Creation:
    """Tests for Vector3 instantiation."""

    def test_default_vector(self):
        v = Vector3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_vector_with_values(self):
        v = Vector3(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_vector_with_negative_values(self):
        v = Vector3(-1.0, -2.0, -3.0)
        assert v.x == -1.0
        assert v.y == -2.0
        assert v.z == -3.0


class TestVector3Arithmetic:
    """Tests for Vector3 arithmetic operations."""

    def test_addition(self):
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        result = v1 + v2
        assert result.x == 5.0
        assert result.y == 7.0
        assert result.z == 9.0

    def test_subtraction(self):
        v1 = Vector3(4.0, 5.0, 6.0)
        v2 = Vector3(1.0, 2.0, 3.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 3.0
        assert result.z == 3.0

    def test_scalar_multiplication(self):
        v = Vector3(1.0, 2.0, 3.0)
        result = v * 2.0
        assert result.x == 2.0
        assert result.y == 4.0
        assert result.z == 6.0

    def test_scalar_multiplication_reverse(self):
        v = Vector3(1.0, 2.0, 3.0)
        result = 2.0 * v
        assert result.x == 2.0
        assert result.y == 4.0
        assert result.z == 6.0

    def test_scalar_multiplication_zero(self):
        v = Vector3(1.0, 2.0, 3.0)
        result = v * 0.0
        assert result.x == 0.0
        assert result.y == 0.0
        assert result.z == 0.0

    def test_scalar_multiplication_negative(self):
        v = Vector3(1.0, 2.0, 3.0)
        result = v * -1.0
        assert result.x == -1.0
        assert result.y == -2.0
        assert result.z == -3.0

    def test_division(self):
        v = Vector3(4.0, 6.0, 8.0)
        result = v / 2.0
        assert result.x == 2.0
        assert result.y == 3.0
        assert result.z == 4.0

    def test_division_by_zero(self):
        v = Vector3(1.0, 2.0, 3.0)
        with pytest.raises(ZeroDivisionError):
            v / 0.0


class TestVector3Properties:
    """Tests for Vector3 properties and methods."""

    def test_magnitude(self):
        v = Vector3(3.0, 4.0, 0.0)
        assert v.magnitude() == pytest.approx(5.0)

    def test_magnitude_zero_vector(self):
        v = Vector3(0.0, 0.0, 0.0)
        assert v.magnitude() == 0.0

    def test_magnitude_3d(self):
        v = Vector3(1.0, 2.0, 2.0)
        assert v.magnitude() == pytest.approx(3.0)

    def test_normalized(self):
        v = Vector3(3.0, 4.0, 0.0)
        normalized = v.normalized()
        assert normalized.magnitude() == pytest.approx(1.0)
        assert normalized.x == pytest.approx(0.6)
        assert normalized.y == pytest.approx(0.8)
        assert normalized.z == pytest.approx(0.0)

    def test_normalized_zero_vector(self):
        v = Vector3(0.0, 0.0, 0.0)
        normalized = v.normalized()
        assert normalized.x == 0.0
        assert normalized.y == 0.0
        assert normalized.z == 0.0

    def test_dot_product(self):
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        assert v1.dot(v2) == pytest.approx(32.0)

    def test_dot_product_orthogonal(self):
        v1 = Vector3(1.0, 0.0, 0.0)
        v2 = Vector3(0.0, 1.0, 0.0)
        assert v1.dot(v2) == 0.0

    def test_cross_product(self):
        v1 = Vector3(1.0, 0.0, 0.0)
        v2 = Vector3(0.0, 1.0, 0.0)
        result = v1.cross(v2)
        assert result.x == pytest.approx(0.0)
        assert result.y == pytest.approx(0.0)
        assert result.z == pytest.approx(1.0)

    def test_cross_product_anti_commutative(self):
        v1 = Vector3(1.0, 0.0, 0.0)
        v2 = Vector3(0.0, 1.0, 0.0)
        result1 = v1.cross(v2)
        result2 = v2.cross(v1)
        assert result1.x == pytest.approx(-result2.x)
        assert result1.y == pytest.approx(-result2.y)
        assert result1.z == pytest.approx(-result2.z)

    def test_distance_to(self):
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(3.0, 4.0, 0.0)
        assert v1.distance_to(v2) == pytest.approx(5.0)

    def test_distance_to_same_point(self):
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(1.0, 2.0, 3.0)
        assert v1.distance_to(v2) == 0.0

    def test_lerp(self):
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(10.0, 10.0, 10.0)
        result = v1.lerp(v2, 0.5)
        assert result.x == pytest.approx(5.0)
        assert result.y == pytest.approx(5.0)
        assert result.z == pytest.approx(5.0)

    def test_lerp_at_start(self):
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(10.0, 10.0, 10.0)
        result = v1.lerp(v2, 0.0)
        assert result.x == pytest.approx(0.0)
        assert result.y == pytest.approx(0.0)
        assert result.z == pytest.approx(0.0)

    def test_lerp_at_end(self):
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(10.0, 10.0, 10.0)
        result = v1.lerp(v2, 1.0)
        assert result.x == pytest.approx(10.0)
        assert result.y == pytest.approx(10.0)
        assert result.z == pytest.approx(10.0)


class TestCameraCreation:
    """Tests for Camera instantiation."""

    def test_default_camera(self):
        camera = Camera()
        assert camera.position.x == 0.0
        assert camera.position.y == 0.0
        assert camera.position.z == 0.0
        assert camera.yaw == 0.0
        assert camera.pitch == 0.0
        assert camera.fov == math.pi / 3
        assert camera.near == 0.1
        assert camera.far == 1000.0
        assert camera.aspect_ratio == pytest.approx(16.0 / 9.0)
        assert camera.sensitivity == 0.003

    def test_camera_with_custom_position(self):
        camera = Camera(position=Vector3(1.0, 2.0, 3.0))
        assert camera.position.x == 1.0
        assert camera.position.y == 2.0
        assert camera.position.z == 3.0

    def test_camera_with_custom_fov(self):
        camera = Camera(fov=math.pi / 2)
        assert camera.fov == math.pi / 2

    def test_camera_with_custom_near_far(self):
        camera = Camera(near=0.01, far=100.0)
        assert camera.near == 0.01
        assert camera.far == 100.0


class TestCameraOrientation:
    """Tests for camera orientation and direction vectors."""

    def test_forward_default(self):
        camera = Camera()
        forward = camera.forward
        assert forward.magnitude() == pytest.approx(1.0)
        # Default forward should be along +Z axis
        assert forward.z == pytest.approx(1.0)
        assert forward.x == pytest.approx(0.0)
        assert forward.y == pytest.approx(0.0)

    def test_forward_with_yaw(self):
        camera = Camera(yaw=math.pi / 2)
        forward = camera.forward
        assert forward.magnitude() == pytest.approx(1.0)
        # Yaw of 90 degrees should point along +X
        assert forward.x == pytest.approx(1.0)
        assert forward.z == pytest.approx(0.0)

    def test_forward_with_pitch(self):
        camera = Camera(pitch=math.pi / 2)
        forward = camera.forward
        assert forward.magnitude() == pytest.approx(1.0)
        # Pitch of 90 degrees should point along +Y
        assert forward.y == pytest.approx(1.0)

    def test_right_default(self):
        camera = Camera()
        right = camera.right
        assert right.magnitude() == pytest.approx(1.0)
        # Default right should be along -X axis (cross product of forward and up)
        assert right.x == pytest.approx(-1.0)
        assert right.z == pytest.approx(0.0)

    def test_up_default(self):
        camera = Camera()
        up = camera.up
        assert up.magnitude() == pytest.approx(1.0)
        # Default up should be along +Y axis
        assert up.y == pytest.approx(1.0)
        assert up.x == pytest.approx(0.0)
        assert up.z == pytest.approx(0.0)

    def test_target(self):
        camera = Camera(position=Vector3(0.0, 0.0, 0.0))
        target = camera.target
        # Target should be position + forward
        expected = camera.position + camera.forward
        assert target.x == pytest.approx(expected.x)
        assert target.y == pytest.approx(expected.y)
        assert target.z == pytest.approx(expected.z)

    def test_target_with_position(self):
        camera = Camera(position=Vector3(1.0, 2.0, 3.0))
        target = camera.target
        expected = camera.position + camera.forward
        assert target.x == pytest.approx(expected.x)
        assert target.y == pytest.approx(expected.y)
        assert target.z == pytest.approx(expected.z)


class TestCameraMovement:
    """Tests for camera movement methods."""

    def test_rotate(self):
        camera = Camera()
        initial_yaw = camera.yaw
        initial_pitch = camera.pitch
        camera.rotate(1.0, 0.0)
        assert camera.yaw == pytest.approx(initial_yaw + 0.003)
        assert camera.pitch == initial_pitch

    def test_rotate_pitch(self):
        camera = Camera()
        initial_pitch = camera.pitch
        camera.rotate(0.0, 1.0)
        assert camera.pitch == pytest.approx(initial_pitch + 0.003)

    def test_rotate_clamps_pitch(self):
        camera = Camera()
        # Set pitch close to max
        camera.pitch = math.pi / 2 - 0.005
        camera.rotate(0.0, 1000.0)  # Large rotation
        assert camera.pitch <= math.pi / 2 - 0.01
        assert camera.pitch >= -(math.pi / 2 - 0.01)

    def test_move_forward(self):
        camera = Camera(position=Vector3(0.0, 0.0, 0.0))
        initial_pos = camera.position
        camera.move_forward(1.0)
        # Should move along forward vector
        expected = initial_pos + camera.forward * 1.0
        assert camera.position.x == pytest.approx(expected.x)
        assert camera.position.y == pytest.approx(expected.y)
        assert camera.position.z == pytest.approx(expected.z)

    def test_move_right(self):
        camera = Camera(position=Vector3(0.0, 0.0, 0.0))
        initial_pos = camera.position
        camera.move_right(1.0)
        # Should move along right vector
        expected = initial_pos + camera.right * 1.0
        assert camera.position.x == pytest.approx(expected.x)
        assert camera.position.y == pytest.approx(expected.y)
        assert camera.position.z == pytest.approx(expected.z)

    def test_move_up(self):
        camera = Camera(position=Vector3(0.0, 0.0, 0.0))
        initial_pos = camera.position
        camera.move_up(1.0)
        # Should move along Y axis
        assert camera.position.x == initial_pos.x
        assert camera.position.y == pytest.approx(initial_pos.y + 1.0)
        assert camera.position.z == initial_pos.z

    def test_move_backward(self):
        camera = Camera(position=Vector3(0.0, 0.0, 0.0))
        initial_pos = camera.position
        camera.move_forward(-1.0)
        # Should move opposite to forward vector
        expected = initial_pos + camera.forward * (-1.0)
        assert camera.position.x == pytest.approx(expected.x)
        assert camera.position.y == pytest.approx(expected.y)
        assert camera.position.z == pytest.approx(expected.z)


class TestCameraMatrices:
    """Tests for camera matrix generation."""

    def test_view_matrix_dimensions(self):
        camera = Camera()
        view_matrix = camera.get_view_matrix()
        assert len(view_matrix) == 4
        for row in view_matrix:
            assert len(row) == 4

    def test_projection_matrix_dimensions(self):
        camera = Camera()
        proj_matrix = camera.get_projection_matrix(1920, 1080)
        assert len(proj_matrix) == 4
        for row in proj_matrix:
            assert len(row) == 4

    def test_projection_matrix_aspect_ratio(self):
        camera = Camera()
        # Square aspect ratio
        proj1 = camera.get_projection_matrix(100, 100)
        # Wide aspect ratio
        proj2 = camera.get_projection_matrix(200, 100)
        # The f/aspect value should differ
        assert proj1[0][0] != proj2[0][0]

    def test_view_matrix_with_position(self):
        camera = Camera(position=Vector3(1.0, 2.0, 3.0))
        view_matrix = camera.get_view_matrix()
        # The last row should contain dot products with position
        assert len(view_matrix[3]) == 4

    def test_projection_matrix_with_fov(self):
        camera = Camera(fov=math.pi / 2)
        proj = camera.get_projection_matrix(100, 100)
        # f = 1/tan(fov/2) = 1/tan(pi/4) = 1
        expected_f = 1.0 / math.tan(math.pi / 4)
        assert proj[1][1] == pytest.approx(expected_f)


class TestCameraReset:
    """Tests for camera reset functionality."""

    def test_reset_position(self):
        camera = Camera(position=Vector3(10.0, 20.0, 30.0))
        camera.reset()
        assert camera.position.x == pytest.approx(0.0)
        assert camera.position.y == pytest.approx(1.6)
        assert camera.position.z == pytest.approx(0.0)

    def test_reset_orientation(self):
        camera = Camera(yaw=math.pi, pitch=math.pi / 4)
        camera.reset()
        assert camera.yaw == pytest.approx(0.0)
        assert camera.pitch == pytest.approx(0.0)

    def test_reset_preserves_settings(self):
        camera = Camera(fov=math.pi / 2, near=0.01, far=500.0)
        camera.reset()
        assert camera.fov == math.pi / 2
        assert camera.near == 0.01
        assert camera.far == 500.0


class TestCameraIntegration:
    """Integration tests for camera functionality."""

    def test_rotate_and_move(self):
        camera = Camera()
        # Rotate to face +X
        camera.rotate(math.pi / 2 / 0.003, 0.0)
        # Move forward
        camera.move_forward(1.0)
        # Position should have changed in X direction
        assert camera.position.x != 0.0

    def test_view_and_projection_matrices(self):
        camera = Camera()
        view = camera.get_view_matrix()
        proj = camera.get_projection_matrix(1920, 1080)
        # Both matrices should be 4x4
        assert len(view) == 4 and all(len(row) == 4 for row in view)
        assert len(proj) == 4 and all(len(row) == 4 for row in proj)

    def test_camera_forward_is_unit_vector(self):
        camera = Camera()
        for _ in range(10):
            camera.rotate(0.1, 0.1)
            assert camera.forward.magnitude() == pytest.approx(1.0)

    def test_camera_right_is_orthogonal_to_forward(self):
        camera = Camera()
        dot = camera.right.dot(camera.forward)
        assert dot == pytest.approx(0.0)

    def test_camera_up_is_orthogonal_to_forward(self):
        camera = Camera()
        dot = camera.up.dot(camera.forward)
        assert dot == pytest.approx(0.0)

    def test_camera_up_is_orthogonal_to_right(self):
        camera = Camera()
        dot = camera.up.dot(camera.right)
        assert dot == pytest.approx(0.0)
