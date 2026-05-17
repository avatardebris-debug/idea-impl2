"""SignalCollector — accepts, validates, and stores preference signals."""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from .signals import Signal, SignalValidationError


class SignalCollector:
    """Collects and manages preference signals from various tools.

    Stores signals in memory, deduplicates identical signals, and supports
    retrieval by user, tool, or item.
    """

    def __init__(self) -> None:
        self._signals: List[Signal] = []
        self._seen: Set[tuple] = set()  # dedup key: (user_id, tool_id, item_id, signal_type, value)

    def add_signal(
        self,
        user_id: str,
        tool_id: str,
        item_id: str,
        signal_type: str = "explicit_rating",
        value: float = 1.0,
        weight: float = 1.0,
        timestamp: Optional[str] = None,
    ) -> Signal:
        """Add a new preference signal.

        Args:
            user_id: User identifier.
            tool_id: Tool identifier.
            item_id: Item identifier.
            signal_type: Type of signal.
            value: Signal value.
            weight: Signal weight.
            timestamp: Optional ISO-format timestamp string.

        Returns:
            The created Signal object.

        Raises:
            SignalValidationError: If the signal fails validation.
        """
        signal = Signal(
            user_id=user_id,
            tool_id=tool_id,
            item_id=item_id,
            signal_type=signal_type,
            value=value,
            weight=weight,
        )
        if timestamp:
            from datetime import datetime, timezone
            signal.timestamp = datetime.fromisoformat(timestamp)

        dedup_key = (signal.user_id, signal.tool_id, signal.item_id, signal.signal_type, signal.value)
        if dedup_key not in self._seen:
            self._seen.add(dedup_key)
            self._signals.append(signal)

        return signal

    def add_signals(self, signals: List[Signal]) -> int:
        """Add multiple signals, deduplicating as we go.

        Args:
            signals: List of Signal objects to add.

        Returns:
            Number of new (non-duplicate) signals added.
        """
        count = 0
        for s in signals:
            dedup_key = (s.user_id, s.tool_id, s.item_id, s.signal_type, s.value)
            if dedup_key not in self._seen:
                self.add_signal(
                    user_id=s.user_id,
                    tool_id=s.tool_id,
                    item_id=s.item_id,
                    signal_type=s.signal_type,
                    value=s.value,
                    weight=s.weight,
                    timestamp=s.timestamp.isoformat() if s.timestamp else None,
                )
                count += 1
        return count

    def get_signals(self, user_id: Optional[str] = None, tool_id: Optional[str] = None, item_id: Optional[str] = None) -> List[Signal]:
        """Retrieve stored signals with optional filters.

        Args:
            user_id: Filter by user.
            tool_id: Filter by tool.
            item_id: Filter by item.

        Returns:
            List of matching Signal objects.
        """
        result = self._signals
        if user_id is not None:
            result = [s for s in result if s.user_id == user_id]
        if tool_id is not None:
            result = [s for s in result if s.tool_id == tool_id]
        if item_id is not None:
            result = [s for s in result if s.item_id == item_id]
        return result

    def get_signal_count(self) -> int:
        """Return the total number of stored signals."""
        return len(self._signals)

    def clear(self) -> None:
        """Remove all stored signals."""
        self._signals.clear()
        self._seen.clear()

    def get_signals_by_user(self, user_id: str) -> List[Signal]:
        """Get all signals for a specific user."""
        return self.get_signals(user_id=user_id)

    def get_signals_by_item(self, item_id: str) -> List[Signal]:
        """Get all signals for a specific item."""
        return self.get_signals(item_id=item_id)

    def get_signals_by_tool(self, tool_id: str) -> List[Signal]:
        """Get all signals from a specific tool."""
        return self.get_signals(tool_id=tool_id)
