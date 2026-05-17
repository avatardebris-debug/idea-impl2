"""Custom exception hierarchy for AgentFlow Drophip."""

from __future__ import annotations

from typing import Any, Optional


class DrophipError(Exception):
    """Base exception for all AgentFlow Drophip errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ParsingError(DrophipError):
    """Raised when parsing fails (intent, config, data)."""

    def __init__(self, message: str, field: Optional[str] = None, raw_input: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.field = field
        self.raw_input = raw_input


class ValidationError(DrophipError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.field = field
        self.value = value


class WorkflowError(DrophipError):
    """Raised when workflow execution fails."""

    def __init__(self, message: str, workflow_id: Optional[str] = None, task_id: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.workflow_id = workflow_id
        self.task_id = task_id


class CycleDetectedError(WorkflowError):
    """Raised when a cycle is detected in the DAG."""

    def __init__(self, message: str = "Cycle detected in workflow DAG", cycle_nodes: Optional[list[str]] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details=details)
        self.cycle_nodes = cycle_nodes or []


class AgentError(DrophipError):
    """Raised when an agent execution fails."""

    def __init__(self, message: str, agent_name: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.agent_name = agent_name


class AdapterError(DrophipError):
    """Raised when an integration adapter fails."""

    def __init__(self, message: str, adapter_type: Optional[str] = None, endpoint: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.adapter_type = adapter_type
        self.endpoint = endpoint


class ConfigurationError(DrophipError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.config_key = config_key
