"""DashboardVizRenderer: renders a DashboardBoard as a VR scene.

Converts dashboard panels into VR geometry objects with color-coded
visual hints based on ticker data.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.dashboard_board import DashboardBoard
from src.vr_renderer import VRRenderer
from src.vr_scene import VRGeometry, VRScene


class DashboardVizRenderer(VRRenderer):
    """Renders a DashboardBoard as a VR scene with colored geometry.

    Attributes:
        board: The DashboardBoard to render.
        resolution: (width, height) of the render output.
        is_rendered: Whether the board has been rendered.
    """

    def __init__(
        self,
        board: DashboardBoard | None = None,
        resolution: tuple[int, int] = (1920, 1080),
    ) -> None:
        # Create a default scene for the base class
        scene = VRScene()
        super().__init__(scene=scene, resolution=resolution)
        self.board = board or DashboardBoard()
        self.is_rendered = False

    def set_board(self, board: DashboardBoard) -> None:
        """Set the board to render."""
        self.board = board

    def _color_name_to_rgb(self, color_name: str) -> List[float]:
        """Convert a color name to RGB values in [0, 1].

        Args:
            color_name: Color name ('green', 'red', 'white', etc.).

        Returns:
            List of [r, g, b] values in [0, 1].
        """
        color_map = {
            "green": [0.0, 1.0, 0.0],
            "red": [1.0, 0.0, 0.0],
            "white": [1.0, 1.0, 1.0],
            "blue": [0.0, 0.0, 1.0],
            "yellow": [1.0, 1.0, 0.0],
            "orange": [1.0, 0.5, 0.0],
            "purple": [0.5, 0.0, 0.5],
            "cyan": [0.0, 1.0, 1.0],
            "gray": [0.5, 0.5, 0.5],
            "black": [0.0, 0.0, 0.0],
        }
        return color_map.get(color_name, [0.5, 0.5, 0.5])

    def render(self) -> Dict[str, Any]:
        """Render the board as a VR scene.

        Creates geometry objects for each panel with color-coded
        visual hints based on ticker data.

        Returns:
            Dict with scene data, resolution, and rendering metadata.
        """
        # Clear existing geometries
        self.scene.geometries = []

        # Create geometry for each panel
        for i, panel in enumerate(self.board.panels):
            ticker_data = panel.ticker_data
            color_name = ticker_data.get("price_color", "white")
            color_rgb = self._color_name_to_rgb(color_name)

            geometry = VRGeometry(
                geometry_id=f"panel_{i}",
                geometry_type="box",
                position=[panel.x * 2.0, panel.y * 2.0, 0.0],
                scale=[panel.width * 0.8, panel.height * 0.8, 0.1],
                color=color_rgb,
                label=panel.title,
            )
            self.scene.add_geometry(geometry)

        self.is_rendered = True
        return {
            "scene": self.scene.to_dict(),
            "resolution": list(self.resolution),
            "is_rendered": True,
            "render_timestamp": 0.0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the renderer state to a plain dict."""
        return {
            "board": self.board.to_dict(),
            "resolution": list(self.resolution),
            "is_rendered": self.is_rendered,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardVizRenderer":
        """Deserialize a DashboardVizRenderer from a plain dict."""
        board = DashboardBoard.from_dict(data.get("board", {}))
        resolution = tuple(data.get("resolution", [1920, 1080]))
        renderer = cls(board=board, resolution=resolution)
        renderer.is_rendered = data.get("is_rendered", False)
        return renderer
