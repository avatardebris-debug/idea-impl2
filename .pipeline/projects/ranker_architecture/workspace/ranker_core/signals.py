"""Signal data model and validation for the Ranker Architecture."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

VALID_SIGNAL_TYPES = Literal[
    "explicit_rating",
    "implicit_click",
    "implicit_view",
    "implicit_purchase",
    "implicit_like",
    "explicit_dislike",
    "explicit_rank",
]

VALID_SIGNAL_TYPE_VALUES = {
    "explicit_rating",
    "implicit_click",
    "implicit_view",
    "implicit_purchase",
    "implicit_like",
    "explicit_dislike",
    "explicit_rank",
}


class SignalValidationError(Exception):
    """Raised when a Signal fails validation."""


@dataclass
class Signal:
    """Represents a single preference signal.

    Attributes:
        user_id: Identifier for the user who generated the signal.
        tool_id: Identifier for the tool that produced the signal.
        item_id: Identifier for the item being rated/evaluated.
        timestamp: When the signal was generated.
        signal_type: Type of signal (explicit or implicit).
        value: Numeric value of the signal (e.g., rating 1-5, binary 0/1).
        weight: Importance weight for this signal (default 1.0).
        id: Unique identifier for this signal.
    """

    user_id: str
    tool_id: str
    item_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signal_type: str = "explicit_rating"
    value: float = 1.0
    weight: float = 1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate signal fields after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all fields. Raises SignalValidationError on failure."""
        errors: list[str] = []

        # Validate user_id
        if not self.user_id or not str(self.user_id).strip():
            errors.append("user_id is required and must be non-empty")

        # Validate tool_id
        if not self.tool_id or not str(self.tool_id).strip():
            errors.append("tool_id is required and must be non-empty")

        # Validate item_id
        if not self.item_id or not str(self.item_id).strip():
            errors.append("item_id is required and must be non-empty")

        # Validate signal_type
        if self.signal_type not in VALID_SIGNAL_TYPE_VALUES:
            errors.append(
                f"signal_type must be one of {sorted(VALID_SIGNAL_TYPE_VALUES)}, "
                f"got '{self.signal_type}'"
            )

        # Validate value range
        if self.signal_type == "explicit_rating" and not (1.0 <= self.value <= 5.0):
            errors.append("explicit_rating value must be between 1.0 and 5.0")
        elif self.signal_type == "explicit_dislike" and not (-5.0 <= self.value <= -1.0):
            errors.append("explicit_dislike value must be between -5.0 and -1.0")
        elif self.signal_type == "explicit_rank" and not (1.0 <= self.value <= 100.0):
            errors.append("explicit_rank value must be between 1.0 and 100.0")
        elif self.signal_type in ("implicit_click", "implicit_view", "implicit_purchase", "implicit_like"):
            if not (0.0 <= self.value <= 1.0):
                errors.append(f"implicit signal value must be between 0.0 and 1.0, got {self.value}")

        # Validate weight
        if self.weight <= 0.0:
            errors.append(f"weight must be positive, got {self.weight}")
        if self.weight > 10.0:
            errors.append(f"weight must be <= 10.0, got {self.weight}")

        if errors:
            raise SignalValidationError("; ".join(errors))

    def to_dict(self) -> dict:
        """Convert signal to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tool_id": self.tool_id,
            "item_id": self.item_id,
            "timestamp": self.timestamp.isoformat(),
            "signal_type": self.signal_type,
            "value": self.value,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Signal":
        """Create a Signal from a dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            user_id=data["user_id"],
            tool_id=data["tool_id"],
            item_id=data["item_id"],
            timestamp=timestamp,
            signal_type=data.get("signal_type", "explicit_rating"),
            value=data.get("value", 1.0),
            weight=data.get("weight", 1.0),
            id=data.get("id", str(uuid.uuid4())),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Signal):
            return NotImplemented
        return (
            self.user_id == other.user_id
            and self.tool_id == other.tool_id
            and self.item_id == other.item_id
            and self.signal_type == other.signal_type
            and self.value == other.value
        )

    def __hash__(self) -> int:
        return hash((self.user_id, self.tool_id, self.item_id, self.signal_type, self.value))
