"""DashboardVizRenderer: converts dashboard panel data into VR scene objects.

Maps each panel type to appropriate VR geometry:
  - WinRatePanel → arc/gauge geometry
  - BankrollCurvePanel → polyline/area geometry
  - NashEquilibriumPanel → grid of colored boxes (heatmap)
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.dashboard.layout import DashboardBoard
from src.vr_renderer import VRRenderer
from src.vr_scene import VRGeometry, VRScene
from src.dashboard.panels import WinRatePanel, BankrollCurvePanel, NashEquilibriumPanel


class DashboardVizRenderer:
    """Converts DashboardBoard panel data into VR-renderable scene objects.

    Attributes:
        board: The DashboardBoard to render.
        vr_renderer: Underlying VRRenderer for final output.
        scene: The VRScene being built.
    """

    def __init__(self, board: DashboardBoard | None = None) -> None:
        self.board = board or DashboardBoard()
        self.scene = VRScene(scene_id="dashboard")
        self.vr_renderer = VRRenderer(scene=self.scene)

    def render(self) -> Dict[str, Any]:
        """Render the dashboard board into a VR scene and return the rendered output.

        Returns:
            Dict with the rendered VR scene data.
        """
        self.scene = VRScene(scene_id="dashboard")

        # Render each panel type
        for panel in self.board.panels:
            if isinstance(panel, WinRatePanel):
                self._render_win_rate_panel(panel)
            elif isinstance(panel, BankrollCurvePanel):
                self._render_bankroll_panel(panel)
            elif isinstance(panel, NashEquilibriumPanel):
                self._render_nash_panel(panel)

        # Set camera to view the dashboard
        self.scene.camera_position = [0.0, 1.0, 5.0]
        self.scene.camera_look_at = [0.0, 0.0, 0.0]

        # Pass to VRRenderer
        self.vr_renderer.set_scene(self.scene)
        return self.vr_renderer.render()

    def _render_win_rate_panel(self, panel: Any) -> None:
        """Render WinRatePanel as a gauge arc geometry."""
        # Main gauge body (semi-circle approximation using a box)
        gauge_color = self._color_to_rgb(panel.get_visual_encoding().get("color", "white"))
        gauge_geom = VRGeometry(
            geometry_id=f"{panel.symbol}_gauge",
            geometry_type="box",
            position=[panel.x + panel.width / 2, panel.y + panel.height / 2, 0.0],
            scale=[panel.width * 0.8, panel.height * 0.3, 0.1],
            color=gauge_color,
            label=f"Win Rate: {panel.gauge_value:.2%}",
        )
        self.scene.add_geometry(gauge_geom)

        # Background frame
        frame_geom = VRGeometry(
            geometry_id=f"{panel.symbol}_frame",
            geometry_type="box",
            position=[panel.x + panel.width / 2, panel.y + panel.height / 2, -0.01],
            scale=[panel.width * 0.9, panel.height * 0.9, 0.01],
            color=[0.2, 0.2, 0.2],
            label="",
        )
        self.scene.add_geometry(frame_geom)

    def _render_bankroll_panel(self, panel: Any) -> None:
        """Render BankrollCurvePanel as a polyline/area geometry."""
        if not panel.sparkline:
            return

        # Create a series of small boxes along the curve
        n_points = len(panel.sparkline)
        if n_points < 2:
            return

        # Normalize values to panel coordinates
        min_val = min(panel.sparkline)
        max_val = max(panel.sparkline)
        val_range = max_val - min_val if max_val != min_val else 1.0

        shading_color = self._color_to_rgb(panel.get_visual_encoding().get("color", "white"))

        for i in range(n_points - 1):
            p1 = panel.sparkline[i]
            p2 = panel.sparkline[i + 1]

            x1 = panel.x + (i / (n_points - 1)) * panel.width
            x2 = panel.x + ((i + 1) / (n_points - 1)) * panel.width
            y1 = panel.y + ((p1 - min_val) / val_range) * panel.height
            y2 = panel.y + ((p2 - min_val) / val_range) * panel.height

            # Line segment
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            seg_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

            line_geom = VRGeometry(
                geometry_id=f"{panel.symbol}_line_{i}",
                geometry_type="box",
                position=[mid_x, mid_y, 0.0],
                scale=[seg_length, 0.05, 0.05],
                color=shading_color,
                label="",
            )
            self.scene.add_geometry(line_geom)

    def _render_nash_panel(self, panel: Any) -> None:
        """Render NashEquilibriumPanel as a grid of colored boxes."""
        color = self._color_to_rgb(panel.get_visual_encoding().get("color", "white"))

        box_geom = VRGeometry(
            geometry_id=f"{panel.symbol}_cell",
            geometry_type="box",
            position=[
                panel.x + panel.width / 2,
                panel.y + panel.height / 2,
                0.0,
            ],
            scale=[panel.width * 0.9, panel.height * 0.9, 0.1],
            color=color,
            label=f"Nash Dist: {panel.distance:.2f}",
        )
        self.scene.add_geometry(box_geom)

    def _color_to_rgb(self, color_name: str) -> List[float]:
        """Convert a color name string to RGB list."""
        color_map = {
            "white": [1.0, 1.0, 1.0],
            "green": [0.0, 1.0, 0.0],
            "red": [1.0, 0.0, 0.0],
            "yellow": [1.0, 1.0, 0.0],
            "orange": [1.0, 0.65, 0.0],
        }
        return color_map.get(color_name.lower(), [0.5, 0.5, 0.5])
