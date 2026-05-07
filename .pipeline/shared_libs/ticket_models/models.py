"""Core data models for the SupportAgent Workflow Builder."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TicketSource(str, Enum):
    """Source channel of the ticket."""
    JSON = "json"
    EMAIL = "email"
    WEB = "web"


class Urgency(str, Enum):
    """Urgency level of a ticket."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    """Current status of a ticket in the pipeline."""
    NEW = "new"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    DRAFTED = "drafted"
    ESCALATED = "escalated"
    CLOSED = "closed"


# ---------------------------------------------------------------------------
# Ticket model
# ---------------------------------------------------------------------------

@dataclass
class Ticket:
    """Unified ticket representation.

    All fields are populated during the pipeline; fields that are not yet
    determined (e.g. category, urgency) default to None / sentinel values.
    """

    ticket_id: str
    source: TicketSource
    subject: str
    body: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Pipeline outputs (populated downstream)
    category: Optional[str] = None
    urgency: Optional[Urgency] = None
    sentiment: Optional[str] = None
    priority_score: Optional[int] = None
    assigned_team: Optional[str] = None
    draft_response: Optional[str] = None
    status: TicketStatus = TicketStatus.NEW

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dict (non-serialised enums become strings)."""
        d = asdict(self)
        # Enum → str
        d["source"] = self.source.value
        d["status"] = self.status.value
        if self.urgency is not None:
            d["urgency"] = self.urgency.value
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        """Deserialize from a plain dict."""
        # Convert string enums back
        source = data.get("source", "json")
        if isinstance(source, str):
            source = TicketSource(source)
        status = data.get("status", "new")
        if isinstance(status, str):
            status = TicketStatus(status)
        urgency = data.get("urgency")
        if isinstance(urgency, str):
            urgency = Urgency(urgency)
        return cls(
            ticket_id=data["ticket_id"],
            source=source,
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            category=data.get("category"),
            urgency=urgency,
            sentiment=data.get("sentiment"),
            priority_score=data.get("priority_score"),
            assigned_team=data.get("assigned_team"),
            draft_response=data.get("draft_response"),
            status=status,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Ticket":
        """Deserialize from a JSON string."""
        return cls.from_dict(json.loads(json_str))


# ---------------------------------------------------------------------------
# PipelineResult model
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Structured output returned by the pipeline / API."""

    ticket_id: str
    category: str
    urgency: str
    priority_score: int
    assigned_team: str
    draft_response: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineResult":
        return cls(
            ticket_id=data["ticket_id"],
            category=data["category"],
            urgency=data["urgency"],
            priority_score=data["priority_score"],
            assigned_team=data["assigned_team"],
            draft_response=data["draft_response"],
            status=data["status"],
        )

    @classmethod
    def from_ticket(cls, ticket: Ticket) -> "PipelineResult":
        """Build a PipelineResult from a fully-processed Ticket."""
        return cls(
            ticket_id=ticket.ticket_id,
            category=ticket.category or "general",
            urgency=ticket.urgency.value if ticket.urgency else "low",
            priority_score=ticket.priority_score or 1,
            assigned_team=ticket.assigned_team or "general_inbox",
            draft_response=ticket.draft_response or "",
            status=ticket.status.value,
        )
