"""Event types and serialization for the mirroring bridge."""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class GameEvent:
    """A structured game event for mirroring bridge."""
    event_type: str
    timestamp: float = field(default_factory=time.time)
    turn: int = 0
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "turn": self.turn,
            "data": self.data,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GameEvent":
        return cls(
            event_type=d.get("event_type", "unknown"),
            timestamp=d.get("timestamp", time.time()),
            turn=d.get("turn", 0),
            data=d.get("data", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "GameEvent":
        return cls.from_dict(json.loads(json_str))


class EventLog:
    """Simple event log that stores and retrieves game events."""

    def __init__(self):
        self._events: List[GameEvent] = []

    def add_event(self, event: GameEvent) -> None:
        self._events.append(event)

    def get_events(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._events]

    def get_events_json(self) -> str:
        return json.dumps([e.to_dict() for e in self._events], indent=2)

    def clear(self) -> None:
        self._events.clear()

    @property
    def events(self) -> List[GameEvent]:
        return self._events

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events": [e.to_dict() for e in self._events],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EventLog":
        log = cls()
        for event_dict in d.get("events", []):
            log.add_event(GameEvent.from_dict(event_dict))
        return log

    def __len__(self) -> int:
        return len(self._events)

    def __getitem__(self, index: int) -> GameEvent:
        return self._events[index]
