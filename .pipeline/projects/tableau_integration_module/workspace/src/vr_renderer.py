"""VRRenderer: base class for rendering VR scenes.

Provides a simple renderer interface that takes a VRScene and
produces a rendered output dict compatible with VR display systems.
"""

from __future__ import annotations

from typing import Any, Dict

from src.vr_scene import VRScene


class VRRenderer:
    """Renders a VRScene into a displayable output.

    Attributes:
        scene: The VRScene to render.
        resolution: (width, height) of the render output.
        is_rendered: Whether the scene has been rendered.
    """

    def __init__(
        self,
        scene: VRScene | None = None,
        resolution: tuple[int, int] = (1920, 1080),
    ) -> None:
        self.scene = scene or VRScene()
        self.resolution = resolution
        self.is_rendered = False

    def set_scene(self, scene: VRScene) -> None:
        """Set the scene to render."""
        self.scene = scene

    def render(self) -> Dict[str, Any]:
        """Render the current scene and return the output dict.

        Returns:
            Dict with scene data, resolution, and rendering metadata.
        """
        rendered = {
            "scene": self.scene.to_dict(),
            "resolution": list(self.resolution),
            "is_rendered": True,
            "render_timestamp": 0.0,  # Would be time.time() in real impl
        }
        self.is_rendered = True
        return rendered

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the renderer state to a plain dict."""
        return {
            "scene": self.scene.to_dict(),
            "resolution": list(self.resolution),
            "is_rendered": self.is_rendered,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VRRenderer":
        """Deserialize a VRRenderer from a plain dict."""
        scene = VRScene.from_dict(data.get("scene", {}))
        resolution = tuple(data.get("resolution", [1920, 1080]))
        renderer = cls(scene=scene, resolution=resolution)
        renderer.is_rendered = data.get("is_rendered", False)
        return renderer
