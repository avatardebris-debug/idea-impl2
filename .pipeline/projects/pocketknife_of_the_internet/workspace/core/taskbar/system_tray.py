"""SystemTray class for notifications, status indicators, and clock display."""

from __future__ import annotations

import time


_DEFAULT_ITEMS = [
    {"id": "clock", "name": "Clock", "icon": "🕒", "tooltip": "", "type": "clock"},
    {"id": "volume", "name": "Volume", "icon": "🔊", "tooltip": "", "type": "volume", "volume": 50},
    {"id": "network", "name": "Network", "icon": "📶", "tooltip": "", "type": "network", "connected": True, "signal_strength": 100},
]


class SystemTray:
    """System tray with status indicators and clock.

    Properties:
        items: List of tray item dicts.
        clock: Current clock state dict.
        volume: Current volume state dict.
        network: Current network state dict.
    """

    def __init__(self) -> None:
        """Initialize the SystemTray with default items."""
        self._items: dict[str, dict] = {}
        for item in _DEFAULT_ITEMS:
            self._items[item["id"]] = item.copy()
        self._clock_state: dict = {"time": ""}
        self._volume_state: dict = {"volume": 50}
        self._network_state: dict = {"connected": True, "signal_strength": 100}

    # ── item management ──

    @property
    def items(self) -> list[dict]:
        """Return all tray items (read-only view)."""
        return list(self._items.values())

    def add_item(
        self,
        item_id: str,
        name: str,
        icon: str,
        tooltip: str = "",
    ) -> None:
        """Add a custom tray item.

        Args:
            item_id: Unique identifier for the item.
            name: Display name.
            icon: Icon string/emoji.
            tooltip: Optional tooltip text.
        """
        self._items[item_id] = {
            "id": item_id,
            "name": name,
            "icon": icon,
            "tooltip": tooltip,
        }

    def remove_item(self, item_id: str) -> bool:
        """Remove a tray item.

        Args:
            item_id: Item to remove.

        Returns:
            True if removed, False if not found.
        """
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def get_item(self, item_id: str) -> dict | None:
        """Get a tray item by ID.

        Args:
            item_id: Item ID to look up.

        Returns:
            Item dict or None if not found.
        """
        return self._items.get(item_id)

    # ── status updates ──

    def update_clock(self) -> None:
        """Update the clock item with current time."""
        current_time = time.strftime("%H:%M:%S")
        self._clock_state["time"] = current_time
        if "clock" in self._items:
            self._items["clock"]["tooltip"] = current_time
            self._items["clock"]["time"] = current_time

    def update_volume(self, level: int) -> None:
        """Update volume level.

        Args:
            level: Volume level (0-100).
        """
        self._volume_state["volume"] = level
        if "volume" in self._items:
            self._items["volume"]["volume"] = level

    def update_network(self, connected: bool, signal_strength: int) -> None:
        """Update network status.

        Args:
            connected: Whether the network is connected.
            signal_strength: Signal strength percentage (0-100).
        """
        self._network_state["connected"] = connected
        self._network_state["signal_strength"] = signal_strength
        if "network" in self._items:
            self._items["network"]["connected"] = connected
            self._items["network"]["signal_strength"] = signal_strength

    # ── state accessors ──

    @property
    def clock(self) -> dict:
        """Return current clock state."""
        return self._clock_state

    @property
    def volume(self) -> dict:
        """Return current volume state."""
        return self._volume_state

    @property
    def network(self) -> dict:
        """Return current network state."""
        return self._network_state

    # ── serialization ──

    def to_dict(self) -> dict:
        """Serialize the SystemTray state.

        Returns:
            Dict with items, clock, volume, and network states.
        """
        return {
            "items": list(self._items.values()),
            "clock": self._clock_state,
            "volume": self._volume_state,
            "network": self._network_state,
        }

    @classmethod
    def from_dict(cls, state: dict) -> "SystemTray":
        """Deserialize a SystemTray from a dict.

        Args:
            state: Dict with items, clock, volume, and network states.

        Returns:
            New SystemTray instance.
        """
        tray = cls()
        tray._items = {item["id"]: item for item in state.get("items", [])}
        tray._clock_state = state.get("clock", {"time": ""})
        tray._volume_state = state.get("volume", {"volume": 50})
        tray._network_state = state.get("network", {"connected": True, "signal_strength": 100})
        return tray

    def __repr__(self) -> str:
        return f"SystemTray(items={len(self._items)})"
