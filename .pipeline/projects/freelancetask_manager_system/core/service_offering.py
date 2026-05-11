"""Core data models for the Freelance Task Manager System."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Milestone:
    """A milestone within a service offering timeline."""
    title: str
    description: str = ""
    deadline_days: int = 0
    deliverables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "deadline_days": self.deadline_days,
            "deliverables": list(self.deliverables),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Milestone:
        return cls(
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            deadline_days=data.get("deadline_days", 0),
            deliverables=data.get("deliverables", []),
        )

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access for test compatibility."""
        return getattr(self, key)


@dataclass
class PricingTier:
    """A pricing tier for a service offering."""
    name: str
    price: float
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "price": self.price,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PricingTier:
        return cls(
            name=data.get("name", "Unnamed"),
            price=float(data.get("price", 0)),
            description=data.get("description", ""),
        )


@dataclass
class ServiceOffering:
    """A standardized service offering (SOP) with pricing and timeline."""
    title: str
    description: str
    deliverables: list[str] = field(default_factory=list)
    timeline: dict[str, Any] = field(default_factory=lambda: {"total_days": 0, "milestones": []})
    pricing: list[PricingTier] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    version: str = "1.0"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceOffering:
        pricing_data = data.get("pricing", [])
        pricing = [PricingTier.from_dict(t) for t in pricing_data]

        timeline_data = data.get("timeline", {})
        if "milestones" in timeline_data:
            raw_milestones = timeline_data["milestones"]
            milestones = []
            for m in raw_milestones:
                if isinstance(m, dict):
                    milestones.append(Milestone.from_dict(m))
                elif isinstance(m, Milestone):
                    milestones.append(m)
            timeline_data = dict(timeline_data)
            timeline_data["milestones"] = milestones

        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            deliverables=data.get("deliverables", []),
            timeline=timeline_data,
            pricing=pricing,
            requirements=data.get("requirements", []),
            assumptions=data.get("assumptions", []),
            risks=data.get("risks", []),
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        timeline_data = dict(self.timeline)
        if "milestones" in timeline_data:
            timeline_data["milestones"] = [
                m.to_dict() if isinstance(m, Milestone) else m
                for m in timeline_data["milestones"]
            ]

        return {
            "title": self.title,
            "description": self.description,
            "deliverables": list(self.deliverables),
            "timeline": timeline_data,
            "pricing": [t.to_dict() for t in self.pricing],
            "requirements": list(self.requirements),
            "assumptions": list(self.assumptions),
            "risks": list(self.risks),
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def validate(data: dict[str, Any]) -> list[str]:
        """Validate SOP data. Returns list of error messages."""
        errors = []
        if not data.get("title"):
            errors.append("title is required")
        if not data.get("description"):
            errors.append("description is required")
        if not data.get("deliverables"):
            errors.append("deliverables is required")
        if not data.get("pricing"):
            errors.append("pricing is required")
        else:
            for i, tier in enumerate(data["pricing"]):
                if tier.get("price", 0) < 0:
                    errors.append(f"pricing[{i}].price must be non-negative")
        if not data.get("timeline"):
            errors.append("timeline is required")
        return errors

    def validate_self(self) -> list[str]:
        """Validate this offering."""
        return self.validate(self.to_dict())

    def update(self, **kwargs: Any) -> None:
        """Update fields and bump version."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow().isoformat()
        # Bump version: 1.0 -> 1.1, 1.1 -> 1.2, etc.
        parts = self.version.split(".")
        if len(parts) == 2:
            major, minor = parts
            self.version = f"{major}.{int(minor) + 1}"
        elif len(parts) == 3:
            major, minor, patch = parts
            self.version = f"{major}.{minor}.{int(patch) + 1}"

    def get_pricing_range(self) -> tuple[float, float]:
        """Return (min_price, max_price) tuple."""
        if not self.pricing:
            return (0.0, 0.0)
        prices = [t.price for t in self.pricing]
        return (min(prices), max(prices))


@dataclass
class ClientProfile:
    """A client profile with needs, budget, and preferences."""
    name: str
    email: str
    industry: str = ""
    company_size: str = ""
    budget_range: str = ""
    needs: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    decision_maker: str = ""
    timeline_preference: str = ""
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClientProfile:
        return cls(
            name=data.get("name", ""),
            email=data.get("email", ""),
            industry=data.get("industry", ""),
            company_size=data.get("company_size", ""),
            budget_range=data.get("budget_range", ""),
            needs=data.get("needs", []),
            pain_points=data.get("pain_points", []),
            goals=data.get("goals", []),
            decision_maker=data.get("decision_maker", ""),
            timeline_preference=data.get("timeline_preference", ""),
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "industry": self.industry,
            "company_size": self.company_size,
            "budget_range": self.budget_range,
            "needs": list(self.needs),
            "pain_points": list(self.pain_points),
            "goals": list(self.goals),
            "decision_maker": self.decision_maker,
            "timeline_preference": self.timeline_preference,
            "notes": self.notes,
        }

    @staticmethod
    def validate(data: dict[str, Any]) -> list[str]:
        """Validate client data. Returns list of error messages."""
        errors = []
        if not data.get("name"):
            errors.append("name is required")
        if not data.get("email"):
            errors.append("email is required")
        return errors

    def get_budget_range(self) -> tuple[float, float]:
        """Parse budget_range string like '$5000-$15000' into (min, max)."""
        if not self.budget_range:
            return (0.0, 0.0)
        match = re.search(r'\$(\d+)-\$(\d+)', self.budget_range)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        return (0.0, 0.0)
