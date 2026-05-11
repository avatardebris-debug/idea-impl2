"""Dashboard layout components for card-game simulation metrics.

Provides:
  - ``DashboardBoard`` – a container that holds panels and manages their
    layout (rows / columns) for rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.dashboard.panels import DashboardPanel


@dataclass
class DashboardBoard:
    """A logical board that arranges panels in a grid.

    Attributes:
        panels: List of panels to display on the board.
        rows: Number of rows in the grid layout.
        columns: Number of columns in the grid layout.
        title: Optional title for the board.
    """

    panels: List[DashboardPanel] = field(default_factory=list)
    rows: int = 1
    columns: int = 1
    title: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate that the grid dimensions match the number of panels."""
        if self.panels:
            total_cells = self.rows * self.columns
            if len(self.panels) > total_cells:
                raise ValueError(
                    f"Cannot fit {len(self.panels)} panels into a "
                    f"{self.rows}x{self.columns} grid ({total_cells} cells)."
                )

    def add_panel(self, panel: DashboardPanel) -> None:
        """Add a panel to the board."""
        self.panels.append(panel)

    def remove_panel(self, panel: DashboardPanel) -> None:
        """Remove a panel from the board."""
        if panel in self.panels:
            self.panels.remove(panel)

    def get_panel_at(self, row: int, col: int) -> Optional[DashboardPanel]:
        """Return the panel at the given grid position (0-indexed)."""
        index = row * self.columns + col
        if 0 <= index < len(self.panels):
            return self.panels[index]
        return None

    def get_grid_dimensions(self) -> Tuple[int, int]:
        """Return the grid dimensions as (rows, columns)."""
        return (self.rows, self.columns)

    def set_grid_dimensions(self, rows: int, columns: int) -> None:
        """Set the grid dimensions.

        Raises:
            ValueError: If the new grid cannot hold all current panels.
        """
        total_cells = rows * columns
        if len(self.panels) > total_cells:
            raise ValueError(
                f"Cannot fit {len(self.panels)} panels into a "
                f"{rows}x{columns} grid ({total_cells} cells)."
            )
        self.rows = rows
        self.columns = columns

    def get_layout_info(self) -> dict:
        """Return a dict describing the board layout."""
        return {
            "title": self.title,
            "rows": self.rows,
            "columns": self.columns,
            "panel_count": len(self.panels),
            "panels": [
                {"symbol": p.symbol, "type": type(p).__name__}
                for p in self.panels
            ],
        }

    def to_dict(self) -> dict:
        """Serialize the board to a dictionary."""
        return {
            "title": self.title,
            "rows": self.rows,
            "columns": self.columns,
            "panels": [p.to_dict() for p in self.panels],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DashboardBoard":
        """Deserialize a board from a dictionary."""
        panels_data = data.get("panels", [])
        panels = []
        for pd in panels_data:
            symbol = pd.get("symbol", "")
            if symbol == "WIN_RATE":
                from src.dashboard.panels import WinRatePanel
                panel = WinRatePanel.from_dict(pd)
            elif symbol == "BANKROLL_CURVE":
                from src.dashboard.panels import BankrollCurvePanel
                panel = BankrollCurvePanel.from_dict(pd)
            elif symbol == "NASH_DIST":
                from src.dashboard.panels import NashEquilibriumPanel
                panel = NashEquilibriumPanel.from_dict(pd)
            else:
                from src.dashboard.panels import DashboardPanel
                panel = DashboardPanel.from_dict(pd)
            panels.append(panel)
        return cls(
            title=data.get("title"),
            rows=data.get("rows", 1),
            columns=data.get("columns", 1),
            panels=panels,
        )
