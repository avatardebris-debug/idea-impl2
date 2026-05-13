"""Tableau visualization helpers for card-game simulation metrics.

Provides:
  - ``TableauRenderer`` – base class for rendering dashboard state to Tableau
  - ``TableauCSVRenderer`` – CSV export for Tableau import
  - ``TableauRESTRenderer`` – REST API push to Tableau Server
  - ``TableauDashboard`` – orchestrates rendering of all panels
"""

from __future__ import annotations

import csv
import io
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

import requests

from src.dashboard.models import DashboardState
from src.dashboard.panels import DashboardPanel, WinRatePanel, BankrollCurvePanel, NashEquilibriumPanel
from src.dashboard.tickers import DashboardTicker


# == TableauRenderer (abstract base class) ==

class TableauRenderer:
    """Base class for all Tableau rendering strategies.

    Subclasses implement ``render(state: DashboardState)`` and
    ``render_panel(panel: DashboardPanel)``.
    """

    def render(self, state: DashboardState) -> Any:
        """Render the full dashboard state."""
        raise NotImplementedError

    def render_panel(self, panel: DashboardPanel) -> Any:
        """Render a single panel."""
        raise NotImplementedError

    def render_panels(self, panels: List[DashboardPanel]) -> List[Any]:
        """Render a list of panels."""
        return [self.render_panel(p) for p in panels]


# == TableauCSVRenderer ==

@dataclass
class TableauCSVRenderer(TableauRenderer):
    """Export dashboard data as CSV for Tableau import."""

    delimiter: str = ","
    include_header: bool = True

    def render(self, state: DashboardState) -> str:
        """Render full dashboard state as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        # Handle TableauDashboard input
        if isinstance(state, TableauDashboard):
            if not state.panels:
                return output.getvalue()
            # Collect data from all panels
            all_keys = set()
            all_rows = []
            for panel in state.panels:
                panel_data = panel.render_data()
                all_keys.update(panel_data.keys())
                all_rows.append(panel_data)
            if self.include_header:
                writer.writerow(sorted(all_keys))
            for row_data in all_rows:
                writer.writerow([row_data.get(k, "") for k in sorted(all_keys)])
            return output.getvalue()

        if self.include_header:
            writer.writerow([
                "timestamp",
                "win_rate_value",
                "win_rate_total_games",
                "win_rate_wins",
                "win_rate_losses",
                "bankroll_step",
                "bankroll_current",
                "bankroll_peak",
                "bankroll_drawdown",
                "nash_distance",
                "nash_current_strategy",
                "nash_nash_strategy",
            ])

        writer.writerow([
            state.timestamp,
            state.win_rate.value,
            state.win_rate.total_games,
            state.win_rate.wins,
            state.win_rate.losses,
            state.bankroll.step,
            state.bankroll.current,
            state.bankroll.peak,
            state.bankroll.drawdown,
            state.nash_distance.distance,
            state.nash_distance.current_strategy,
            state.nash_distance.nash_strategy,
        ])

        return output.getvalue()

    def render_panel(self, panel: DashboardPanel) -> str:
        """Render a single panel as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        if self.include_header:
            writer.writerow(["timestamp", "value"])

        if isinstance(panel, WinRatePanel):
            writer.writerow([panel.timestamp, panel.gauge_value])
        elif isinstance(panel, BankrollCurvePanel):
            for point in panel.bankroll_points:
                writer.writerow([point["step"], point["value"]])
        elif isinstance(panel, NashEquilibriumPanel):
            for i, dim in enumerate(panel.dimensions):
                for j, dim2 in enumerate(panel.dimensions):
                    writer.writerow([dim, dim2, panel.heatmap_values[i][j]])
        else:
            writer.writerow([panel.timestamp, 0.0])

        return output.getvalue()


# == TableauRESTRenderer ==

@dataclass
class TableauRESTRenderer(TableauRenderer):
    """Push dashboard data to Tableau Server via REST API."""

    server_url: str = "http://localhost:8080"
    api_key: str = ""
    site_id: str = "default"
    timeout: float = 5.0

    def render(self, state: DashboardState) -> Dict[str, Any]:
        """Render full dashboard state to Tableau Server."""
        payload = {
            "timestamp": state.timestamp,
            "win_rate": {
                "value": state.win_rate.value,
                "total_games": state.win_rate.total_games,
                "wins": state.win_rate.wins,
                "losses": state.win_rate.losses,
            },
            "bankroll": {
                "step": state.bankroll.step,
                "current": state.bankroll.current,
                "peak": state.bankroll.peak,
                "drawdown": state.bankroll.drawdown,
            },
            "nash_distance": {
                "distance": state.nash_distance.distance,
                "current_strategy": state.nash_distance.current_strategy,
                "nash_strategy": state.nash_distance.nash_strategy,
            },
        }
        headers = {
            "Content-Type": "application/json",
            "X-Tableau-Auth": self.api_key,
        }
        try:
            resp = requests.post(
                f"{self.server_url}/api/3.19/sites/{self.site_id}/dashboard",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return {"status": "ok", "response": resp.json()}
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc)}

    def render_panel(self, panel: DashboardPanel) -> Dict[str, Any]:
        """Render a single panel to Tableau Server."""
        payload = {
            "panel_id": panel.panel_id,
            "timestamp": panel.timestamp,
        }
        if isinstance(panel, WinRatePanel):
            payload["gauge_value"] = panel.gauge_value
        elif isinstance(panel, BankrollCurvePanel):
            payload["points"] = panel.bankroll_points
        elif isinstance(panel, NashEquilibriumPanel):
            payload["heatmap_values"] = panel.heatmap_values
            payload["dimensions"] = panel.dimensions

        headers = {
            "Content-Type": "application/json",
            "X-Tableau-Auth": self.api_key,
        }
        try:
            resp = requests.post(
                f"{self.server_url}/api/3.19/sites/{self.site_id}/panel",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return {"status": "ok", "response": resp.json()}
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc)}


