"""Mirroring bridge — maps game actions/state changes to structured JSON events."""

import json
from typing import Any, Dict, List, Optional

from agentic_mirroring_game.core.events import GameEvent, EventLog
from agentic_mirroring_game.core.models import Resources, Territory, Building


class MirroringBridge:
    """Maps game actions and state changes to structured output events
    suitable for downstream integration (agentic commerce, robotics, etc.).
    """

    def __init__(
        self,
        player_name: str = "",
        turn: int = 0,
        empire_score: int = 0,
        resources: Optional[Dict[str, Any]] = None,
        territory: Optional[Dict[str, Any]] = None,
        buildings: Optional[List[Dict[str, Any]]] = None,
        production: Optional[Dict[str, int]] = None,
    ):
        self.player_name = player_name
        self._event_log = EventLog()
        self._enabled = True
        self.turn = turn
        self.empire_score = empire_score
        self.resources: Dict[str, Any] = resources or {}
        self.territory: Dict[str, Any] = territory or {}
        self.buildings: List[Dict[str, Any]] = buildings or []
        self.production: Dict[str, int] = production or {}

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def event_log(self) -> EventLog:
        return self._event_log

    def log_event(self, event_type: str, turn: int = 0, **data) -> GameEvent:
        """Capture a game state change as a structured event."""
        if not self._enabled:
            return GameEvent(event_type=event_type, turn=turn, data=data)

        event = GameEvent(
            event_type=event_type,
            turn=turn,
            data={
                "player_name": self.player_name,
                **data,
            },
        )
        self._event_log.add_event(event)
        return event

    def get_events(self) -> List[Dict[str, Any]]:
        """Retrieve the event log as a list of serializable dicts."""
        return self._event_log.get_events()

    def get_events_json(self) -> str:
        """Retrieve the event log as a JSON string."""
        return self._event_log.get_events_json()

    def get_events_for_action(self, action_name: str) -> List[Dict[str, Any]]:
        """Filter events by action name."""
        return [
            e for e in self.get_events()
            if e.get("data", {}).get("action") == action_name
        ]

    def get_state_events(self) -> List[Dict[str, Any]]:
        """Get only state-related events."""
        return [
            e for e in self.get_events()
            if e.get("event_type") in ("turn_complete", "game_start", "game_over")
        ]

    def clear_events(self) -> None:
        """Clear the event log."""
        self._event_log.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the bridge state."""
        return {
            "player_name": self.player_name,
            "turn": self.turn,
            "empire_score": self.empire_score,
            "resources": self.resources,
            "territory": self.territory,
            "buildings": self.buildings,
            "production": self.production,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MirroringBridge":
        """Deserialize the bridge state."""
        return cls(
            player_name=d.get("player_name", ""),
            turn=d.get("turn", 0),
            empire_score=d.get("empire_score", 0),
            resources=d.get("resources", {}),
            territory=d.get("territory", {}),
            buildings=d.get("buildings", []),
            production=d.get("production", {}),
        )

    def save_to_file(self, filepath: str) -> None:
        """Save the bridge state to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "MirroringBridge":
        """Load the bridge state from a JSON file."""
        with open(filepath, "r") as f:
            d = json.load(f)
        return cls.from_dict(d)

    def export_to_file(self, filepath: str) -> None:
        """Export event log to a JSON file."""
        with open(filepath, "w") as f:
            f.write(self.get_events_json())
