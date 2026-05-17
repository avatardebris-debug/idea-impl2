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

    def __init__(self):
        self._ticker = None

    def bind_ticker(self, ticker: DashboardTicker):
        self._ticker = ticker

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
        self._csv_buffer = io.StringIO()

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
        return output.getvalue()

    def render_panel(self, panel: DashboardPanel) -> str:
        if isinstance(panel, WinRatePanel):
            return str(panel.gauge_value)
        elif isinstance(panel, BankrollCurvePanel):
            return str(panel.bankroll)
        elif isinstance(panel, NashEquilibriumPanel):
            return str(panel.distance)
        return ""


class TableauRESTRenderer(TableauRenderer):
    """Renders dashboard state via REST API."""

    def __init__(self, method: str = "POST", url: str = None):
        self.method = method
        self.url = url
        self.last_response = None

    def render(self, state: DashboardState) -> dict:
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                json=state.to_dict(),
            )
            self.last_response = response
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}

    def render_panel(self, panel: DashboardPanel) -> dict:
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                json=panel.render_data(),
            )
            self.last_response = response
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}


class TableauDashboard:
    """Manages Tableau renderers and panels."""

    def __init__(self):
        self._panels = []
        self._renderers = []
        self._ticker = None

    def add_panel(self, panel: DashboardPanel):
        self._panels.append(panel)

    def add_renderer(self, renderer: TableauRenderer):
        self._renderers.append(renderer)

    def bind_ticker(self, ticker: DashboardTicker):
        self._ticker = ticker
        for panel in self._panels:
            panel.bind_ticker(ticker)
        for renderer in self._renderers:
            renderer.bind_ticker(ticker)

    def update_panels(self):
        if not self._ticker:
            return
        for panel in self._panels:
            panel.update(self._ticker)

    def render(self, state: DashboardState) -> list:
        results = []
        for renderer in self._renderers:
            results.append(renderer.render(state))
        return results

    def render_panel(self, panel: DashboardPanel) -> list:
        results = []
        for renderer in self._renderers:
            results.append(renderer.render_panel(panel))
        return results

    def get_panel_data(self) -> dict:
        data = {}
        for panel in self._panels:
            data[type(panel).__name__] = panel.render_data()
        return data

    def get_visual_encodings(self) -> dict:
        encodings = {}
        for panel in self._panels:
            encodings[type(panel).__name__] = panel.get_visual_encoding()
        return encodings
