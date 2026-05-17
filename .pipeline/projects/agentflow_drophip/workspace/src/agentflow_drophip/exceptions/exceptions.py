"""Custom exceptions for AgentFlow."""

from __future__ import annotations

from typing import Any, Dict, Optional


class AgentFlowError(Exception):
    """Base exception for AgentFlow."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class AgentError(AgentFlowError):
    """Exception raised when an agent fails."""

    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message.
            agent_name: Name of the agent that failed.
            details: Additional error details.
        """
        super().__init__(message, details)
        self.agent_name = agent_name


class OrchestratorError(AgentFlowError):
    """Exception raised when the orchestrator fails."""

    def __init__(
        self,
        message: str,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message.
            action: Action that failed.
            details: Additional error details.
        """
        super().__init__(message, details)
        self.action = action


class ParserError(AgentFlowError):
    """Exception raised when parsing fails."""

    def __init__(
        self,
        message: str,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message.
            description: Description that failed to parse.
            details: Additional error details.
        """
        super().__init__(message, details)
        self.description = description


class WorkflowError(AgentFlowError):
    """Exception raised when workflow execution fails."""

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message.
            task_id: ID of the task that failed.
            details: Additional error details.
        """
        super().__init__(message, details)
        self.task_id = task_id


class CycleDetectedError(AgentFlowError):
    """Exception raised when a cycle is detected in a DAG."""

    def __init__(
        self,
        message: str,
        cycle_nodes: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message.
            cycle_nodes: List of nodes involved in the cycle.
            details: Additional error details.
        """
        super().__init__(message, details)
        self.cycle_nodes = cycle_nodes or []
