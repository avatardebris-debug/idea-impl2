"""Camera module — VR camera controls with position, orientation, and projection."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class Vector3:
    """3D vector with common operations."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3":
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vector3":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector3":
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide vector by zero")
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self) -> "Vector3":
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)
        return self / mag

    def dot(self, other: "Vector3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vector3") -> "Vector3":
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def distance_to(self, other: "Vector3") -> float:
        return (self - other).magnitude()

    def lerp(self, other: "Vector3", t: float) -> "Vector3":
        return Vector3(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t,
        )


@dataclass
class Camera:
    """VR camera with position, orientation (yaw/pitch), and projection settings."""
    position: Vector3 = field(default_factory=Vector3)
    yaw: float = 0.0       # horizontal rotation in radians
    pitch: float = 0.0     # vertical rotation in radians
    fov: float = math.pi / 3  # field of view in radians (60 degrees)
    near: float = 0.1
    far: float = 1000.0
    aspect_ratio: float = 16.0 / 9.0
    sensitivity: float = 0.003  # mouse sensitivity for rotation

    @property
    def forward(self) -> Vector3:
        """Compute the forward direction vector from yaw and pitch."""
        yaw_rad = math.radians(math.degrees(self.yaw))
        pitch_rad = math.radians(math.degrees(self.pitch))
        x = math.cos(pitch_rad) * math.sin(yaw_rad)
        y = math.sin(pitch_rad)
        z = math.cos(pitch_rad) * math.cos(yaw_rad)
        return Vector3(x, y, z).normalized()

    @property
    def right(self) -> Vector3:
        """Compute the right direction vector (cross product of forward and up)."""
        forward = self.forward
        up = Vector3(0, 1, 0)
        return forward.cross(up).normalized()

    @property
    def up(self) -> Vector3:
        """Compute the up direction vector (right cross forward gives +Y for default orientation)."""
        return self.right.cross(self.forward).normalized()

    @property
    def target(self) -> Vector3:
        """The point the camera is looking at."""
        return self.position + self.forward

    def rotate(self, dx: float, dy: float) -> None:
        """Rotate the camera by delta angles (in radians)."""
        self.yaw += dx * self.sensitivity
        self.pitch += dy * self.sensitivity
        # Clamp pitch to avoid flipping
        max_pitch = math.pi / 2 - 0.01
        self.pitch = max(-max_pitch, min(max_pitch, self.pitch))

    def move_forward(self, distance: float) -> None:
        """Move the camera forward/backward along its forward vector."""
        self.position = self.position + self.forward * distance

    def move_right(self, distance: float) -> None:
        """Strafe the camera right/left along its right vector."""
        self.position = self.position + self.right * distance

    def move_up(self, distance: float) -> None:
        """Move the camera up/down."""
        self.position = self.position + Vector3(0, distance, 0)

    def get_view_matrix(self) -> List[List[float]]:
        """Compute the 4x4 view matrix (look-at matrix)."""
        forward = self.forward
        right = self.right
        up = self.up
        pos = self.position

        # Build view matrix (row-major for OpenGL)
        return [
            [right.x, up.x, -forward.x, 0],
            [right.y, up.y, -forward.y, 0],
            [right.z, up.z, -forward.z, 0],
            [-right.dot(pos), -up.dot(pos), forward.dot(pos), 1],
        ]

    def get_projection_matrix(self, width: int, height: int) -> List[List[float]]:
        """Compute the 4x4 projection matrix (perspective)."""
        aspect = width / height if height > 0 else 1.0
        f = 1.0 / math.tan(self.fov / 2)
        return [
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, -(self.far + self.near) / (self.near - self.far), 1],
            [0, 0, -(2 * self.far * self.near) / (self.near - self.far), 0],
        ]

    def reset(self) -> None:
        """Reset camera to default state."""
        self.position = Vector3(0, 1.6, 0)  # ~eye height
        self.yaw = 0.0
        self.pitch = 0.0
