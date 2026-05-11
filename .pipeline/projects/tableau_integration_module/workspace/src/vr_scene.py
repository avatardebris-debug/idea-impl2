"""VRScene: base class for VR scene objects.

Provides a simple scene graph that can hold renderable geometry
and be serialized for the VR renderer pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class VRGeometry:
    """A renderable geometry primitive in the VR scene.

    Attributes:
        geometry_id: Unique identifier.
        geometry_type: Type of geometry (e.g., 'box', 'sphere', 'plane').
        position: (x, y, z) position in 3D space.
        scale: (x, y, z) scale factors.
        color: (r, g, b) color values in [0, 1].
        label: Optional display label.
    """

    geometry_id: str = ""
    geometry_type: str = "box"
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    color: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize geometry to a plain dict."""
        return {
            "geometry_id": self.geometry_id,
            "geometry_type": self.geometry_type,
            "position": self.position,
            "scale": self.scale,
            "color": self.color,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VRGeometry":
        """Deserialize a VRGeometry from a plain dict."""
        return cls(
            geometry_id=data.get("geometry_id", ""),
            geometry_type=data.get("geometry_type", "box"),
            position=[float(v) for v in data.get("position", [0.0, 0.0, 0.0])],
            scale=[float(v) for v in data.get("scale", [1.0, 1.0, 1.0])],
            color=[float(v) for v in data.get("color", [1.0, 1.0, 1.0])],
            label=data.get("label", ""),
        )


@dataclass
class VRScene:
    """A VR scene containing multiple geometry objects.

    Attributes:
        scene_id: Unique identifier for the scene.
        geometries: List of VRGeometry objects in the scene.
        camera_position: (x, y, z) camera position.
        camera_look_at: (x, y, z) camera target.
    """

    scene_id: str = "default"
    geometries: List[VRGeometry] = field(default_factory=list)
    camera_position: List[float] = field(default_factory=lambda: [0.0, 0.0, 5.0])
    camera_look_at: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])

    def add_geometry(self, geometry: VRGeometry) -> None:
        """Add a geometry to the scene."""
        self.geometries.append(geometry)

    def remove_geometry(self, geometry_id: str) -> bool:
        """Remove a geometry by ID."""
        for i, g in enumerate(self.geometries):
            if g.geometry_id == geometry_id:
                self.geometries.pop(i)
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the scene to a plain dict."""
        return {
            "scene_id": self.scene_id,
            "geometries": [g.to_dict() for g in self.geometries],
            "camera_position": self.camera_position,
            "camera_look_at": self.camera_look_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VRScene":
        """Deserialize a VRScene from a plain dict."""
        scene = cls(
            scene_id=data.get("scene_id", "default"),
            camera_position=[float(v) for v in data.get("camera_position", [0.0, 0.0, 5.0])],
            camera_look_at=[float(v) for v in data.get("camera_look_at", [0.0, 0.0, 0.0])],
        )
        for g_data in data.get("geometries", []):
            scene.add_geometry(VRGeometry.from_dict(g_data))
        return scene
