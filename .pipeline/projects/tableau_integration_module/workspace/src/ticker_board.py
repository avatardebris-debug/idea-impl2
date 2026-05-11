"""TickerBoard: base class for arranging TickerPanels in a layout.

Provides a simple panel management system that can be extended by
DashboardBoard to add metric-specific panel types and VR rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TickerPanel:
    """Base panel that displays a ticker's value.

    Attributes:
        panel_id: Unique identifier for this panel.
        title: Display title for the panel.
        width: Panel width in layout units.
        height: Panel height in layout units.
        x: Horizontal position in the layout.
        y: Vertical position in the layout.
        ticker_data: Current ticker data dict.
    """

    panel_id: str = ""
    title: str = ""
    width: float = 1.0
    height: float = 1.0
    x: float = 0.0
    y: float = 0.0
    ticker_data: Dict[str, Any] = field(default_factory=dict)

    def update_from_ticker(self, ticker_data: Dict[str, Any]) -> None:
        """Update panel data from a ticker dict."""
        self.ticker_data = ticker_data

    def to_dict(self) -> Dict[str, Any]:
        """Serialize panel to a plain dict."""
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "ticker_data": self.ticker_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TickerPanel":
        """Deserialize a TickerPanel from a plain dict."""
        return cls(
            panel_id=data.get("panel_id", ""),
            title=data.get("title", ""),
            width=float(data.get("width", 1.0)),
            height=float(data.get("height", 1.0)),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            ticker_data=data.get("ticker_data", {}),
        )


class TickerBoard:
    """Manages a collection of TickerPanels in a layout.

    Attributes:
        panels: List of TickerPanel instances.
        layout_width: Total width of the board layout.
        layout_height: Total height of the board layout.
    """

    def __init__(
        self,
        layout_width: float = 10.0,
        layout_height: float = 10.0,
    ) -> None:
        self.panels: List[TickerPanel] = []
        self.layout_width = layout_width
        self.layout_height = layout_height

    def add_panel(self, panel: TickerPanel) -> None:
        """Add a panel to the board."""
        self.panels.append(panel)

    def remove_panel(self, panel_id: str) -> bool:
        """Remove a panel by ID. Returns True if found and removed."""
        for i, p in enumerate(self.panels):
            if p.panel_id == panel_id:
                self.panels.pop(i)
                return True
        return False

    def get_panel(self, panel_id: str) -> TickerPanel | None:
        """Get a panel by ID."""
        for p in self.panels:
            if p.panel_id == panel_id:
                return p
        return None

    def update_all_panels(self, ticker_data_map: Dict[str, Dict[str, Any]]) -> None:
        """Update all panels with their corresponding ticker data.

        Args:
            ticker_data_map: Mapping of panel_id -> ticker_data dict.
        """
        for panel in self.panels:
            if panel.panel_id in ticker_data_map:
                panel.update_from_ticker(ticker_data_map[panel.panel_id])

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the board to a plain dict."""
        return {
            "layout_width": self.layout_width,
            "layout_height": self.layout_height,
            "panels": [p.to_dict() for p in self.panels],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TickerBoard":
        """Deserialize a TickerBoard from a plain dict."""
        board = cls(
            layout_width=float(data.get("layout_width", 10.0)),
            layout_height=float(data.get("layout_height", 10.0)),
        )
        for p_data in data.get("panels", []):
            board.add_panel(TickerPanel.from_dict(p_data))
        return board
