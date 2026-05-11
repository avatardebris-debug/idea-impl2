"""DashboardBoard: extends TickerBoard with metric-specific panel types.

Provides a dashboard layout with dedicated panels for win rate, bankroll,
and Nash equilibrium metrics.  Supports VR rendering via DashboardVizRenderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.ticker_board import TickerBoard, TickerPanel


@dataclass
class DashboardBoard(TickerBoard):
    """Dashboard board with metric-specific panel types.

    Attributes:
        win_rate_panel: Panel for win rate metric.
        bankroll_panel: Panel for bankroll metric.
        nash_panel: Panel for Nash equilibrium metric.
        layout_width: Total width of the board layout.
        layout_height: Total height of the board layout.
    """

    win_rate_panel: Optional[TickerPanel] = None
    bankroll_panel: Optional[TickerPanel] = None
    nash_panel: Optional[TickerPanel] = None
    layout_width: float = 10.0
    layout_height: float = 10.0

    def __post_init__(self) -> None:
        """Initialize default panels if not provided."""
        if self.win_rate_panel is None:
            self.win_rate_panel = TickerPanel(
                panel_id="win_rate",
                title="Win Rate",
                width=3.0,
                height=2.0,
                x=0.0,
                y=0.0,
                ticker_data={},
            )
        if self.bankroll_panel is None:
            self.bankroll_panel = TickerPanel(
                panel_id="bankroll",
                title="Bankroll",
                width=3.0,
                height=2.0,
                x=3.0,
                y=0.0,
                ticker_data={},
            )
        if self.nash_panel is None:
            self.nash_panel = TickerPanel(
                panel_id="nash",
                title="Nash Equilibrium",
                width=4.0,
                height=2.0,
                x=6.0,
                y=0.0,
                ticker_data={},
            )
        # Add default panels to the board
        self.panels = [self.win_rate_panel, self.bankroll_panel, self.nash_panel]

    def add_win_rate_panel(self, panel: TickerPanel) -> None:
        """Add a custom win rate panel."""
        self.win_rate_panel = panel
        self.add_panel(panel)

    def add_bankroll_panel(self, panel: TickerPanel) -> None:
        """Add a custom bankroll panel."""
        self.bankroll_panel = panel
        self.add_panel(panel)

    def add_nash_panel(self, panel: TickerPanel) -> None:
        """Add a custom nash panel."""
        self.nash_panel = panel
        self.add_panel(panel)

    def get_panel_by_type(self, panel_type: str) -> Optional[TickerPanel]:
        """Get a panel by its type name.

        Args:
            panel_type: One of 'win_rate', 'bankroll', 'nash'.

        Returns:
            The corresponding panel, or None if not found.
        """
        if panel_type == "win_rate":
            return self.win_rate_panel
        elif panel_type == "bankroll":
            return self.bankroll_panel
        elif panel_type == "nash":
            return self.nash_panel
        return None

    def update_from_ticker(self, ticker_data: Dict[str, Any]) -> None:
        """Update all panels with ticker data.

        Args:
            ticker_data: Dict mapping panel_id -> ticker data dict.
        """
        for panel in self.panels:
            if panel.panel_id in ticker_data:
                panel.update_from_ticker(ticker_data[panel.panel_id])

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the dashboard board to a plain dict."""
        return {
            "layout_width": self.layout_width,
            "layout_height": self.layout_height,
            "win_rate_panel": self.win_rate_panel.to_dict() if self.win_rate_panel else None,
            "bankroll_panel": self.bankroll_panel.to_dict() if self.bankroll_panel else None,
            "nash_panel": self.nash_panel.to_dict() if self.nash_panel else None,
            "panels": [p.to_dict() for p in self.panels],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardBoard":
        """Deserialize a DashboardBoard from a plain dict."""
        board = cls(
            layout_width=float(data.get("layout_width", 10.0)),
            layout_height=float(data.get("layout_height", 10.0)),
        )
        # Deserialize individual panels
        wr_data = data.get("win_rate_panel")
        if wr_data:
            board.win_rate_panel = TickerPanel.from_dict(wr_data)
        br_data = data.get("bankroll_panel")
        if br_data:
            board.bankroll_panel = TickerPanel.from_dict(br_data)
        ns_data = data.get("nash_panel")
        if ns_data:
            board.nash_panel = TickerPanel.from_dict(ns_data)
        # Deserialize panels list
        for p_data in data.get("panels", []):
            board.add_panel(TickerPanel.from_dict(p_data))
        return board
