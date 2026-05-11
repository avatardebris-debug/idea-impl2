"""Mock data source for simulating stock ticker updates."""

from __future__ import annotations

import random
import threading
import time
from typing import Dict, List, Optional

from src.ticker import Ticker


class MockDataSource:
    """Simulates a data source that provides ticker updates."""

    def __init__(
        self,
        update_interval: float = 1.0,
        volatility: float = 0.01,
        tickers: Optional[Dict[str, float]] = None,
    ):
        """Initialize mock data source.

        Args:
            update_interval: Seconds between updates.
            volatility: Maximum price change percentage per update.
            tickers: Initial ticker configurations {symbol: price}.
        """
        self.update_interval = update_interval
        self.volatility = volatility
        self._tickers: Dict[str, Ticker] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        if tickers:
            for symbol, price in tickers.items():
                self.add_ticker(symbol, price)

    def add_ticker(self, symbol: str, price: float = 0.0, name: str = "") -> None:
        """Add a ticker to the data source."""
        with self._lock:
            if symbol not in self._tickers:
                self._tickers[symbol] = Ticker(
                    symbol=symbol,
                    name=name or symbol,
                    price=price,
                    open_price=price,
                    previous_close=price,
                )

    def remove_ticker(self, symbol: str) -> bool:
        """Remove a ticker from the data source."""
        with self._lock:
            if symbol in self._tickers:
                del self._tickers[symbol]
                return True
            return False

    def get_tickers(self) -> List[Ticker]:
        """Get all tickers."""
        with self._lock:
            return list(self._tickers.values())

    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get a specific ticker."""
        with self._lock:
            return self._tickers.get(symbol)

    def start(self) -> None:
        """Start the data source update loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the data source."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def force_update(self) -> List[Ticker]:
        """Force an immediate update of all tickers (bypasses time throttling)."""
        updated = []
        with self._lock:
            for ticker in self._tickers.values():
                change_pct = random.uniform(-self.volatility, self.volatility)
                new_price = ticker.price * (1 + change_pct)
                ticker.update_price(new_price)
                updated.append(ticker)
        return updated

    def _update_loop(self) -> None:
        """Background update loop."""
        while self._running:
            self.force_update()
            time.sleep(self.update_interval)

    def get_status(self) -> Dict:
        """Get data source status."""
        return {
            "running": self._running,
            "ticker_count": len(self._tickers),
            "update_interval": self.update_interval,
            "volatility": self.volatility,
        }
