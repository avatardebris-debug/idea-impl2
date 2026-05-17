"""
Phase 6: Email Processing Models

This module contains the Phase 6 implementation of email processing models.
"""

from .models import (
    Email,
    Rule,
    RuleMatch,
    RuleType,
    RuleMatchType,
    RuleMatchStrategy,
    Category,
    ActionType,
    ActionExecutionResult,
    EmailMetadata,
    ProcessingStats,
    RuleSet,
    ActionSet,
    ProcessingConfig,
    AttachmentProcessingResult,
    EmailMatch,
    EmailProcessingResult
)

__all__ = [
    'Email',
    'Rule',
    'RuleMatch',
    'RuleType',
    'RuleMatchType',
    'RuleMatchStrategy',
    'Category',
    'ActionType',
    'ActionExecutionResult',
    'EmailMetadata',
    'ProcessingStats',
    'RuleSet',
    'ActionSet',
    'ProcessingConfig',
    'AttachmentProcessingResult',
    'EmailMatch',
    'EmailProcessingResult'
]
