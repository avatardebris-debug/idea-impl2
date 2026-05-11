"""MockDataSource base class for generating periodic metric updates.

Provides a threading-based data source that periodically calls an
_update() method and notifies registered callbacks with the latest data.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional


class MockDataSource:
    """Base class for a periodic metric data source.

    Subclasses should implement ``_generate_update()`` to produce
    the next data payload.  The base class runs an update loop on a
    background thread and notifies registered callbacks.

    Attributes:
        interval: Seconds between updates (configurable).
        running: Whether the background thread is active.
        callbacks: List of callables invoked on each update.
    """

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.running = False
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback to be called on each update."""
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a previously registered callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def start(self) -> None:
        """Start the background update loop."""
        if self.running:
            return
        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background update loop."""
        self.running = False
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval + 1)

    def force_update(self) -> Dict[str, Any]:
        """Trigger an immediate update and return the payload."""
        payload = self._generate_update()
        self._notify(payload)
        return payload

    # ---- Subclass hook ----

    def _generate_update(self) -> Dict[str, Any]:
        """Generate a single metric update payload.

        Override in subclasses to return the actual data dict.
        """
        return {"type": "mock", "data": {}}

    # ---- Internal ----

    def _run_loop(self) -> None:
        """Background loop that calls _generate_update periodically."""
        while self.running and not self._stop_event.is_set():
            payload = self._generate_update()
            self._notify(payload)
            self._stop_event.wait(timeout=self.interval)

    def _notify(self, payload: Dict[str, Any]) -> None:
        """Invoke all registered callbacks with the payload."""
        with self._lock:
            for cb in list(self.callbacks):
                try:
                    cb(payload)
                except Exception:
                    pass  # swallow callback errors
