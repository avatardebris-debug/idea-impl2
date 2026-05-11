"""Ticker display components — panels and boards for rendering tickers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.ticker import Ticker


@dataclass
class TickerPanel:
    """Represents a panel displaying a single ticker."""

    ticker: Ticker
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: Tuple[float, float, float] = (1.0, 0.6, 0.05)
    color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    background_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    text_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    is_selected: bool = False
    is_highlighted: bool = False

    def __post_init__(self):
        """Set default colors from ticker."""
        if self.color == (0.0, 0.0, 0.0):
            self.color = self.ticker.price_color
        if self.background_color == (0.0, 0.0, 0.0):
            self.background_color = self.ticker.background_color
        if self.text_color == (0.0, 0.0, 0.0):
            self.text_color = (1.0, 1.0, 1.0)

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
        """Update the panel with a new ticker."""
        self.ticker = new_ticker
        self.color = new_ticker.price_color
        self.background_color = new_ticker.background_color

    def to_dict(self) -> Dict:
        """Convert panel to dictionary."""
        return {
            "ticker": self.ticker.to_dict(),
            "position": list(self.position),
            "size": list(self.size),
            "rotation": list(self.rotation),
            "color": list(self.color),
            "background_color": list(self.background_color),
            "text_color": list(self.text_color),
            "is_selected": self.is_selected,
            "is_highlighted": self.is_highlighted,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> TickerPanel:
        """Create a panel from dictionary."""
        ticker = Ticker.from_dict(data["ticker"])
        return cls(
            ticker=ticker,
            position=tuple(data["position"]),
            size=tuple(data["size"]),
            rotation=tuple(data["rotation"]),
            color=tuple(data["color"]) if "color" in data else (0.0, 0.0, 0.0),
            background_color=tuple(data["background_color"]) if "background_color" in data else (0.0, 0.0, 0.0),
            text_color=tuple(data["text_color"]) if "text_color" in data else (0.0, 0.0, 0.0),
            is_selected=data.get("is_selected", False),
            is_highlighted=data.get("is_highlighted", False),
        )

    def __eq__(self, other: object) -> bool:
        """Check equality between two panels."""
        if not isinstance(other, TickerPanel):
            return NotImplemented
        return (
            self.ticker == other.ticker
            and self.position == other.position
            and self.size == other.size
            and self.rotation == other.rotation
            and self.color == other.color
            and self.background_color == other.background_color
            and self.text_color == other.text_color
            and self.is_selected == other.is_selected
            and self.is_highlighted == other.is_highlighted
        )


@dataclass
class TickerBoard:
    """A board containing multiple ticker panels."""

    name: str = "Board 1"
    position: Tuple[float, float, float] = (0.0, 1.6, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: Tuple[float, float, float] = (10.0, 6.0, 0.05)
    panels: List[TickerPanel] = field(default_factory=list)

    def add_panel(self, panel: TickerPanel) -> None:
        """Add a panel to the board."""
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
        """Update a panel's ticker."""
        panel = self.get_panel(symbol)
        if panel:
            panel.update_ticker(new_ticker)
            return True
        return False

    def get_all_ticker_symbols(self) -> List[str]:
        """Get all ticker symbols on the board."""
        return [panel.ticker.symbol for panel in self.panels]

    def get_panel_at_position(self, position: Tuple[float, float, float]) -> Optional[TickerPanel]:
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
        """Remove all panels from the board."""
        self.panels.clear()

    def to_dict(self) -> Dict:
        """Convert board to dictionary."""
        return {
            "name": self.name,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "size": list(self.size),
            "panels": [panel.to_dict() for panel in self.panels],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> TickerBoard:
        """Create a board from dictionary."""
        panels_data = data.get("panels", [])
        panels = [TickerPanel.from_dict(p) for p in panels_data]
        return cls(
            name=data.get("name", "Board 1"),
            position=tuple(data.get("position", [0.0, 1.6, 0.0])),
            rotation=tuple(data.get("rotation", [0.0, 0.0, 0.0])),
            size=tuple(data.get("size", [10.0, 6.0, 0.05])),
            panels=panels,
        )

    def __eq__(self, other: object) -> bool:
        """Check equality between two boards."""
        if not isinstance(other, TickerBoard):
            return NotImplemented
        return (
            self.name == other.name
            and self.position == other.position
            and self.rotation == other.rotation
            and self.size == other.size
            and len(self.panels) == len(other.panels)
            and all(p == op for p, op in zip(self.panels, other.panels))
        )
