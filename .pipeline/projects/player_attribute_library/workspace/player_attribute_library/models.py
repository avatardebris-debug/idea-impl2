"""Data model for player attributes."""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

DEFAULT_ATTRIBUTES: Dict[str, int] = {
    "speed": 0,
    "shooting": 0,
    "passing": 0,
    "defending": 0,
    "physical": 0,
    "mental": 0,
}

MIN_VALUE: int = 0
MAX_VALUE: int = 100

__all__ = [
    "DEFAULT_ATTRIBUTES",
    "MIN_VALUE",
    "MAX_VALUE",
    "PlayerAttribute",
]


def _clamp(value: float, lo: int = MIN_VALUE, hi: int = MAX_VALUE) -> float:
    """Clamp a numeric value to [lo, hi]."""
    if value < lo:
        return float(lo)
    if value > hi:
        return float(hi)
    return float(value)


@dataclass
class PlayerAttribute:
    """Represents a football player's attribute profile.

    Each attribute is clamped to the 0–100 range on assignment.

    Attributes
    ----------
    name : str
        Player name (required).
    speed : float
        Pace / speed rating.
    shooting : float
        Shooting ability rating.
    passing : float
        Passing accuracy / vision rating.
    defending : float
        Defensive capability rating.
    physical : float
        Physical strength / stamina rating.
    mental : float
        Mental / tactical awareness rating.
    """

    name: str
    speed: float = 0.0
    shooting: float = 0.0
    passing: float = 0.0
    defending: float = 0.0
    physical: float = 0.0
    mental: float = 0.0

    def __post_init__(self) -> None:
        """Validate and clamp all numeric attributes."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Player name must be a non-empty string.")
        self.name = self.name.strip()

        for attr_name in DEFAULT_ATTRIBUTES:
            raw = getattr(self, attr_name)
            if not isinstance(raw, (int, float)):
                raise TypeError(
                    f"Attribute '{attr_name}' must be a number, got {type(raw).__name__}"
                )
            setattr(self, attr_name, _clamp(raw))

    # ------------------------------------------------------------------
    # Attribute access helpers
    # ------------------------------------------------------------------

    def get(self, attr_name: str) -> float:
        """Return the value of *attr_name*, or raise KeyError."""
        if attr_name not in DEFAULT_ATTRIBUTES:
            raise KeyError(
                f"Unknown attribute '{attr_name}'. "
                f"Valid: {list(DEFAULT_ATTRIBUTES)}"
            )
        return getattr(self, attr_name)

    def set(self, attr_name: str, value: float) -> None:
        """Set *attr_name* to *value* (clamped to 0–100)."""
        if attr_name not in DEFAULT_ATTRIBUTES:
            raise KeyError(
                f"Unknown attribute '{attr_name}'. "
                f"Valid: {list(DEFAULT_ATTRIBUTES)}"
            )
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Attribute value must be a number, got {type(value).__name__}"
            )
        setattr(self, attr_name, _clamp(value))

    def to_dict(self) -> Dict[str, float]:
        """Return a dictionary of all attributes."""
        return {k: getattr(self, k) for k in DEFAULT_ATTRIBUTES}

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "PlayerAttribute":
        """Create a PlayerAttribute from a dict of attribute values."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Player name must be a non-empty string.")
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")
        kwargs: Dict[str, object] = {"name": name}
        for k, v in data.items():
            if k in DEFAULT_ATTRIBUTES:
                if not isinstance(v, (int, float)):
                    raise TypeError(
                        f"Attribute '{k}' must be a number, got {type(v).__name__}"
                    )
                kwargs[k] = v
        return cls(**kwargs)

    def to_json(self) -> str:
        """Serialize the player to a JSON string."""
        data: Dict[str, object] = {"name": self.name}
        data.update(self.to_dict())
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "PlayerAttribute":
        """Deserialize a PlayerAttribute from a JSON string."""
        if not isinstance(json_str, str):
            raise TypeError("json_str must be a string")
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise TypeError("JSON root must be an object")
        if "name" not in data:
            raise ValueError("JSON data must contain 'name'")
        return cls.from_dict(data["name"], data)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={getattr(self, k):.1f}" for k in DEFAULT_ATTRIBUTES)
        return f"PlayerAttribute(name={self.name!r}, {attrs})"
