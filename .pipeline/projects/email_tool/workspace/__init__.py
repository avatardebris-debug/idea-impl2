"""
Email Tool - Email processing and management system.

This package provides tools for parsing, matching, and processing email messages
according to configurable rules and actions.
"""

from email_tool.models import (
    Rule,
    RuleType,
    Action,
    ActionType,
    Email,
    RuleMatch,
    RuleMatchType,
    ActionExecutionResult,
    EmailMatch,
    EmailProcessingResult,
    EmailMetadata,
    ProcessingStats,
    RuleSet,
    ActionSet,
    AttachmentProcessingResult,
    ProcessingConfig,
    RuleMatchStrategy,
    Category,
    EmailAttachmentProcessingResult,
)
from email_tool.parser import EmailParser
from email_tool.matcher import RuleMatcher
from email_tool.dispatcher import Dispatcher, ActionBuilder, ActionExecutor
from email_tool.processor import (
    EmailProcessor,
    PipelineBuilder,
    PipelineExecutor,
    PipelineMonitor,
    PipelineConfig,
)

__version__ = "1.0.0"
__all__ = [
    # Models
    "Rule",
    "RuleType",
    "Action",
    "ActionType",
    "Email",
    "RuleMatch",
    "RuleMatchType",
    "ActionExecutionResult",
    "EmailMatch",
    "EmailProcessingResult",
    "EmailMetadata",
    "ProcessingStats",
    "RuleSet",
    "ActionSet",
    "AttachmentProcessingResult",
    "ProcessingConfig",
    "RuleMatchStrategy",
    "Category",
    "EmailAttachmentProcessingResult",
    # Components
    "EmailParser",
    "RuleMatcher",
    "Dispatcher",
    "ActionBuilder",
    "ActionExecutor",
    # Processor
    "EmailProcessor",
    "PipelineBuilder",
    "PipelineExecutor",
    "PipelineMonitor",
    "PipelineConfig",
]
