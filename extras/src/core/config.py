"""Configuration module for BudgetFlow Tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppConfig:
    """Application configuration."""

    # Database settings
    db_path: str = "budgetflow.db"

    # Default settings
    default_currency: str = "$"
    default_language: str = "en"
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"

    # UI settings
    theme: str = "dark"
    font_size: int = 12
    show_notifications: bool = True

    # Import settings
    default_import_format: str = "csv"
    max_import_file_size: int = 10 * 1024 * 1024  # 10MB

    # Budget settings
    default_budget_period: str = "monthly"
    budget_warning_threshold: float = 0.8  # 80%
    budget_alert_threshold: float = 1.0  # 100%

    # Export settings
    export_formats: list[str] = field(default_factory=lambda: ["csv", "json", "pdf"])
    default_export_format: str = "csv"

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = "budgetflow.log"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.budget_warning_threshold < 0 or self.budget_warning_threshold > 1:
            raise ValueError("budget_warning_threshold must be between 0 and 1")
        if self.budget_alert_threshold < 0 or self.budget_alert_threshold > 1:
            raise ValueError("budget_alert_threshold must be between 0 and 1")


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config


def update_config(**kwargs) -> None:
    """Update configuration with new values."""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise AttributeError(f"Config has no attribute '{key}'")
