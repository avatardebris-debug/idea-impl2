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
            state.bankroll.bankroll,
            state.bankroll.peak_bankroll,
            state.bankroll.drawdown,
            state.nash_distance.distance,
            state.nash_distance.current_strategy,
            state.nash_distance.nash_strategy,
        ])

        return output.getvalue()

    def render_panel(self, panel: DashboardPanel) -> str:
        """Render a single panel as CSV string."""
        data = panel.render_data()
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        if self.include_header:
            writer.writerow(data.keys())

        writer.writerow(data.values())
        return output.getvalue()


# == TableauRESTRenderer ==

@dataclass
class TableauRESTRenderer(TableauRenderer):
    """Push dashboard data to Tableau Server via REST API."""

    server_url: str = "https://tableau.example.com"
    site_id: str = "default"
    content_url: str = "projects/default"
    timeout: int = 30
    last_response: Optional[requests.Response] = field(default=None, init=False)
    token: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    payload_fn: Optional[Callable] = None
    url: str = ""  # alias for server_url, for backward compatibility

    def __post_init__(self):
        if self.url and not self.server_url or self.server_url == "https://tableau.example.com":
            if self.url:
                self.server_url = self.url

    def render(self, state: DashboardState) -> str:
        """Render full dashboard state to Tableau Server via REST API."""
        # Handle TableauDashboard input
        if isinstance(state, TableauDashboard):
            panels_data = []
            for panel in state.panels:
                panel_data = panel.render_data()
                panels_data.append({"panel": panel.symbol, "data": panel_data})
            payload = {
                "title": state.title,
                "description": state.description,
                "panels": panels_data,
            }
            return json.dumps(payload)

        if self.payload_fn:
            payload = self.payload_fn(state)
        else:
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
                    "bankroll": state.bankroll.bankroll,
                    "peak_bankroll": state.bankroll.peak_bankroll,
                    "drawdown": state.bankroll.drawdown,
                },
                "nash_distance": {
                    "distance": state.nash_distance.distance,
                    "current_strategy": state.nash_distance.current_strategy,
                    "nash_strategy": state.nash_distance.nash_strategy,
                },
            }

        url = f"{self.server_url}/api/3.16/sites/{self.site_id}/projects/{self.content_url}/data"
        req_headers = {"Content-Type": "application/json"}
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        req_headers.update(self.headers)

        try:
            response = requests.post(url, json=payload, headers=req_headers, timeout=self.timeout)
            self.last_response = response
            return response
        except requests.RequestException:
            self.last_response = None
            return None

    def render_panel(self, panel: DashboardPanel) -> str:
        """Render a single panel as a JSON string for Tableau."""
        data = panel.render_data()
        payload = {
            "panel": panel.symbol,
            "data": data,
        }
        return json.dumps(payload)

    def get_last_response(self) -> Optional[requests.Response]:
        """Return the last HTTP response."""
        return self.last_response


# == TableauDashboard ==

@dataclass
class TableauDashboard:
    """Orchestrates rendering of all panels to Tableau."""

    title: str = "Dashboard"
    description: str = ""
    width: int = 10
    height: int = 10
    x: int = 0
    y: int = 0
    panels: List[DashboardPanel] = field(default_factory=list)
    renderer: Optional[TableauRenderer] = None
    ticker: Optional[DashboardTicker] = None

    def __post_init__(self):
        pass

    def update(self) -> None:
        """Update all panels from the ticker."""
        if self.ticker is None:
            return
        for panel in self.panels:
            panel.update_from_bound_ticker()

    def add_panel(self, panel: DashboardPanel) -> None:
        """Add a panel to this dashboard."""
        self.panels.append(panel)
        if self.ticker is not None:
            panel.bind_ticker(self.ticker)

    def remove_panel(self, panel: DashboardPanel) -> None:
        """Remove a panel from this dashboard."""
        if panel in self.panels:
            self.panels.remove(panel)

    def get_panel_count(self) -> int:
        """Return the number of panels."""
        return len(self.panels)

    def get_panels_by_type(self, panel_type: type) -> List[DashboardPanel]:
        """Return panels of a specific type."""
        return [p for p in self.panels if isinstance(p, panel_type)]

    def bind_ticker(self, ticker: DashboardTicker) -> None:
        """Bind a ticker to this dashboard."""
        self.ticker = ticker
        for panel in self.panels:
            panel.bind_ticker(ticker)

    def render(self, state: Optional[DashboardState] = None) -> Any:
        """Render all panels to Tableau."""
        if self.renderer is None:
            return None

        if state is None:
            if self.ticker is None:
                return None
            state = DashboardState(
                win_rate=self.ticker.current_win_rate,
                bankroll=self.ticker.bankroll_history,
                nash_distance=self.ticker.nash_distance,
                timestamp=self.ticker.timestamp,
            )

        return self.renderer.render(state)

    def render_panel(self, panel: DashboardPanel) -> Any:
        """Render a single panel to Tableau."""
        if self.renderer is None:
            return None
        return self.renderer.render_panel(panel)

    def render_all_panels(self) -> List[Any]:
        """Render all panels to Tableau."""
        if self.renderer is None:
            return []
        return self.renderer.render_panels(self.panels)

    def render_csv(
        self,
        state: DashboardState,
        delimiter: str = ",",
        headers: Optional[Dict[str, str]] = None,
        payload_fn: Optional[Callable] = None,
    ) -> str:
        """Render dashboard state as CSV string, optionally with custom options."""
        # Build combined data from all panels
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)

        # Collect headers
        all_keys = set()
        for panel in self.panels:
            panel_data = panel.render_data()
            all_keys.update(panel_data.keys())

        if headers:
            all_keys.update(headers.keys())

        if payload_fn:
            custom_data = payload_fn(state)
            all_keys.update(custom_data.keys())

        if all_keys:
            writer.writerow(sorted(all_keys))

        # Collect values
        row = {}
        for panel in self.panels:
            panel_data = panel.render_data()
            row.update(panel_data)

        if headers:
            row.update(headers)

        if payload_fn:
            row.update(payload_fn(state))

        writer.writerow([row.get(k, "") for k in sorted(all_keys)])

        return output.getvalue()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize dashboard to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "panels": [p.to_dict() for p in self.panels],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TableauDashboard":
        """Deserialize dashboard from dictionary."""
        panels_data = data.get("panels", [])
        panels = []
        for p_data in panels_data:
            panel_type = p_data.get("type")
            if panel_type == "WinRatePanel":
                panel = WinRatePanel.from_dict(p_data)
            elif panel_type == "BankrollCurvePanel":
                panel = BankrollCurvePanel.from_dict(p_data)
            elif panel_type == "NashEquilibriumPanel":
                panel = NashEquilibriumPanel.from_dict(p_data)
            else:
                panel = WinRatePanel.from_dict(p_data)
            panels.append(panel)

        return cls(
            title=data.get("title", "Dashboard"),
            description=data.get("description", ""),
            width=data.get("width", 10),
            height=data.get("height", 10),
            x=data.get("x", 0),
            y=data.get("y", 0),
            panels=panels,
        )

    def clear_panels(self) -> None:
        """Clear all panels from the dashboard."""
        self.panels.clear()
