"""Ticker display system — renders stock tickers as 3D panels in VR."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from src.ticker import Ticker


@dataclass
class TickerPanel:
    """A 3D panel displaying a single ticker."""

    ticker: Ticker
    position: tuple = (0.0, 0.0, 0.0)
    size: tuple = (1.0, 0.6, 0.05)
    rotation: tuple = (0.0, 0.0, 0.0)
    is_selected: bool = False
    is_highlighted: bool = False
    _color: Optional[tuple] = None
    _background_color: Optional[tuple] = None
    _text_color: Optional[tuple] = None

    def __init__(
        self,
        ticker: Ticker,
        position: tuple = (0.0, 0.0, 0.0),
        size: tuple = (1.0, 0.6, 0.05),
        rotation: tuple = (0.0, 0.0, 0.0),
        is_selected: bool = False,
        is_highlighted: bool = False,
        color: Optional[tuple] = None,
        background_color: Optional[tuple] = None,
        text_color: Optional[tuple] = None,
    ) -> None:
        """Initialize a ticker panel.

        Args:
            ticker: The ticker to display.
            position: 3D position (x, y, z).
            size: Panel dimensions (width, height, depth).
            rotation: Rotation in degrees (x, y, z).
            is_selected: Whether the panel is selected.
            is_highlighted: Whether the panel is highlighted.
            color: Custom display color (overrides ticker-based color).
            background_color: Custom background color.
            text_color: Custom text color.
        """
        self.ticker = ticker
        self.position = position
        self.size = size
        self.rotation = rotation
        self.is_selected = is_selected
        self.is_highlighted = is_highlighted
        self._color = color
        self._background_color = background_color
        self._text_color = text_color

    @property
    def color(self) -> tuple:
        """Get the display color for this panel."""
        if self._color is not None:
            return self._color
        if self.ticker.change > 0:
            return (0.0, 1.0, 0.0)  # Green
        elif self.ticker.change < 0:
            return (1.0, 0.0, 0.0)  # Red
        else:
            return (1.0, 1.0, 1.0)  # White

    @color.setter
    def color(self, value: Optional[tuple]) -> None:
        self._color = value

    @property
    def background_color(self) -> tuple:
        """Get the background color for this panel."""
        if self._background_color is not None:
            return self._background_color
        if self.ticker.change > 0:
            return (0.0, 0.5, 0.0)  # Dark green
        elif self.ticker.change < 0:
            return (0.5, 0.0, 0.0)  # Dark red
        else:
            return (0.2, 0.2, 0.2)  # Gray

    @background_color.setter
    def background_color(self, value: Optional[tuple]) -> None:
        self._background_color = value

    @property
    def text_color(self) -> tuple:
        """Get the text color for this panel."""
        if self._text_color is not None:
            return self._text_color
        return (1.0, 1.0, 1.0)  # White

    @text_color.setter
    def text_color(self, value: Optional[tuple]) -> None:
        self._text_color = value

    def select(self) -> None:
        """Select this panel."""
        self.is_selected = True
        self.is_highlighted = True

    def deselect(self) -> None:
        """Deselect this panel."""
        self.is_selected = False
        self.is_highlighted = False

    def toggle(self) -> None:
        """Toggle selection state."""
        if self.is_selected:
            self.deselect()
        else:
            self.select()

    def highlight(self) -> None:
        """Highlight this panel."""
        self.is_highlighted = True

    def unhighlight(self) -> None:
        """Unhighlight this panel."""
        self.is_highlighted = False

    def update_ticker(self, new_ticker: Ticker) -> None:
        """Update this panel with a new ticker."""
        self.ticker = new_ticker
        # Reset custom colors when ticker changes
        self._color = None
        self._background_color = None
        self._text_color = None

    def to_dict(self) -> dict:
        """Convert panel to dictionary."""
        return {
            "ticker": self.ticker.to_dict(),
            "position": list(self.position),
            "size": list(self.size),
            "rotation": list(self.rotation),
            "is_selected": self.is_selected,
            "is_highlighted": self.is_highlighted,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TickerPanel:
        """Create a panel from a dictionary."""
        return cls(
            ticker=Ticker.from_dict(data["ticker"]),
            position=tuple(data["position"]),
            size=tuple(data["size"]),
            rotation=tuple(data["rotation"]),
            is_selected=data["is_selected"],
            is_highlighted=data["is_highlighted"],
        )

    def __repr__(self) -> str:
        return (
            f"TickerPanel({self.ticker.symbol}: ${self.ticker.price:.2f} "
            f"at {self.position})"
        )


@dataclass
class TickerBoard:
    """A board containing multiple ticker panels."""

    name: str = "Board 1"
    position: tuple = (0.0, 1.6, 0.0)
    size: tuple = (10.0, 6.0, 0.05)
    rotation: tuple = (0.0, 0.0, 0.0)
    panels: List[TickerPanel] = field(default_factory=list)

    def add_panel(self, panel: TickerPanel) -> None:
        """Add a panel to this board."""
        self.panels.append(panel)

    def remove_panel(self, symbol: str) -> bool:
        """Remove a panel by ticker symbol."""
        for i, panel in enumerate(self.panels):
            if panel.ticker.symbol == symbol:
                self.panels.pop(i)
                return True
        return False

    def get_panel(self, symbol: str) -> Optional[TickerPanel]:
        """Get a panel by ticker symbol."""
        for panel in self.panels:
            if panel.ticker.symbol == symbol:
                return panel
        return None

    def update_panel(self, symbol: str, new_ticker: Ticker) -> bool:
        """Update a panel with a new ticker."""
        panel = self.get_panel(symbol)
        if panel:
            panel.update_ticker(new_ticker)
            return True
        return False

    def get_all_ticker_symbols(self) -> List[str]:
        """Get all ticker symbols on this board."""
        return [panel.ticker.symbol for panel in self.panels]

    def get_panel_at_position(self, position: tuple) -> Optional[TickerPanel]:
        """Get the panel at a specific position."""
        for panel in self.panels:
            if panel.position == position:
                return panel
        return None

    def get_selected_panel(self) -> Optional[TickerPanel]:
        """Get the currently selected panel."""
        for panel in self.panels:
            if panel.is_selected:
                return panel
        return None

    def clear_panels(self) -> None:
        """Remove all panels from this board."""
        self.panels.clear()

    def to_dict(self) -> dict:
        """Convert board to dictionary."""
        return {
            "name": self.name,
            "position": list(self.position),
            "size": list(self.size),
            "rotation": list(self.rotation),
            "panels": [panel.to_dict() for panel in self.panels],
        }

    @classmethod
    def from_dict(cls, data: dict) -> TickerBoard:
        """Create a board from a dictionary."""
        return cls(
            name=data["name"],
            position=tuple(data["position"]),
            size=tuple(data["size"]),
            rotation=tuple(data["rotation"]),
            panels=[TickerPanel.from_dict(p) for p in data["panels"]],
        )

    def __repr__(self) -> str:
        return (
            f"TickerBoard({self.name}: {len(self.panels)} panels, "
            f"size={self.size})"
        )
