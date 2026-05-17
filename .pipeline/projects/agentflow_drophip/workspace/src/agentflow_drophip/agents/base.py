"""Base agent class for all dropshipping agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class AgentResult:
    """Result of an agent execution."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    products: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.success

    @property
    def is_failure(self) -> bool:
        return not self.success


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the base agent.

        Args:
            name: Name of the agent.
            config: Configuration dictionary.
        """
        self.name = name
        self.config = config or {}
        self.execution_count = 0
        self.last_result: Optional[AgentResult] = None

    @abstractmethod
    def execute(self, **kwargs: Any) -> AgentResult:
        """Execute the agent's primary function.

        Args:
            **kwargs: Input parameters for the agent.

        Returns:
            AgentResult with execution outcome.
        """
        pass

    def validate_config(self) -> bool:
        """Validate the agent's configuration.

        Returns:
            True if configuration is valid.
        """
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent.

        Returns:
            Dictionary with agent status information.
        """
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "last_result_success": self.last_result.is_success if self.last_result else None,
            "last_result_time": self.last_result.metadata.get("timestamp") if self.last_result else None,
        }

    def reset(self) -> None:
        """Reset the agent's state."""
        self.execution_count = 0
        self.last_result = None
