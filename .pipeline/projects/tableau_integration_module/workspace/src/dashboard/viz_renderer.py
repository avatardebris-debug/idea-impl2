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
        if self.board.win_rate_panel:
            self._render_win_rate_panel(self.board.win_rate_panel)
        if self.board.bankroll_panel:
            self._render_bankroll_panel(self.board.bankroll_panel)
        if self.board.nash_panel:
            self._render_nash_panel(self.board.nash_panel)

        # Set camera to view the dashboard
        self.scene.camera_position = [0.0, 1.0, 5.0]
        self.scene.camera_look_at = [0.0, 0.0, 0.0]

        # Pass to VRRenderer
        self.vr_renderer.set_scene(self.scene)
        return self.vr_renderer.render()

    def _render_win_rate_panel(self, panel: Any) -> None:
        """Render WinRatePanel as a gauge arc geometry."""
        # Main gauge body (semi-circle approximation using a box)
        gauge_color = self._color_to_rgb(panel.gauge_color)
        gauge_geom = VRGeometry(
            geometry_id=f"{panel.panel_id}_gauge",
            geometry_type="box",
            position=[panel.x + panel.width / 2, panel.y + panel.height / 2, 0.0],
            scale=[panel.width * 0.8, panel.height * 0.3, 0.1],
            color=gauge_color,
            label=f"Win Rate: {panel.gauge_value:.2%}",
        )
        self.scene.add_geometry(gauge_geom)

        # Background frame
        frame_geom = VRGeometry(
            geometry_id=f"{panel.panel_id}_frame",
            geometry_type="box",
            position=[panel.x + panel.width / 2, panel.y + panel.height / 2, -0.01],
            scale=[panel.width * 0.9, panel.height * 0.9, 0.01],
            color=[0.2, 0.2, 0.2],
            label="",
        )
        self.scene.add_geometry(frame_geom)

    def _render_bankroll_panel(self, panel: Any) -> None:
        """Render BankrollCurvePanel as a polyline/area geometry."""
        if not panel.bankroll_points:
            return

        # Create a series of small boxes along the curve
        n_points = len(panel.bankroll_points)
        if n_points < 2:
            return

        # Normalize values to panel coordinates
        min_val = panel.min_bankroll if panel.min_bankroll != panel.max_bankroll else 0.0
        max_val = panel.max_bankroll if panel.min_bankroll != panel.max_bankroll else 1.0
        val_range = max_val - min_val if max_val != min_val else 1.0

        shading_color = self._color_to_rgb(panel.shading_color)

        for i in range(n_points - 1):
            p1 = panel.bankroll_points[i]
            p2 = panel.bankroll_points[i + 1]

            x1 = panel.x + (i / (n_points - 1)) * panel.width
            x2 = panel.x + ((i + 1) / (n_points - 1)) * panel.width
            y1 = panel.y + ((p1.get("value", 0.0) - min_val) / val_range) * panel.height
            y2 = panel.y + ((p2.get("value", 0.0) - min_val) / val_range) * panel.height

            # Line segment
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            seg_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

            line_geom = VRGeometry(
                geometry_id=f"{panel.panel_id}_line_{i}",
                geometry_type="box",
                position=[mid_x, mid_y, 0.0],
                scale=[seg_length, 0.05, 0.05],
                color=shading_color,
                label="",
            )
            self.scene.add_geometry(line_geom)

    def _render_nash_panel(self, panel: Any) -> None:
        """Render NashEquilibriumPanel as a grid of colored boxes."""
        if not panel.heatmap_values:
            return

        n = len(panel.dimensions)
        cell_size = min(panel.width, panel.height) / (n + 1)

        for i in range(n):
            for j in range(n):
                val = panel.heatmap_values[i][j]
                color = self._color_to_rgb(panel.heatmap_colors[i][j])

                # Scale color intensity by value
                intensity = val
                scaled_color = [
                    min(c * intensity + 0.1 * (1 - intensity), 1.0)
                    for c in color
                ]

                box_geom = VRGeometry(
                    geometry_id=f"{panel.panel_id}_cell_{i}_{j}",
                    geometry_type="box",
                    position=[
                        panel.x + (j + 1) * cell_size + cell_size / 2,
                        panel.y + (n - i) * cell_size + cell_size / 2,
                        0.0,
                    ],
                    scale=[cell_size * 0.9, cell_size * 0.9, 0.1],
                    color=scaled_color,
                    label=f"{panel.dimensions[i]} vs {panel.dimensions[j]}",
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
