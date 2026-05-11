"""Configuration management for BudgetFlow Tracker."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """BudgetFlow configuration manager."""

    DEFAULT_CONFIG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "config",
        "budgetflow.yaml",
    )

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._settings: dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load configuration from YAML file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self._settings = yaml.safe_load(f) or {}
        else:
            self._settings = self._default_settings()
            self._save()

    def _default_settings(self) -> dict[str, Any]:
        """Return default configuration."""
        return {
            "database": {
                "path": os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                    "data",
                    "budgetflow_tracker.db",
                ),
                "journal_mode": "WAL",
            },
            "import": {
                "default_bank_format": None,
                "date_formats": ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%b %d, %Y"],
                "amount_decimal_places": 2,
            },
            "categorization": {
                "default_confidence_threshold": 0.5,
                "max_rules_per_transaction": 10,
            },
            "budget": {
                "default_period": "monthly",
                "rollover_enabled": True,
            },
            "ui": {
                "default_date_range_days": 30,
                "color_theme": "default",
            },
        }

    def _save(self):
        """Save configuration to YAML file."""
        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self._settings, f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'database.path')."""
        keys = key.split(".")
        value = self._settings
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split(".")
        d = self._settings
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        self._save()

    @property
    def database_path(self) -> str:
        """Get the database path."""
        return self.get("database.path", self._default_settings()["database"]["path"])

    @property
    def default_date_formats(self) -> list[str]:
        """Get default date formats for import."""
        return self.get("import.date_formats", self._default_settings()["import"]["date_formats"])

    @property
    def default_confidence_threshold(self) -> float:
        """Get default confidence threshold for categorization."""
        return self.get("categorization.default_confidence_threshold", 0.5)
