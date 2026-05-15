"""Service Offering domain model for the FreelanceTask Manager System."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class PricingTier:
    """A single pricing tier within a service offering."""
    name: str
    price: float
    description: str = ""
    features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PricingTier:
        return cls(**data)


@dataclass
class Milestone:
    """A milestone/deliverable within an SOP."""
    title: str
    description: str
    deadline_days: int  # days from project start
    deliverables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Milestone:
        return cls(**data)


@dataclass
class ServiceOffering:
    """
    Represents a drop-servicing service offering (SOP).

    Required fields enforced by validation:
      - title, description, deliverables, timeline, pricing
    """
    title: str
    description: str
    deliverables: list[str]
    timeline: dict[str, Any] = field(default_factory=dict)
    pricing: list[PricingTier] = field(default_factory=list)
    version: str = "1.0.0"
    features: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Alias so tests can use ServiceOffering.PricingTier
    PricingTier = PricingTier

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    # ---- Validation ----

    @staticmethod
    def validate(data: dict[str, Any]) -> list[str]:
        """Return a list of validation error messages (empty if valid)."""
        errors: list[str] = []

        required_fields = ["title", "description", "deliverables", "timeline", "pricing"]
        for f in required_fields:
            if f not in data or data[f] is None:
                errors.append(f"Missing required field: {f}")
            elif f == "deliverables" and (not isinstance(data[f], list) or len(data[f]) == 0):
                errors.append(f"Field '{f}' must be a non-empty list")
            elif f == "pricing" and (not isinstance(data[f], list) or len(data[f]) == 0):
                errors.append(f"Field '{f}' must be a non-empty list")
            elif f == "timeline" and not isinstance(data[f], dict):
                errors.append(f"Field '{f}' must be a dict")

        if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
            errors.append("'title' must be a non-empty string")

        if "pricing" in data and isinstance(data["pricing"], list):
            for i, tier in enumerate(data["pricing"]):
                if not isinstance(tier, dict):
                    errors.append(f"'pricing[{i}]' must be a dict")
                    continue
                if "name" not in tier:
                    errors.append(f"'pricing[{i}]' missing 'name'")
                if "price" not in tier:
                    errors.append(f"'pricing[{i}]' missing 'price'")
                elif not isinstance(tier["price"], (int, float)) or tier["price"] < 0:
                    errors.append(f"'pricing[{i}].price' must be a non-negative number")

        return errors

    def validate_self(self) -> list[str]:
        """Validate this instance and return error messages."""
        data = asdict(self)
        # Convert PricingTier objects to dicts for validation
        data["pricing"] = [t.to_dict() if hasattr(t, 'to_dict') else t for t in self.pricing]
        return self.validate(data)

    # ---- Serialization ----

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pricing"] = [t.to_dict() for t in self.pricing]
        if "milestones" in self.timeline:
            d["timeline"]["milestones"] = [
                m.to_dict() if hasattr(m, 'to_dict') else m
                for m in self.timeline["milestones"]
            ]
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceOffering:
        pricing = [PricingTier.from_dict(t) for t in data["pricing"]]
        timeline = data["timeline"]
        if "milestones" in timeline:
            timeline["milestones"] = [
                Milestone.from_dict(m) for m in timeline["milestones"]
            ]
        return cls(
            title=data["title"],
            description=data["description"],
            deliverables=data["deliverables"],
            timeline=timeline,
            pricing=pricing,
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> ServiceOffering:
        return cls.from_dict(json.loads(json_str))

    def update(self, **kwargs: Any) -> None:
        """Update fields and bump version + timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow().isoformat()
        # Bump patch version
        parts = self.version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
            self.version = ".".join(parts)
