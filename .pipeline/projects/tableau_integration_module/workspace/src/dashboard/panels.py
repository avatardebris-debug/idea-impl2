"""Dashboard panels for visualizing dashboard metrics."""

import math
from typing import Any, Dict, List, Optional, Tuple

from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
)
from src.dashboard.tickers import DashboardTicker


class DashboardPanel:
    """Base class for dashboard panels."""

    symbol: str = ""

    def __init__(
        self,
        symbol: str = "",
        title: str = "",
        description: str = "",
        width: int = 10,
        height: int = 10,
        x: int = 0,
        y: int = 0,
    ):
        # Make DashboardPanel abstract by raising TypeError on direct instantiation
        if self.__class__ is DashboardPanel:
            raise TypeError("Cannot instantiate abstract class DashboardPanel directly")
        self.symbol = symbol if symbol else self.__class__.symbol
        self.title = title
        self.description = description
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self._ticker: Optional[DashboardTicker] = None

    def update(self, ticker: DashboardTicker) -> None:
        """Update the panel from a ticker. Subclasses override."""
        self._ticker = ticker

    def render_data(self) -> Dict[str, Any]:
        """Return panel data as a dict. Subclasses override."""
        data = {
            "symbol": self.symbol,
            "title": self.title,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "type": type(self).__name__,
        }
        if self._ticker is not None:
            data["ticker"] = self._ticker.to_dict()
        return data

    def get_visual_encoding(self) -> Dict[str, Any]:
        """Return visual encoding info. Subclasses override."""
        return {}

    def render(self, data: Any) -> str:
        """Render the panel as a string."""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the panel to a dictionary."""
        return {
            "symbol": self.symbol,
            "title": self.title,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "type": type(self).__name__,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardPanel":
        """Deserialize a panel from a dictionary."""
        panel = cls(
            symbol=data.get("symbol", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            width=data.get("width", 10),
            height=data.get("height", 10),
            x=data.get("x", 0),
            y=data.get("y", 0),
        )
        return panel

    def bind_ticker(self, ticker: DashboardTicker) -> None:
        """Bind a ticker to this panel."""
        self._ticker = ticker

    def update_from_bound_ticker(self) -> None:
        """Update the panel from its bound ticker."""
        if self._ticker is not None:
            self.update(self._ticker)


class WinRatePanel(DashboardPanel):
    """Panel for win rate metrics."""

    symbol = "WIN_RATE"

    def __init__(
        self,
        symbol: str = "",
        gauge_value: float = 0.0,
        confidence_interval: Tuple[float, float] = (0.0, 1.0),
        trend_arrow: str = "→",
        total_games: int = 0,
        wins: int = 0,
        losses: int = 0,
        title: str = "Win Rate",
        description: str = "Shows the win rate of the agent.",
        width: int = 10,
        height: int = 10,
        x: int = 0,
        y: int = 0,
    ):
        super().__init__(symbol=symbol, title=title, description=description, width=width, height=height, x=x, y=y)
        self.gauge_value = gauge_value
        self._prev_gauge_value = gauge_value
        self.confidence_interval = confidence_interval
        self.trend_arrow = trend_arrow
        self.total_games = total_games
        self.wins = wins
        self.losses = losses

    def update(self, ticker: DashboardTicker) -> None:
        """Update the panel from a ticker."""
        super().update(ticker)
        wr = ticker.current_win_rate
        # Clamp gauge value to [0, 1]
        self.gauge_value = max(0.0, min(1.0, wr.value))
        self.total_games = wr.total_games
        self.wins = wr.wins
        self.losses = wr.losses

        # Compute confidence interval (Wilson score interval)
        n = max(wr.total_games, 1)
        p = self.gauge_value
        z = 1.96  # 95% confidence
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denominator
        spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
        lo = max(0.0, center - spread)
        hi = min(1.0, center + spread)
        self.confidence_interval = (lo, hi)

        # Compute trend arrow by comparing against previous gauge_value
        if self.gauge_value > self._prev_gauge_value + 0.001:
            self.trend_arrow = "↑"
        elif self.gauge_value < self._prev_gauge_value - 0.001:
            self.trend_arrow = "↓"
        else:
            self.trend_arrow = "→"
        # Store current value for next comparison
        self._prev_gauge_value = self.gauge_value

    def render_data(self) -> Dict[str, Any]:
        """Return panel data as a dict."""
        data = super().render_data()
        data["value"] = self.gauge_value
        data["ci_lower"] = self.confidence_interval[0]
        data["ci_upper"] = self.confidence_interval[1]
        data["trend_arrow"] = self.trend_arrow
        data["total_games"] = self.total_games
        data["wins"] = self.wins
        data["losses"] = self.losses
        return data

    def get_visual_encoding(self) -> Dict[str, Any]:
        """Return visual encoding info."""
        # Color: green if >= 0.5, yellow if >= 0.4, red otherwise
        if self.gauge_value >= 0.5:
            color = "green"
        elif self.gauge_value >= 0.4:
            color = "yellow"
        else:
            color = "red"
        return {
            "type": "gauge",
            "color": color,
            "width": self.width,
            "height": self.height,
            "symbol": self.symbol,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WinRatePanel":
        """Deserialize a WinRatePanel from a dictionary."""
        return cls(
            symbol=data.get("symbol", cls.symbol),
            gauge_value=data.get("gauge_value", 0.0),
            confidence_interval=data.get("confidence_interval", (0.0, 1.0)),
            trend_arrow=data.get("trend_arrow", "→"),
            total_games=data.get("total_games", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            title=data.get("title", "Win Rate"),
            description=data.get("description", "Shows the win rate of the agent."),
            width=data.get("width", 10),
            height=data.get("height", 10),
            x=data.get("x", 0),
            y=data.get("y", 0),
        )


class BankrollCurvePanel(DashboardPanel):
    """Panel for bankroll curve metrics."""

    symbol = "BANKROLL_CURVE"

    def __init__(
        self,
        symbol: str = "",
        current_bankroll: float = 0.0,
        peak_bankroll: float = 0.0,
        drawdown: float = 0.0,
        sparkline: List[float] = None,
        profit_loss: float = 0.0,
        initial_bankroll: float = 1000.0,
        title: str = "Bankroll Curve",
        description: str = "Shows the bankroll curve of the agent.",
        width: int = 10,
        height: int = 10,
        x: int = 0,
        y: int = 0,
    ):
        super().__init__(symbol=symbol, title=title, description=description, width=width, height=height, x=x, y=y)
        self.current_bankroll = current_bankroll
        self.peak_bankroll = peak_bankroll
        self.drawdown = drawdown
        self.sparkline = sparkline or []
        self.profit_loss = profit_loss
        self.initial_bankroll = initial_bankroll

    def update(self, ticker: DashboardTicker) -> None:
        """Update the panel from a ticker."""
        super().update(ticker)
        bh = ticker.bankroll_history
        self.current_bankroll = bh.bankroll if bh.bankroll else (bh.history[-1] if bh.history else 0.0)
        self.peak_bankroll = bh.peak_bankroll
        self.drawdown = bh.drawdown
        self.sparkline = bh.history if bh.history else []
        self.profit_loss = self.current_bankroll - self.initial_bankroll

    def render_data(self) -> Dict[str, Any]:
        """Return panel data as a dict."""
        data = super().render_data()
        data["step"] = self.current_bankroll  # will be overridden by update_from_bound_ticker
        data["bankroll"] = self.current_bankroll
        data["peak_bankroll"] = self.peak_bankroll
        data["drawdown"] = self.drawdown
        data["history"] = self.sparkline
        data["profit_loss"] = self.profit_loss
        return data

    def get_visual_encoding(self) -> Dict[str, Any]:
        """Return visual encoding info."""
        # Color: green if profit_loss >= 0, yellow if >= -10, red otherwise
        if self.profit_loss >= 0:
            color = "green"
        elif self.profit_loss >= -10:
            color = "yellow"
        else:
            color = "red"
        return {
            "type": "sparkline",
            "color": color,
            "width": self.width,
            "height": self.height,
            "symbol": self.symbol,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BankrollCurvePanel":
        """Deserialize a BankrollCurvePanel from a dictionary."""
        return cls(
            symbol=data.get("symbol", cls.symbol),
            current_bankroll=data.get("current_bankroll", 0.0),
            peak_bankroll=data.get("peak_bankroll", 0.0),
            drawdown=data.get("drawdown", 0.0),
            sparkline=data.get("sparkline", []),
            profit_loss=data.get("profit_loss", 0.0),
            initial_bankroll=data.get("initial_bankroll", 1000.0),
            title=data.get("title", "Bankroll Curve"),
            description=data.get("description", "Shows the bankroll curve of the agent."),
            width=data.get("width", 10),
            height=data.get("height", 10),
            x=data.get("x", 0),
            y=data.get("y", 0),
        )


class NashEquilibriumPanel(DashboardPanel):
    """Panel for Nash equilibrium metrics."""

    symbol = "NASH_DISTANCE"

    def __init__(
        self,
        symbol: str = "",
        distance: float = 0.0,
        current_strategy: str = "unknown",
        nash_strategy: str = "nash_equilibrium",
        heatmap_color: str = "white",
        title: str = "Nash Equilibrium Distance",
        description: str = "Shows the distance from the Nash Equilibrium.",
        width: int = 10,
        height: int = 10,
        x: int = 0,
        y: int = 0,
    ):
        super().__init__(symbol=symbol, title=title, description=description, width=width, height=height, x=x, y=y)
        self.distance = distance
        self.current_strategy = current_strategy
        self.nash_strategy = nash_strategy
        self.heatmap_color = heatmap_color

    def update(self, ticker: DashboardTicker) -> None:
        """Update the panel from a ticker."""
        super().update(ticker)
        nd = ticker.nash_distance
        self.distance = nd.distance
        self.current_strategy = nd.current_strategy
        self.nash_strategy = nd.nash_strategy

        # Compute heatmap color based on distance
        if self.distance < 0.05:
            self.heatmap_color = "green"
        elif self.distance < 0.15:
            self.heatmap_color = "yellow"
        else:
            self.heatmap_color = "red"

    def render_data(self) -> Dict[str, Any]:
        """Return panel data as a dict."""
        data = super().render_data()
        data["distance"] = self.distance
        data["current_strategy"] = self.current_strategy
        data["nash_strategy"] = self.nash_strategy
        data["heatmap_color"] = self.heatmap_color
        return data

    def get_visual_encoding(self) -> Dict[str, Any]:
        """Return visual encoding info."""
        # Color: green if distance < 0.05, yellow if < 0.15, red otherwise
        if self.distance < 0.05:
            color = "green"
        elif self.distance < 0.15:
            color = "yellow"
        else:
            color = "red"
        return {
            "type": "heatmap",
            "color": color,
            "width": self.width,
            "height": self.height,
            "symbol": self.symbol,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NashEquilibriumPanel":
        """Deserialize a NashEquilibriumPanel from a dictionary."""
        return cls(
            symbol=data.get("symbol", cls.symbol),
            distance=data.get("distance", 0.0),
            current_strategy=data.get("current_strategy", "unknown"),
            nash_strategy=data.get("nash_strategy", "nash_equilibrium"),
            heatmap_color=data.get("heatmap_color", "white"),
            title=data.get("title", "Nash Equilibrium Distance"),
            description=data.get("description", "Shows the distance to Nash equilibrium."),
            width=data.get("width", 10),
            height=data.get("height", 10),
            x=data.get("x", 0),
            y=data.get("y", 0),
        )
