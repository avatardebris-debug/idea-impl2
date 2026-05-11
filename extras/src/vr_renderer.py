"""VR renderer for the stock ticker application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.ticker import Ticker
from src.panels import TickerPanel, TickerBoard
from src.vr_scene import VRScene


@dataclass
class VRRenderer:
    """Handles rendering of the VR scene."""

    scene: Optional[VRScene] = None
    is_rendering: bool = False
    frame_rate: float = 60.0
    resolution: tuple = (1920, 1080)

    def set_scene(self, scene: VRScene) -> None:
        """Set the scene to render."""
        self.scene = scene

    def start_rendering(self) -> None:
        """Start rendering the scene."""
        self.is_rendering = True

    def stop_rendering(self) -> None:
        """Stop rendering the scene."""
        self.is_rendering = False

    def render_ticker(self, ticker: Ticker) -> Dict:
        """Render a single ticker to a dictionary representation."""
        return {
            "symbol": ticker.symbol,
            "name": ticker.name,
            "price": ticker.price,
            "change": ticker.change,
            "change_percent": ticker.change_percent,
            "color": ticker.price_color,
            "background_color": ticker.background_color,
        }

    def render_panel(self, panel: TickerPanel) -> Dict:
        """Render a ticker panel to a dictionary representation."""
        return {
            "ticker": self.render_ticker(panel.ticker),
            "position": list(panel.position),
            "size": list(panel.size),
            "rotation": list(panel.rotation),
            "color": list(panel.color),
            "background_color": list(panel.background_color),
            "text_color": list(panel.text_color),
            "is_selected": panel.is_selected,
            "is_highlighted": panel.is_highlighted,
        }

    def render_board(self, board: TickerBoard) -> Dict:
        """Render a ticker board to a dictionary representation."""
        return {
            "name": board.name,
            "position": list(board.position),
            "rotation": list(board.rotation),
            "size": list(board.size),
            "panels": [self.render_panel(panel) for panel in board.panels],
        }

    def render_scene(self) -> Dict:
        """Render the entire scene to a dictionary representation."""
        if not self.scene:
            return {}

        return {
            "name": self.scene.name,
            "tickers": [self.render_ticker(t) for t in self.scene.tickers],
            "boards": {name: self.render_board(board) for name, board in self.scene.boards.items()},
            "is_rendering": self.is_rendering,
            "frame_rate": self.frame_rate,
            "resolution": list(self.resolution),
        }

    def get_render_status(self) -> Dict:
        """Get the current rendering status."""
        return {
            "is_rendering": self.is_rendering,
            "frame_rate": self.frame_rate,
            "resolution": list(self.resolution),
            "scene_name": self.scene.name if self.scene else None,
            "ticker_count": len(self.scene.tickers) if self.scene else 0,
            "board_count": len(self.scene.boards) if self.scene else 0,
        }
