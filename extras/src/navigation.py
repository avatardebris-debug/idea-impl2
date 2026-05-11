"""VR navigator for the stock ticker application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class VRNavigator:
    """Handles navigation within the VR scene."""

    position: Tuple[float, float, float] = (0.0, 1.6, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    is_moving: bool = False

    def move(self, delta: Tuple[float, float, float]) -> None:
        """Move the navigator by the given delta."""
        self.position = tuple(p + d for p, d in zip(self.position, delta))

    def rotate(self, delta: Tuple[float, float, float]) -> None:
        """Rotate the navigator by the given delta."""
        self.rotation = tuple(r + d for r, d in zip(self.rotation, delta))

    def set_position(self, position: Tuple[float, float, float]) -> None:
        """Set the navigator position."""
        self.position = position

    def set_rotation(self, rotation: Tuple[float, float, float]) -> None:
        """Set the navigator rotation."""
        self.rotation = rotation

    def start_moving(self) -> None:
        """Start moving the navigator."""
        self.is_moving = True

    def stop_moving(self) -> None:
        """Stop moving the navigator."""
        self.is_moving = False

    def get_look_at(self) -> Tuple[float, float, float]:
        """Get the point the navigator is looking at."""
        # Simple look-at calculation based on rotation
        import math
        yaw, pitch, roll = self.rotation
        x = math.cos(math.radians(pitch)) * math.sin(math.radians(yaw))
        y = math.sin(math.radians(pitch))
        z = math.cos(math.radians(pitch)) * math.cos(math.radians(yaw))
        return tuple(p + v for p, v in zip(self.position, (x, y, z)))

    def get_status(self) -> Dict:
        """Get navigator status."""
        return {
            "position": self.position,
            "rotation": self.rotation,
            "velocity": self.velocity,
            "is_moving": self.is_moving,
            "look_at": self.get_look_at(),
        }

    def to_dict(self) -> Dict:
        """Convert navigator to dictionary."""
        return {
            "position": list(self.position),
            "rotation": list(self.rotation),
            "velocity": list(self.velocity),
            "is_moving": self.is_moving,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> VRNavigator:
        """Create a navigator from dictionary."""
        return cls(
            position=tuple(data.get("position", [0.0, 1.6, 0.0])),
            rotation=tuple(data.get("rotation", [0.0, 0.0, 0.0])),
            velocity=tuple(data.get("velocity", [0.0, 0.0, 0.0])),
            is_moving=data.get("is_moving", False),
        )
