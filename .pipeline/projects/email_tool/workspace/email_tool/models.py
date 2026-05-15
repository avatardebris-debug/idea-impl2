"""
Email Tool - Data Models

Core data structures for email processing rules, actions, and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from pathlib import Path


class RuleType(Enum):
    """Types of email matching rules."""
    SUBJECT_CONTAINS = "subject_contains"
    SUBJECT_EXACT = "subject_exact"
    SUBJECT_REGEX = "subject_regex"
    SUBJECT_PATTERN = "subject_pattern"
    FROM_CONTAINS = "from_contains"
    FROM_EXACT = "from_exact"
    FROM_PATTERN = "from_pattern"
    FROM_DOMAIN = "from_domain"
    TO_CONTAINS = "to_contains"
    TO_EXACT = "to_exact"
    BODY_CONTAINS = "body_contains"
    BODY_CONTAINS_EXACT = "body_contains_exact"
    BODY_CONTAINS_CONTAINS = "body_contains_contains"
    BODY_REGEX = "body_regex"
    BODY_CONTAINS_PATTERN = "body_contains_pattern"
    HAS_ATTACHMENT = "has_attachment"
    ATTACHMENT_NAME = "attachment_name"
    ATTACHMENT_TYPE = "attachment_type"
    DATE_AFTER = "date_after"
    DATE_BEFORE = "date_before"
    SIZE_LESS_THAN = "size_less_than"
    SIZE_GREATER_THAN = "size_greater_than"
    LABEL_EXISTS = "label_exists"
    LABEL_DOES_NOT_EXIST = "label_does_not_exist"
    ANY = "any"  # All conditions must match
    ANY_OF = "any_of"  # At least one condition must match
    NONE = "none"  # No conditions match


class ActionType(Enum):
    """Types of actions to perform on matched emails."""
    MOVE = "move"
    COPY = "copy"
    DELETE = "delete"
    ARCHIVE = "archive"
    MARK_READ = "mark_read"
    MARK_UNREAD = "mark_unread"
    ADD_LABEL = "add_label"
    REMOVE_LABEL = "remove_label"
    LABEL = "label"
    FORWARD = "forward"
    REPLY = "reply"
    SEND_NOTIFICATION = "send_notification"
    NOTIFY = "notify"
    EXPORT = "export"
    CONVERT = "convert"
    IGNORE = "ignore"  # Don't process further
    FILE = "file"  # Save email to file system
    MOVE_TO_CATEGORY = "move_to_category"  # Phase 6 alias


@dataclass
class Rule:
    """
    A rule for matching emails.
    
    Rules can have multiple conditions that must all match (AND logic)
    or at least one that must match (OR logic).
    """
    name: str
    rule_type: RuleType
    pattern: Optional[str] = None
    priority: int = 50
    category: str = "general"
    labels: List[str] = field(default_factory=list)
    description: str = ""
    enabled: bool = True
    id: Optional[str] = None
    
    def __post_init__(self):
        """Validate rule after initialization."""
        if self.priority < 0 or self.priority > 100:
            raise ValueError(f"Priority must be between 0 and 100, got {self.priority}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary for serialization."""
        return {
            "name": self.name,
            "rule_type": self.rule_type.value,
            "pattern": self.pattern,
            "priority": self.priority,
            "category": self.category,
            "labels": self.labels,
            "description": self.description,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create rule from dictionary."""
        return cls(
            name=data["name"],
            rule_type=RuleType(data["rule_type"]),
            pattern=data.get("pattern"),
            priority=data.get("priority", 50),
            category=data.get("category", "general"),
            labels=data.get("labels", []),
            description=data.get("description", ""),
            enabled=data.get("enabled", True)
        )


@dataclass
class Action:
    """
    An action to perform on matched emails.
    
    Actions are executed after a rule matches.
    """
    action_type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for serialization."""
        return {
            "action_type": self.action_type.value,
            "params": self.params,
            "description": self.description,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create action from dictionary."""
        return cls(
            action_type=ActionType(data["action_type"]),
            params=data.get("params", {}),
            description=data.get("description", ""),
            enabled=data.get("enabled", True)
        )


@dataclass
class EmailMatch:
    """Result of matching an email against rules."""
    email_file: str
    rule_name: str
    rule_priority: int
    match_type: str
    match_details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert match to dictionary."""
        return {
            "email_file": self.email_file,
            "rule_name": self.rule_name,
            "rule_priority": self.rule_priority,
            "match_type": self.match_type,
            "match_details": self.match_details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EmailProcessingResult:
    """Result of processing an email."""
    email_file: str
    success: bool
    matches: List[EmailMatch] = field(default_factory=list)
    actions_performed: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "email_file": self.email_file,
            "success": self.success,
            "matches": [m.to_dict() for m in self.matches],
            "actions_performed": self.actions_performed,
            "output_path": self.output_path,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EmailMetadata:
    """Metadata extracted from an email."""
    subject: str
    from_email: str
    from_name: str
    to_emails: List[str]
    cc_emails: List[str]
    bcc_emails: List[str]
    date: datetime
    message_id: str
    size_bytes: int
    has_attachments: bool
    attachment_names: List[str]
    labels: List[str]
    body_text: str = ""
    body_html: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "subject": self.subject,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "to_emails": self.to_emails,
            "cc_emails": self.cc_emails,
            "bcc_emails": self.bcc_emails,
            "date": self.date.isoformat(),
            "message_id": self.message_id,
            "size_bytes": self.size_bytes,
            "has_attachments": self.has_attachments,
            "attachment_names": self.attachment_names,
            "labels": self.labels,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "headers": self.headers
        }


@dataclass
class ProcessingStats:
    """Statistics about email processing."""
    total_emails: int = 0
    processed_emails: int = 0
    successful_emails: int = 0
    failed_emails: int = 0
    matched_emails: int = 0
    total_rules: int = 0
    total_actions: int = 0
    total_processing_time_ms: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert success_rate to fraction for Phase 6 compatibility."""
        success_rate = 0.0
        if self.processed_emails > 0:
            success_rate = self.successful_emails / self.processed_emails
        
        return {
            "total_emails": self.total_emails,
            "processed_emails": self.processed_emails,
            "successful_emails": self.successful_emails,
            "failed_emails": self.failed_emails,
            "matched_emails": self.matched_emails,
            "total_rules": self.total_rules,
            "total_actions": self.total_actions,
            "total_processing_time_ms": self.total_processing_time_ms,
            "success_rate": success_rate,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "errors_by_type": self.errors_by_type
        }
    
    def add_error(self, error_type: str):
        """Track an error by type."""
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1


@dataclass
class RuleSet:
    """A collection of rules."""
    name: str
    rules: List[Rule] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_rule(self, rule: Rule):
        """Add a rule to the set."""
        self.rules.append(rule)
        self.updated_at = datetime.now()
    
    def remove_rule(self, rule_or_name) -> bool:
        """Remove a rule by name or Rule object."""
        rule_name = rule_or_name.name if hasattr(rule_or_name, 'name') else rule_or_name
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """Get a rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def get_enabled_rules(self) -> List[Rule]:
        """Get all enabled rules, sorted by priority."""
        return sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule set to dictionary."""
        return {
            "name": self.name,
            "rules": [r.to_dict() for r in self.rules],
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleSet':
        """Create rule set from dictionary."""
        rules = [Rule.from_dict(r) for r in data.get("rules", [])]
        return cls(
            name=data["name"],
            rules=rules,
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        )


@dataclass
class ActionSet:
    """A collection of actions."""
    name: str
    actions: List[Action] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_action(self, action):
        """Add an action to the set. Accepts Action objects or plain ActionType enums."""
        self.actions.append(action)
        self.updated_at = datetime.now()
    
    def remove_action(self, action_type: ActionType) -> bool:
        """Remove an action by type."""
        for i, action in enumerate(self.actions):
            # Support both plain ActionType enums and Action objects
            act_type = action if isinstance(action, ActionType) else action.action_type
            if act_type == action_type:
                self.actions.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_action(self, action_type: ActionType) -> Optional[Action]:
        """Get an action by type."""
        for action in self.actions:
            act_type = action if isinstance(action, ActionType) else action.action_type
            if act_type == action_type:
                return action
        return None
    
    def get_enabled_actions(self) -> List[Action]:
        """Get all enabled actions."""
        return [a for a in self.actions if not isinstance(a, ActionType) and a.enabled]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action set to dictionary."""
        def _action_to_dict(a):
            if isinstance(a, ActionType):
                return a.value
            return a.to_dict()
        
        return {
            "name": self.name,
            "actions": [_action_to_dict(a) for a in self.actions],
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionSet':
        """Create action set from dictionary."""
        actions = [Action.from_dict(a) for a in data.get("actions", [])]
        return cls(
            name=data["name"],
            actions=actions,
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        )


@dataclass
class AttachmentProcessingResult:
    """Result of processing an attachment."""
    attachment_id: str = ""
    attachment_name: str = ""
    email_id: str = ""
    original_filename: str = ""
    content_type: str = ""
    size_bytes: int = 0
    attachment_type: Any = None
    processed_at: str = ""
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = False
    output_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "attachment_id": self.attachment_id,
            "attachment_name": self.attachment_name,
            "success": self.success,
            "output_path": self.output_path,
            "errors": self.errors,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ProcessingConfig:
    """Configuration for email processing."""
    base_path: str = "./archive"
    output_format: str = "eml"
    collision_strategy: str = "rename"
    path_template: str = "{{year}}/{{month}}/{{from_domain}}/{{subject_sanitized}}"
    dry_run: bool = False
    log_level: str = "INFO"
    max_file_size_mb: int = 25
    allowed_extensions: List[str] = field(default_factory=lambda: [".eml", ".msg", ".mbox"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "base_path": self.base_path,
            "output_format": self.output_format,
            "collision_strategy": self.collision_strategy,
            "path_template": self.path_template,
            "dry_run": self.dry_run,
            "log_level": self.log_level,
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_extensions": self.allowed_extensions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        """Create config from dictionary."""
        return cls(
            base_path=data.get("base_path", "./archive"),
            output_format=data.get("output_format", "eml"),
            collision_strategy=data.get("collision_strategy", "rename"),
            path_template=data.get("path_template", "{{year}}/{{month}}/{{from_domain}}/{{subject_sanitized}}"),
            dry_run=data.get("dry_run", False),
            log_level=data.get("log_level", "INFO"),
            max_file_size_mb=data.get("max_file_size_mb", 25),
            allowed_extensions=data.get("allowed_extensions", [".eml", ".msg", ".mbox"])
        )


# == Phase 6 Models ==

class RuleMatchStrategy(Enum):
    """Strategies for matching rules against emails."""
    FIRST_MATCH = "first_match"
    BEST_MATCH = "best_match"
    ALL_MATCH = "all_match"


class RuleMatchType(Enum):
    """Types of rule matching."""
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class Category(Enum):
    """Email categories."""
    INBOX = "inbox"
    SENT = "sent"
    DRAFTS = "drafts"
    ARCHIVE = "archive"
    SPAM = "spam"
    TRASH = "trash"
    CUSTOM = "custom"


@dataclass
class EmailAttachmentProcessingResult:
    """Result of processing an email attachment."""
    attachment_id: str = ""
    attachment_name: str = ""
    email_id: str = ""
    original_filename: str = ""
    content_type: str = ""
    size_bytes: int = 0
    attachment_type: Any = None
    processed_at: str = ""
    text_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = False
    output_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "attachment_id": self.attachment_id,
            "attachment_name": self.attachment_name,
            "success": self.success,
            "output_path": self.output_path,
            "errors": self.errors,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Email:
    """Represents an email message."""
    id: Optional[str] = None
    from_addr: str = ""
    to_addrs: List[str] = field(default_factory=list)
    subject: str = ""
    date: Optional[datetime] = None
    body_plain: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    raw_headers: Dict[str, str] = field(default_factory=dict)
    labels: List[str] = field(default_factory=list)
    source_path: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize created_at and id if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert email to dictionary."""
        return {
            "id": self.id,
            "from_addr": self.from_addr,
            "to_addrs": self.to_addrs,
            "subject": self.subject,
            "date": self.date.isoformat() if self.date else None,
            "body_plain": self.body_plain,
            "body_html": self.body_html,
            "attachments": self.attachments,
            "raw_headers": self.raw_headers,
            "labels": self.labels,
            "source_path": self.source_path,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Email':
        """Create Email from dictionary."""
        return cls(
            id=data.get("id"),
            from_addr=data.get("from_addr", ""),
            to_addrs=data.get("to_addrs", []),
            subject=data.get("subject", ""),
            date=datetime.fromisoformat(data["date"]) if data.get("date") else None,
            body_plain=data.get("body_plain"),
            body_html=data.get("body_html"),
            attachments=data.get("attachments", []),
            raw_headers=data.get("raw_headers", {}),
            labels=data.get("labels", []),
            source_path=data.get("source_path"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
    
    def to_eml(self) -> str:
        """Convert email to EML format string."""
        lines = [
            f"From: {self.from_addr}",
            f"To: {', '.join(self.to_addrs)}",
            f"Subject: {self.subject}",
            f"Date: {self.date.isoformat() if self.date else 'N/A'}"
        ]
        
        if self.body_plain:
            lines.append("")
            lines.append(self.body_plain)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"Email(id='{self.id}', from='{self.from_addr}', subject='{self.subject}')"


@dataclass
class RuleMatch:
    """Represents a match between an email and a rule."""
    rule: Rule
    match_type: RuleMatchType
    matched_value: str
    confidence: float = 1.0
    rule_name: str = ""
    
    def __post_init__(self):
        """Set rule_name from rule if not provided."""
        if not self.rule_name and self.rule:
            self.rule_name = self.rule.name
    
    @property
    def rule_type(self) -> 'RuleType':
        """Convenience: the rule_type of the matched rule."""
        return self.rule.rule_type if self.rule else None
    
    @property
    def priority(self) -> int:
        """Convenience: priority of the matched rule."""
        return self.rule.priority if self.rule else 0
    
    @property
    def category(self) -> str:
        """Convenience: category of the matched rule."""
        return self.rule.category if self.rule else ""
    
    @property
    def type(self) -> str:
        """Convenience: match_type as a plain string value."""
        return self.match_type.value if self.match_type else ""
    
    def __repr__(self) -> str:
        return f"RuleMatch(rule='{self.rule_name}', type={self.match_type.value}, value='{self.matched_value}')"


@dataclass
class ActionExecutionResult:
    """Result of an action execution."""
    action_type: ActionType
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_type": self.action_type.value,
            "success": self.success,
            "message": self.message,
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionExecutionResult':
        """Create from dictionary."""
        return cls(
            action_type=ActionType(data["action_type"]),
            success=data["success"],
            message=data["message"],
            details=data.get("details", {})
        )
    
    def __repr__(self) -> str:
        return f"ActionExecutionResult(action_type={self.action_type}, success={self.success}, message='{self.message}')"


# == Phase 6: Extended EmailMatch and EmailProcessingResult ==

@dataclass
class Phase6EmailMatch:
    """Phase 6 email match with typed match_type."""
    email_id: str
    rule_name: str
    match_type: 'RuleMatchType'
    matched_value: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email_id": self.email_id,
            "rule_name": self.rule_name,
            "match_type": self.match_type.value,
            "matched_value": self.matched_value,
            "confidence": self.confidence
        }


@dataclass
class Phase6EmailProcessingResult:
    """Phase 6 email processing result."""
    email_id: str
    status: str
    processing_time_ms: float = 0.0
    rules_matched: int = 0
    actions_executed: int = 0
    errors: List[str] = field(default_factory=list)
    matched_rules: List[str] = field(default_factory=list)
    executed_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email_id": self.email_id,
            "status": self.status,
            "processing_time_ms": self.processing_time_ms,
            "rules_matched": self.rules_matched,
            "actions_executed": self.actions_executed,
            "errors": self.errors,
            "matched_rules": self.matched_rules,
            "executed_actions": self.executed_actions
        }


@dataclass
class Phase6ProcessingConfig:
    """Phase 6 extended processing configuration."""
    max_processing_time_ms: int = 30000
    max_actions_per_email: int = 10
    enable_attachments: bool = True
    enable_llm: bool = False
    enable_monitoring: bool = True
    rule_sets: List[Any] = field(default_factory=list)
    action_sets: List[Any] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_processing_time_ms": self.max_processing_time_ms,
            "max_actions_per_email": self.max_actions_per_email,
            "enable_attachments": self.enable_attachments,
            "enable_llm": self.enable_llm,
            "enable_monitoring": self.enable_monitoring,
            "rule_sets": self.rule_sets,
            "action_sets": self.action_sets
        }


# Public aliases for backward-compatible and Phase 6 imports
EmailMatch = Phase6EmailMatch
EmailProcessingResult = Phase6EmailProcessingResult
