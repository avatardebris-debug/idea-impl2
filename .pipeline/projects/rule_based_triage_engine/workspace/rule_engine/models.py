"""Data models for the rule-based triage engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Condition:
    """A single condition that can be evaluated against an email field."""

    field: str
    operator: str
    value: Any

    def evaluate(self, email_value: Any) -> bool:
        """Evaluate this condition against an email field value.

        Supported operators:
            contains, not_contains, equals, regex, is_empty, gt, lt
        """
        op = self.operator

        if op == "is_empty":
            return self._is_empty(email_value)

        if op == "gt":
            return self._gt(email_value)

        if op == "lt":
            return self._lt(email_value)

        # For string-based operators, coerce to string
        if email_value is None:
            email_str = ""
        else:
            email_str = str(email_value)

        if op == "contains":
            return self.value in email_str

        if op == "not_contains":
            return self.value not in email_str

        if op == "equals":
            return email_str == str(self.value)

        if op == "regex":
            return bool(re.search(str(self.value), email_str))

        raise ValueError(f"Unsupported operator: {op}")

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """Check if a value is considered empty."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, bool):
            return not value
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False

    def _gt(self, value: Any) -> bool:
        """Greater-than comparison."""
        try:
            return float(value) > float(self.value)
        except (TypeError, ValueError):
            return False

    def _lt(self, value: Any) -> bool:
        """Less-than comparison."""
        try:
            return float(value) < float(self.value)
        except (TypeError, ValueError):
            return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary for JSON storage."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Condition:
        """Deserialize from a dictionary loaded from JSON."""
        return cls(
            field=data["field"],
            operator=data["operator"],
            value=data["value"],
        )


@dataclass
class Action:
    """An action to apply when a rule matches."""

    type: str  # tag, route, archive, flag
    target: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary for JSON storage."""
        return {
            "type": self.type,
            "target": self.target,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Action:
        """Deserialize from a dictionary loaded from JSON."""
        return cls(
            type=data["type"],
            target=data["target"],
        )


@dataclass
class Rule:
    """A complete rule with conditions and actions."""

    id: str
    name: str
    conditions: list[Condition]
    actions: list[Action]
    priority: int = 0
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "priority": self.priority,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Deserialize from a dictionary loaded from JSON."""
        return cls(
            id=data["id"],
            name=data["name"],
            conditions=[Condition.from_dict(c) for c in data["conditions"]],
            actions=[Action.from_dict(a) for a in data["actions"]],
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
        )
