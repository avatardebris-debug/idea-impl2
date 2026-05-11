"""VR scene management for the stock ticker application."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.ticker import Ticker
from src.data_source import MockDataSource
from src.panels import TickerBoard, TickerPanel
from src.navigation import VRNavigator


@dataclass
class VRScene:
    """Manages the VR scene with tickers, boards, and data sources."""

    name: str = "VR Stock Ticker Scene"
    tickers: List[Ticker] = field(default_factory=list)
    boards: Dict[str, TickerBoard] = field(default_factory=dict)
    data_source: Optional[MockDataSource] = None
    navigator: Optional[VRNavigator] = None
    is_running: bool = False

    def add_ticker(self, ticker: Ticker) -> None:
        """Add a ticker to the scene."""
        self.tickers.append(ticker)
        # Update data source if available
        if self.data_source:
            self.data_source.add_ticker(ticker.symbol, ticker.price, ticker.name)

    def remove_ticker(self, symbol: str) -> bool:
        """Remove a ticker from the scene."""
        for i, ticker in enumerate(self.tickers):
            if ticker.symbol == symbol:
                self.tickers.pop(i)
                if self.data_source:
                    self.data_source.remove_ticker(symbol)
                return True
        return False

    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get a ticker by symbol."""
        for ticker in self.tickers:
            if ticker.symbol == symbol:
                return ticker
        return None

    def add_board(
        self,
        board: TickerBoard,
        position: Optional[Tuple[float, float, float]] = None,
        rotation: Optional[Tuple[float, float, float]] = None,
        size: Optional[Tuple[float, float, float]] = None,
    ) -> None:
        """Add a board to the scene."""
        if board.name not in self.boards:
            if position is not None:
                board.position = position
            if rotation is not None:
                board.rotation = rotation
            if size is not None:
                board.size = size
            self.boards[board.name] = board

    def remove_board(self, name: str) -> bool:
        """Remove a board from the scene."""
        if name in self.boards:
            del self.boards[name]
            return True
        return False

    def get_board(self, name: str) -> Optional[TickerBoard]:
        """Get a board by name."""
        return self.boards.get(name)

    def get_all_boards(self) -> List[TickerBoard]:
        """Get all boards in the scene."""
        return list(self.boards.values())

    def get_all_ticker_symbols(self) -> List[str]:
        """Get all ticker symbols in the scene."""
        return [t.symbol for t in self.tickers]

    def get_all_board_names(self) -> List[str]:
        """Get all board names in the scene."""
        return list(self.boards.keys())

    def get_navigator(self) -> Optional[VRNavigator]:
        """Get the navigator for the scene."""
        return self.navigator

    def set_data_source(self, data_source: MockDataSource) -> None:
        """Set the data source for the scene."""
        self.data_source = data_source
        # Add all tickers to the data source
        for ticker in self.tickers:
            data_source.add_ticker(ticker.symbol, ticker.price, ticker.name)

    def set_navigator(self, navigator: VRNavigator) -> None:
        """Set the navigator for the scene."""
        self.navigator = navigator

    def start(self) -> None:
        """Start the scene."""
        self.is_running = True
        if self.data_source:
            self.data_source.start()

    def stop(self) -> None:
        """Stop the scene."""
        self.is_running = False
        if self.data_source:
            self.data_source.stop()

    def update_tickers(self) -> None:
        """Update all tickers from the data source."""
        if self.data_source:
            updated_tickers = self.data_source.force_update()
            for ticker in updated_tickers:
                # Update in scene tickers
                for i, scene_ticker in enumerate(self.tickers):
                    if scene_ticker.symbol == ticker.symbol:
                        self.tickers[i] = ticker
                        break
                # Update in boards
                for board in self.boards.values():
                    board.update_panel(ticker.symbol, ticker)
            # Sync all data source tickers back to scene tickers
            for ds_ticker in self.data_source.get_tickers():
                found = False
                for i, scene_ticker in enumerate(self.tickers):
                    if scene_ticker.symbol == ds_ticker.symbol:
                        self.tickers[i] = ds_ticker
                        found = True
                        break
                if not found:
                    self.tickers.append(ds_ticker)

    def get_status(self) -> Dict:
        """Get scene status."""
        return {
            "name": self.name,
            "ticker_count": len(self.tickers),
            "board_count": len(self.boards),
            "is_running": self.is_running,
            "data_source_status": self.data_source.get_status() if self.data_source else None,
        }

    def to_dict(self) -> Dict:
        """Convert scene to dictionary."""
        return {
            "name": self.name,
            "tickers": [t.to_dict() for t in self.tickers],
            "boards": [board.to_dict() for board in self.boards.values()],
            "is_running": self.is_running,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> VRScene:
        """Create a scene from dictionary."""
        scene = cls(name=data.get("name", "VR Stock Ticker Scene"))
        for ticker_data in data.get("tickers", []):
            scene.add_ticker(Ticker.from_dict(ticker_data))
        for board_data in data.get("boards", []):
            scene.add_board(TickerBoard.from_dict(board_data))
        scene.is_running = data.get("is_running", False)
        return scene

    def __eq__(self, other: object) -> bool:
        """Check equality between two scenes."""
        if not isinstance(other, VRScene):
            return NotImplemented
        return (
            self.name == other.name
            and self.tickers == other.tickers
            and self.boards == other.boards
            and self.is_running == other.is_running
        )
