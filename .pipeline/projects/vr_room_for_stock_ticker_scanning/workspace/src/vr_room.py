"""VR room environment — defines the 3D room structure (floor, walls, ceiling)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class RoomGeometry:
    """Represents a single geometric surface of the room."""
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    size: Tuple[float, float, float]
    color: Tuple[float, float, float]
    material_type: str = "wall"  # "floor", "wall", "ceiling"


@dataclass
class VRRoom:
    """Represents the VR room environment."""

    width: float = 10.0
    height: float = 3.0
    depth: float = 10.0
    floor_color: Tuple[float, float, float] = (0.2, 0.2, 0.2)
    wall_color: Tuple[float, float, float] = (0.1, 0.1, 0.15)
    ceiling_color: Tuple[float, float, float] = (0.05, 0.05, 0.05)
    is_enabled: bool = True

    def get_geometry(self) -> List[RoomGeometry]:
        """Get all room geometry surfaces."""
        if not self.is_enabled:
            return []

        half_w = self.width / 2
        half_d = self.depth / 2
        h = self.height

        geometries = []

        # Floor
        geometries.append(RoomGeometry(
            position=(0.0, 0.0, 0.0),
            rotation=(-90.0, 0.0, 0.0),
            size=(self.width, 0.1, self.depth),
            color=self.floor_color,
            material_type="floor"
        ))

        # Ceiling
        geometries.append(RoomGeometry(
            position=(0.0, h, 0.0),
            rotation=(90.0, 0.0, 0.0),
            size=(self.width, 0.1, self.depth),
            color=self.ceiling_color,
            material_type="ceiling"
        ))

        # Back Wall
        geometries.append(RoomGeometry(
            position=(0.0, h / 2, -half_d),
            rotation=(0.0, 0.0, 0.0),
            size=(self.width, h, 0.1),
            color=self.wall_color,
            material_type="wall"
        ))

        # Front Wall
        geometries.append(RoomGeometry(
            position=(0.0, h / 2, half_d),
            rotation=(0.0, 180.0, 0.0),
            size=(self.width, h, 0.1),
            color=self.wall_color,
            material_type="wall"
        ))

        # Left Wall
        geometries.append(RoomGeometry(
            position=(-half_w, h / 2, 0.0),
            rotation=(0.0, 90.0, 0.0),
            size=(self.depth, h, 0.1),
            color=self.wall_color,
            material_type="wall"
        ))

        # Right Wall
        geometries.append(RoomGeometry(
            position=(half_w, h / 2, 0.0),
            rotation=(0.0, -90.0, 0.0),
            size=(self.depth, h, 0.1),
            color=self.wall_color,
            material_type="wall"
        ))

        return geometries

    def to_dict(self) -> dict:
        """Convert room to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "floor_color": list(self.floor_color),
            "wall_color": list(self.wall_color),
            "ceiling_color": list(self.ceiling_color),
            "is_enabled": self.is_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> VRRoom:
        """Create room from dictionary."""
        room = cls()
        room.width = data.get("width", 10.0)
        room.height = data.get("height", 3.0)
        room.depth = data.get("depth", 10.0)
        room.floor_color = tuple(data.get("floor_color", (0.2, 0.2, 0.2)))
        room.wall_color = tuple(data.get("wall_color", (0.1, 0.1, 0.15)))
        room.ceiling_color = tuple(data.get("ceiling_color", (0.05, 0.05, 0.05)))
        room.is_enabled = data.get("is_enabled", True)
        return room
