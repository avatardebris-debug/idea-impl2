"""Client Profile domain model for the FreelanceTask Manager System."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class ClientProfile:
    """
    Represents a client's profile data.

    Captures name, email, preferences, and interaction history.
    """
    name: str
    email: str
    company: str = ""
    industry: str = ""
    budget_range: dict[str, float] = field(default_factory=lambda: {"min": 0, "max": 100000})
    preferences: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    # ---- Validation ----

    @staticmethod
    def validate(data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if "name" not in data or not isinstance(data["name"], str) or not data["name"].strip():
            errors.append("'name' is required and must be a non-empty string")
        if "email" not in data or not isinstance(data["email"], str) or not data["email"].strip():
            errors.append("'email' is required and must be a non-empty string")
        elif "@" not in data["email"]:
            errors.append("'email' must contain '@'")
        return errors

    def validate_self(self) -> list[str]:
        data = asdict(self)
        return self.validate(data)

    # ---- Serialization ----

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClientProfile:
        return cls(
            name=data["name"],
            email=data["email"],
            company=data.get("company", ""),
            industry=data.get("industry", ""),
            budget_range=data.get("budget_range", {"min": 0, "max": 100000}),
            preferences=data.get("preferences", {}),
            history=data.get("history", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> ClientProfile:
        return cls.from_dict(json.loads(json_str))

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow().isoformat()

    def add_history_entry(self, entry: dict[str, Any]) -> None:
        self.history.append(entry)
        self.updated_at = datetime.utcnow().isoformat()
