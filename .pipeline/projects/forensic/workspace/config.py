"""Forensic configuration module."""

import os
from dataclasses import dataclass, field


@dataclass
class ForensicConfig:
    """Configuration for the forensic analysis system."""

    batch_size: int = 10
    timeout: int = 30
    red_flag_threshold: int = 50
    risk_levels: dict = field(default_factory=lambda: {
        "low": 20,
        "medium": 50,
        "high": 75,
        "critical": 100,
    })

    def __post_init__(self):
        """Handle None values by falling back to defaults."""
        if self.batch_size is None:
            self.batch_size = 10
        if self.timeout is None:
            self.timeout = 30
        if self.red_flag_threshold is None:
            self.red_flag_threshold = 50
        if self.risk_levels is None:
            self.risk_levels = {
                "low": 20,
                "medium": 50,
                "high": 75,
                "critical": 100,
            }


class _ConfigSingleton:
    """Singleton holder for the global config."""
    _instance = None

    @classmethod
    def get(cls) -> ForensicConfig:
        if cls._instance is None:
            db_path = os.environ.get("FORENSIC_DB_PATH")
            cls._instance = ForensicConfig()
        return cls._instance


def get_config() -> ForensicConfig:
    """Get the global ForensicConfig singleton."""
    return _ConfigSingleton.get()
