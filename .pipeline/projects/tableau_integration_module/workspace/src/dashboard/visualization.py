"""Visualization renderers for the Tableau dashboard.

Provides three rendering strategies:
  - TableauRenderer: abstract base with common logic.
  - TableauCSVRenderer: exports to CSV for Tableau import.
  - TableauRESTRenderer: serves via a lightweight HTTP endpoint.
  - TableauDashboard: orchestrates rendering of all panels.
"""

from __future__ import annotations

import csv
import io
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests

from src.dashboard.panels import (
    DashboardPanel,
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
from src.dashboard.models import DashboardState
from src.dashboard.tickers import DashboardTicker


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class TableauRenderer(ABC):
    """Abstract base for all Tableau renderers."""

    def render(self, state: DashboardState) -> Any:
        """Render the dashboard. Subclasses define the output format."""
        raise NotImplementedError

    def render_panel(self, panel: DashboardPanel) -> Any:
        """Render a single panel."""
        raise NotImplementedError

    def render_panels(self, panels: List[DashboardPanel]) -> List[Any]:
        """Render a list of panels."""
        return [self.render_panel(p) for p in panels]


# ---------------------------------------------------------------------------
# CSV Renderer
# ---------------------------------------------------------------------------

@dataclass
class TableauCSVRenderer(TableauRenderer):
    """Render dashboard state as CSV rows for Tableau import."""

    delimiter: str = ","
    include_header: bool = True

    def render(self, state: DashboardState) -> str:
        """Return CSV string with one row per panel."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

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


# ---------------------------------------------------------------------------
# REST Renderer
# ---------------------------------------------------------------------------

class _RESTHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler that serves JSON dashboard state."""

    renderer: TableauRESTRenderer = None  # type: ignore[assignment]

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/dashboard":
            data = self.renderer.render()
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        pass  # Suppress default logging


@dataclass
class TableauRESTRenderer(TableauRenderer):
    """Render dashboard state via a lightweight HTTP endpoint."""

    server_url: str = "https://tableau.example.com"
    site_id: str = "default"
    content_url: str = "projects/default"
    timeout: int = 30
    last_response: Optional[requests.Response] = field(default=None, init=False)

    def render(self, state: DashboardState) -> Optional[requests.Response]:
        """Render full dashboard state to Tableau Server via REST API."""
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
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            self.last_response = response
            return response
        except requests.RequestException:
            self.last_response = None
            return None

    def render_panel(self, panel: DashboardPanel) -> Optional[requests.Response]:
        """Render a single panel to Tableau Server via REST API."""
        data = panel.render_data()
        payload = {
            "panel": panel.symbol,
            "data": data,
        }

        url = f"{self.server_url}/api/3.16/sites/{self.site_id}/projects/{self.content_url}/data"
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            self.last_response = response
            return response
        except requests.RequestException:
            self.last_response = None
            return None

    def get_last_response(self) -> Optional[requests.Response]:
        """Return the last HTTP response."""
        return self.last_response


# ===== TableauDashboard =====

@dataclass
class TableauDashboard:
    """Orchestrates rendering of all panels to Tableau."""

    panels: List[DashboardPanel] = field(default_factory=list)
    renderer: Optional[TableauRenderer] = None
    ticker: Optional[DashboardTicker] = None

    def __post_init__(self) -> None:
        if not self.panels:
            self.panels = [
                WinRatePanel(),
                BankrollCurvePanel(),
                NashEquilibriumPanel(),
            ]

    def update(self) -> None:
        """Update all panels from the ticker."""
        if self.ticker is None:
            return
        for panel in self.panels:
            panel.update(self.ticker)

    def render(self) -> Any:
        """Render all panels to Tableau."""
        if self.renderer is None:
            return None
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

    def bind_ticker(self, ticker: DashboardTicker) -> None:
        """Bind a ticker to this dashboard."""
        self.ticker = ticker
        for panel in self.panels:
            panel.bind_ticker(ticker)

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
