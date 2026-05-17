"""Configuration for AgentFlow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AgentFlowConfig:
    """Configuration for AgentFlow."""

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    serp_api_key: Optional[str] = None

    # Agent settings
    max_retries: int = 3
    timeout_seconds: int = 300
    log_level: str = "INFO"

    # Workflow settings
    auto_retry: bool = True
    parallel_execution: bool = False

    # Storage settings
    storage_backend: str = "sqlite"
    storage_path: str = "agentflow.db"

    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentFlowConfig":
        """Create config from dictionary."""
        # Remove custom settings
        custom = data.pop("custom", {})
        config = cls(**data)
        config.custom = custom
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "openai_api_key": self.openai_api_key,
            "anthropic_api_key": self.anthropic_api_key,
            "google_api_key": self.google_api_key,
            "serp_api_key": self.serp_api_key,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "log_level": self.log_level,
            "auto_retry": self.auto_retry,
            "parallel_execution": self.parallel_execution,
            "storage_backend": self.storage_backend,
            "storage_path": self.storage_path,
            "custom": self.custom,
        }


# Global config instance
_config: Optional[AgentFlowConfig] = None


def get_config() -> AgentFlowConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AgentFlowConfig()
    return _config


def set_config(config: AgentFlowConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
