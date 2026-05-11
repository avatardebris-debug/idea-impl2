"""Tableau visualization helpers."""

import csv
import io
from abc import ABC, abstractmethod

import requests

from src.dashboard.panels import (
    DashboardPanel,
    WinRatePanel,
    BankrollCurvePanel,
    NashEquilibriumPanel,
)
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import DashboardState


class TableauRenderer(ABC):
    """Abstract base class for Tableau renderers."""

    @abstractmethod
    def render(self, state: DashboardState):
        pass

    @abstractmethod
    def render_panel(self, panel: DashboardPanel):
        pass


class TableauCSVRenderer(TableauRenderer):
    """Renders dashboard state as CSV."""

    def __init__(self, delimiter: str = ",", include_header: bool = True):
        self.delimiter = delimiter
        self.include_header = include_header
        self._csv_buffer = None

    def render(self, state: DashboardState) -> str:
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)
        if self.include_header:
            writer.writerow(["timestamp", "win_rate", "total_games", "wins", "losses",
                             "bankroll", "peak_bankroll", "drawdown", "nash_distance",
                             "current_strategy", "nash_strategy"])
        writer.writerow([
            state.timestamp,
            state.win_rate.value,
            state.win_rate.total_games,
            state.win_rate.wins,
            state.win_rate.losses,
            state.bankroll.bankroll,
            state.bankroll.peak_bankroll,
            state.bankroll.drawdown,
            state.nash_distance.distance,
            state.nash_distance.current_strategy,
            state.nash_distance.nash_strategy,
        ])
        self._csv_buffer = output.getvalue()
        return self._csv_buffer

    def render_panel(self, panel: DashboardPanel) -> str:
        if isinstance(panel, WinRatePanel):
            data = panel.render_data()
            return self._render_panel_data(data, ["gauge_value"])
        elif isinstance(panel, BankrollCurvePanel):
            data = panel.render_data()
            return self._render_panel_data(data, ["current_bankroll", "peak_bankroll", "drawdown"])
        elif isinstance(panel, NashEquilibriumPanel):
            data = panel.render_data()
            return self._render_panel_data(data, ["distance", "current_strategy", "nash_strategy"])
        return ""

    def _render_panel_data(self, data: dict, fields: list) -> str:
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)
        if self.include_header:
            writer.writerow(fields)
        writer.writerow([data.get(f, "") for f in fields])
        return output.getvalue()

    def get_csv_buffer(self) -> str:
        return self._csv_buffer


class TableauRESTRenderer(TableauRenderer):
    """Renders dashboard state via REST API."""

    def __init__(self, server_url: str = "", username: str = "", password: str = "",
                 site_id: str = "", content_url: str = "", timeout: int = 30):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.site_id = site_id
        self.content_url = content_url
        self.timeout = timeout
        self.last_response = None

    def render(self, state: DashboardState):
        try:
            payload = {
                "win_rate": state.win_rate.value,
                "total_games": state.win_rate.total_games,
                "wins": state.win_rate.wins,
                "losses": state.win_rate.losses,
                "bankroll": state.bankroll.bankroll,
                "peak_bankroll": state.bankroll.peak_bankroll,
                "drawdown": state.bankroll.drawdown,
                "nash_distance": state.nash_distance.distance,
                "current_strategy": state.nash_distance.current_strategy,
                "nash_strategy": state.nash_distance.nash_strategy,
                "timestamp": state.timestamp,
            }
            response = requests.post(
                self.server_url,
                json=payload,
                timeout=self.timeout,
            )
            self.last_response = response
            return response
        except Exception:
            self.last_response = None
            return None

    def render_panel(self, panel: DashboardPanel):
        try:
            panel_name = type(panel).__name__.upper()
            data = panel.render_data()
            payload = {
                "panel": panel_name,
                "data": data,
            }
            response = requests.post(
                self.server_url,
                json=payload,
                timeout=self.timeout,
            )
            self.last_response = response
            return response
        except Exception:
            self.last_response = None
            return None

    def get_last_response(self):
        return self.last_response


class TableauDashboard:
    """Orchestrates panels and renderers."""

    def __init__(self, panels: list = None, renderer: TableauRenderer = None):
        if panels is not None:
            self.panels = panels
        else:
            self.panels = [
                WinRatePanel(),
                BankrollCurvePanel(),
                NashEquilibriumPanel(),
            ]
        self.renderer = renderer
        self.ticker = None

    def bind_ticker(self, ticker: DashboardTicker):
        self.ticker = ticker
        for panel in self.panels:
            panel.bind_ticker(ticker)

    def update(self):
        if self.ticker is not None:
            for panel in self.panels:
                panel.update_from_bound_ticker()

    def render(self):
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

    def render_panel(self, panel: DashboardPanel):
        if self.renderer is None:
            return None
        return self.renderer.render_panel(panel)

    def render_all_panels(self):
        if self.renderer is None:
            return []
        return [self.renderer.render_panel(p) for p in self.panels]

    def add_panel(self, panel: DashboardPanel):
        self.panels.append(panel)
        if self.ticker is not None:
            panel.bind_ticker(self.ticker)

    def remove_panel(self, panel: DashboardPanel):
        self.panels.remove(panel)

    def get_panel_count(self) -> int:
        return len(self.panels)

    def get_panels_by_type(self, panel_type) -> list:
        return [p for p in self.panels if isinstance(p, panel_type)]
