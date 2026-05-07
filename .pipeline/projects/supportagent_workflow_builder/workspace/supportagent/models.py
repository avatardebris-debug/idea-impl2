"""Core data models for the SupportAgent workflow builder."""

from __future__ import annotations

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
    status: str = "open"
    workflow_state: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


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


@dataclass
class Workflow:
    """A complete SOP workflow."""
    name: str
    version: str = "1.0"
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


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