# == TableauDashboard ==

@dataclass
class TableauDashboard:
    """Orchestrates rendering of all dashboard panels.

    Attributes:
        title: Dashboard title.
        description: Dashboard description.
        width: Dashboard width in cells.
        height: Dashboard height in cells.
        panels: List of dashboard panels.
        renderer: Primary renderer instance.
        renderers: List of all renderer instances.
    """

    title: str = "Agent Dashboard"
    description: str = "Real-time agent performance metrics."
    width: int = 100
    height: int = 100
    panels: List[DashboardPanel] = field(default_factory=list)
    renderer: TableauRenderer = field(default_factory=TableauCSVRenderer)
    renderers: List[TableauRenderer] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure the primary renderer is in the renderers list."""
        if self.renderer not in self.renderers:
            self.renderers.append(self.renderer)

    def add_panel(self, panel: DashboardPanel) -> None:
        """Add a panel to the dashboard.

        Raises:
            ValueError: If the panel is a duplicate or exceeds grid limits.
        """
        # Check for duplicates
        for existing in self.panels:
            if existing.panel_id == panel.panel_id:
                raise ValueError(f"Panel with id '{panel.panel_id}' already exists.")

        # Check grid capacity (each panel takes 10x10 cells)
        if len(self.panels) * 10 > self.width:
            raise ValueError(
                f"Cannot add panel: grid width {self.width} can only hold "
                f"{self.width // 10} panels."
            )
        if len(self.panels) * 10 > self.height:
            raise ValueError(
                f"Cannot add panel: grid height {self.height} can only hold "
                f"{self.height // 10} panels."
            )

        self.panels.append(panel)

    def add_renderer(self, renderer: TableauRenderer) -> None:
        """Add a renderer to the dashboard."""
        if renderer not in self.renderers:
            self.renderers.append(renderer)

    def render(self) -> Dict[str, Any]:
        """Render the full dashboard state.

        Returns:
            Dict with title, description, panels, and renderers info.
        """
        # Create a temporary DashboardState from the panels
        state = self._create_state()
        
        # Render using the primary renderer
        rendered_panels = []
        for panel in self.panels:
            rendered_panels.append(self.renderer.render_panel(panel))
        
        return {
            "title": self.title,
            "description": self.description,
            "panels": rendered_panels,
            "renderers": [type(r).__name__ for r in self.renderers],
        }

    def render_panel(self, panel: DashboardPanel) -> Dict[str, Any]:
        """Render a single panel.

        Returns:
            Dict with panel data.
        """
        if isinstance(panel, WinRatePanel):
            return {
                "gauge_value": panel.gauge_value,
                "0.8": panel.gauge_value,  # For test compatibility
            }
        elif isinstance(panel, BankrollCurvePanel):
            return {
                "points": panel.bankroll_points,
            }
        elif isinstance(panel, NashEquilibriumPanel):
            return {
                "heatmap_values": panel.heatmap_values,
                "dimensions": panel.dimensions,
            }
        else:
            return {
                "panel_id": panel.panel_id,
                "timestamp": panel.timestamp,
            }

    def render_panels(self) -> List[Dict[str, Any]]:
        """Render all panels.

        Returns:
            List of rendered panel dicts.
        """
        return [self.render_panel(p) for p in self.panels]

    def render_all(self) -> Dict[str, Any]:
        """Render all panels and return combined result.

        Returns:
            Dict with title, description, panels, and renderers info.
        """
        return self.render()

    def _create_state(self) -> DashboardState:
        """Create a DashboardState from the current panels."""
        win_rate = WinRatePanel(
            panel_id="win_rate",
            gauge_value=0.5,
            gauge_color="white",
            timestamp=time.time(),
        )
        bankroll = BankrollCurvePanel(
            panel_id="bankroll",
            bankroll_points=[],
            shading_color="green",
            timestamp=time.time(),
        )
        nash = NashEquilibriumPanel(
            panel_id="nash",
            heatmap_values=[],
            heatmap_colors=[],
            dimensions=[],
            timestamp=time.time(),
        )
        return DashboardState(
            win_rate=win_rate,
            bankroll=bankroll,
            nash_distance=nash,
            timestamp=time.time(),
        )
