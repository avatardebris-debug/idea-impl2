"""Abstract agent interface for LLM-powered email processing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from email_tool.models import Rule


@dataclass
class AgentContext:
    """Context for agent interactions."""
    conversation_id: Optional[str] = None
    turn: int = 0
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation history."""
        self.history.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp()
        })
    
    def get_context_summary(self) -> str:
        """Get a summary of the conversation context."""
        if not self.history:
            return "No conversation history."
        
        summaries = []
        for msg in self.history[-10:]:  # Last 10 messages
            summaries.append(f"[{msg['role']}] {msg['content']}")
        
        return "\n".join(summaries)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


@dataclass
class AgentResult:
    """Result from an agent operation."""
    success: bool
    data: Any = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AbstractAgent(ABC):
    """
    Abstract base class for email processing agents.
    
    Agents provide LLM-powered capabilities for:
    - Generating rules from natural language
    - Categorizing emails that don't match existing rules
    - Summarizing inbox organization status
    
    All agents must implement these core methods while allowing
    for provider-specific implementations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration including provider settings.
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.context = AgentContext()
    
    @abstractmethod
    def generate_rules(self, 
                       description: str,
                       sample_emails: List[Dict[str, Any]],
                       context: Optional[AgentContext] = None) -> AgentResult:
        """
        Generate rules from natural language description.
        
        Args:
            description: Natural language description of desired rules.
            sample_emails: Sample emails to inform rule generation.
            context: Optional context for the generation.
        
        Returns:
            AgentResult with generated rules.
        """
        pass
    
    @abstractmethod
    def suggest_categories(self,
                          emails: List[Dict[str, Any]],
                          existing_categories: List[str],
                          context: Optional[AgentContext] = None) -> AgentResult:
        """
        Suggest categories for emails that don't match existing rules.
        
        Args:
            emails: List of emails to categorize.
            existing_categories: List of currently used categories.
            context: Optional context for categorization.
        
        Returns:
            AgentResult with suggested categories.
        """
        pass
    
    @abstractmethod
    def summarize_inbox(self,
                       emails: List[Dict[str, Any]],
                       rules: List[Rule],
                       context: Optional[AgentContext] = None) -> AgentResult:
        """
        Generate an inbox summary.
        
        Args:
            emails: List of emails to summarize.
            rules: List of active rules.
            context: Optional context for summarization.
        
        Returns:
            AgentResult with inbox summary.
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities supported by this agent.
        
        Returns:
            List of capability strings.
        """
        pass
    
    def reset_context(self):
        """Reset the agent's conversation context."""
        self.context = AgentContext()
    
    def _validate_rules(self, rules: List[Dict[str, Any]]) -> AgentResult:
        """
        Validate generated rules.
        
        Args:
            rules: List of rule dictionaries to validate.
        
        Returns:
            AgentResult with validation status.
        """
        from email_tool.agent.rule_validator import RuleValidator
        
        validator = RuleValidator()
        return validator.validate_rules(rules)
    
    def _format_email_summary(self, emails: List[Dict[str, Any]]) -> str:
        """
        Format a summary of emails for LLM consumption.
        
        Args:
            emails: List of email dictionaries.
        
        Returns:
            Formatted string summary.
        """
        if not emails:
            return "No emails provided."
        
        summaries = []
        for i, email in enumerate(emails[:10]):  # Limit to 10 for context
            summary = f"Email {i+1}:\n"
            summary += f"  From: {email.get('from', 'Unknown')}\n"
            summary += f"  Subject: {email.get('subject', 'No subject')}\n"
            summary += f"  Date: {email.get('date', 'Unknown date')}\n"
            summary += f"  Has attachments: {email.get('has_attachments', False)}\n"
            if email.get('body'):
                body_preview = email['body'][:200] + "..." if len(email['body']) > 200 else email['body']
                summary += f"  Body preview: {body_preview}\n"
            summaries.append(summary)
        
        if len(emails) > 10:
            summaries.append(f"... and {len(emails) - 10} more emails")
        
        return "\n".join(summaries)
