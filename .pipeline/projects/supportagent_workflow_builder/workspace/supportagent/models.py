"""Core data models for the SupportAgent workflow builder."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TicketSource(Enum):
    """Source of an incoming ticket."""
    EMAIL = "email"
    JSON = "json"
    WEB = "web"
    API = "api"


class Urgency(Enum):
    """Ticket urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(Enum):
    """Ticket lifecycle status."""
    NEW = "new"
    ROUTED = "routed"
    IN_PROGRESS = "in_progress"
    AWAITING_CUSTOMER = "awaiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Priority(Enum):
    """Calculated priority levels."""
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


class TicketCategory(Enum):
    """Classified ticket categories."""
    URGENT = "urgent"
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    GENERAL = "general"


class WorkflowStepType(Enum):
    """Types of workflow steps."""
    ACTION = "action"
    CONDITION = "condition"
    GATE = "gate"


class WorkflowAction(Enum):
    """Available workflow actions."""
    CLASSIFY_TICKET = "classify_ticket"
    ASSIGN_TEAM = "assign_team"
    ESCALATE = "escalate"
    GENERATE_DRAFT = "generate_draft"
    SEND_RESPONSE = "send_response"
    NOTIFY = "notify"


class GateType(Enum):
    """Types of approval gates."""
    HUMAN_APPROVAL = "human_approval"
    HUMAN_REVIEW = "human_review"
    IMMEDIATE_RESPONSE = "immediate_response"


@dataclass
class Ticket:
    """Represents a support ticket."""
    ticket_id: str
    source: TicketSource
    subject: str
    body: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    category: Optional[TicketCategory] = None
    priority_score: float = 0.0
    urgency: Optional[Urgency] = None
    priority: Optional[Priority] = None
    assigned_team: Optional[str] = None
    sentiment: Optional[str] = None
    draft_response: Optional[str] = None
    status: TicketStatus = field(default_factory=lambda: TicketStatus.NEW)
    workflow_state: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        # Convert string status to TicketStatus enum if needed
        if isinstance(self.status, str):
            self.status = TicketStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ticket to a dict."""
        return {
            "ticket_id": self.ticket_id,
            "source": self.source.value if isinstance(self.source, TicketSource) else self.source,
            "subject": self.subject,
            "body": self.body,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "category": self.category.value if isinstance(self.category, TicketCategory) else self.category,
            "priority_score": self.priority_score,
            "urgency": self.urgency.value if isinstance(self.urgency, Urgency) else self.urgency,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "assigned_team": self.assigned_team,
            "sentiment": self.sentiment,
            "draft_response": self.draft_response,
            "status": self.status.value if isinstance(self.status, TicketStatus) else self.status,
            "workflow_state": self.workflow_state,
        }

    def to_json(self) -> str:
        """Serialize ticket to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Ticket":
        """Deserialize a ticket from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        """Deserialize a ticket from a dict."""
        # Convert string enums to enum values
        source = data.get("source", "json")
        if isinstance(source, str):
            source = TicketSource(source)
        
        category = data.get("category")
        if isinstance(category, str):
            category = TicketCategory(category)
        
        urgency = data.get("urgency")
        if isinstance(urgency, str):
            urgency = Urgency(urgency)
        
        priority = data.get("priority")
        if isinstance(priority, str):
            priority = Priority(priority)
        
        status = data.get("status", "new")
        if isinstance(status, str):
            status = TicketStatus(status)
        
        return cls(
            ticket_id=data["ticket_id"],
            source=source,
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            category=category,
            priority_score=data.get("priority_score", 0.0),
            urgency=urgency,
            priority=priority,
            assigned_team=data.get("assigned_team"),
            sentiment=data.get("sentiment"),
            draft_response=data.get("draft_response"),
            status=status,
            workflow_state=data.get("workflow_state", {}),
        )


@dataclass
class PipelineResult:
    """Result of the full ticket processing pipeline."""
    ticket_id: str
    category: str = "general"
    urgency: str = "low"
    priority_score: float = 1
    assigned_team: str = "general_inbox"
    draft_response: str = ""
    status: str = "new"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "ticket_id": self.ticket_id,
            "category": self.category,
            "urgency": self.urgency,
            "priority_score": self.priority_score,
            "assigned_team": self.assigned_team,
            "draft_response": self.draft_response,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineResult":
        """Deserialize from dict."""
        return cls(
            ticket_id=data["ticket_id"],
            category=data.get("category", "general"),
            urgency=data.get("urgency", "low"),
            priority_score=data.get("priority_score", 1),
            assigned_team=data.get("assigned_team", "general_inbox"),
            draft_response=data.get("draft_response", ""),
            status=data.get("status", "new"),
        )

    @classmethod
    def from_ticket(cls, ticket: Ticket) -> "PipelineResult":
        """Create a PipelineResult from a Ticket."""
        return cls(
            ticket_id=ticket.ticket_id,
            category=ticket.category or "general",
            urgency=ticket.urgency.value if ticket.urgency else "low",
            priority_score=ticket.priority_score or 1,
            assigned_team=ticket.assigned_team or "general_inbox",
            draft_response=ticket.draft_response or "",
            status=ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status,
        )


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str
    step_type: WorkflowStepType
    action: Optional[WorkflowAction] = None
    condition: Optional[Dict[str, Any]] = None
    gate_type: Optional[GateType] = None
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    then_step: Optional[str] = None
    else_step: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        step_type_str = data.get("type", "action")
        try:
            step_type = WorkflowStepType(step_type_str)
        except ValueError:
            step_type = WorkflowStepType.ACTION

        action_str = data.get("action")
        try:
            action = WorkflowAction(action_str) if action_str else None
        except ValueError:
            action = None

        gate_str = data.get("gate_type") or data.get("params", {}).get("gate_type")
        gate_type = GateType(gate_str) if gate_str else None

        return cls(
            id=data["id"],
            step_type=step_type,
            action=action,
            condition=data.get("condition"),
            gate_type=gate_type,
            params=data.get("params", {}),
            description=data.get("description", ""),
            then_step=data.get("then"),
            else_step=data.get("else")
        )


@dataclass
class Workflow:
    """A complete SOP workflow."""
    name: str
    version: str = "1.0"
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        steps_data = data.get("steps", [])
        steps = [WorkflowStep.from_dict(s) for s in steps_data]
        return cls(
            name=data["name"],
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            steps=steps,
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "Workflow":
        import yaml
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


@dataclass
class WorkflowExecution:
    """Tracks the execution state of a workflow."""
    workflow: Workflow
    ticket: Ticket
    current_step_id: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    is_complete: bool = False


@dataclass
class TriageResult:
    """Result of ticket triage analysis."""
    ticket: Ticket
    category: TicketCategory
    priority_score: float
    urgency: Urgency
    priority: Priority
    sentiment: str
    confidence: float = 0.0


@dataclass
class RoutingResult:
    """Result of ticket routing."""
    ticket: Ticket
    assigned_team: str
    team_label: str
    sla_hours: float
    escalation_required: bool = False
    escalation_reason: Optional[str] = None


@dataclass
class DraftResponse:
    """A generated draft response."""
    ticket: Ticket
    content: str
    tone: str
    template_used: str
    team: str
    metadata: Dict[str, Any] = field(default_factory=dict)
