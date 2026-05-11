"""Opportunity domain models for the FreelanceTask Manager System."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any


class OpportunityStage(str, Enum):
    """Stages in the opportunity lifecycle."""
    NEW = "new"
    MATCHED = "matched"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


@dataclass
class Opportunity:
    """Represents a potential business opportunity."""

    opportunity_id: str
    client_name: str
    client_email: str
    service_title: str
    stage: OpportunityStage = OpportunityStage.NEW
    score: float = 0.0
    proposal_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        d = asdict(self)
        d["stage"] = self.stage.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Opportunity:
        """Deserialize from dictionary."""
        data = dict(data)
        stage = data.pop("stage", "new")
        if isinstance(stage, str):
            data["stage"] = OpportunityStage(stage)
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> Opportunity:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def update_stage(self, new_stage: OpportunityStage) -> None:
        """Transition to a new stage."""
        self.stage = new_stage
        self.updated_at = datetime.now().isoformat()


@dataclass
class OpportunityPipeline:
    """Tracks the full pipeline of opportunities."""

    pipeline_id: str
    name: str
    opportunities: list[Opportunity] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_opportunity(self, opp: Opportunity) -> None:
        """Add an opportunity to the pipeline."""
        self.opportunities.append(opp)
        self.updated_at = datetime.now().isoformat()

    def get_by_id(self, opp_id: str) -> Opportunity | None:
        """Find an opportunity by ID."""
        for opp in self.opportunities:
            if opp.opportunity_id == opp_id:
                return opp
        return None

    def get_by_stage(self, stage: OpportunityStage) -> list[Opportunity]:
        """Get all opportunities in a given stage."""
        return [opp for opp in self.opportunities if opp.stage == stage]

    def get_won_opportunities(self) -> list[Opportunity]:
        """Get all won opportunities."""
        return self.get_by_stage(OpportunityStage.WON)

    def get_lost_opportunities(self) -> list[Opportunity]:
        """Get all lost opportunities."""
        return self.get_by_stage(OpportunityStage.LOST)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "opportunities": [opp.to_dict() for opp in self.opportunities],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpportunityPipeline:
        """Deserialize from dictionary."""
        data = dict(data)
        opps = data.pop("opportunities", [])
        opportunities = [Opportunity.from_dict(o) for o in opps]
        return cls(**data, opportunities=opportunities)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> OpportunityPipeline:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @staticmethod
    def create_pipeline(name: str) -> OpportunityPipeline:
        """Create a new pipeline."""
        return OpportunityPipeline(
            pipeline_id=f"PIPE-{uuid.uuid4().hex[:8].upper()}",
            name=name,
        )
