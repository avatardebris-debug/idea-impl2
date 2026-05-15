"""Configuration for Forensic Suite."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class ForensicConfig:
    """Configuration for Forensic Suite."""

    # Database
    db_path: str = "forensic.db"

    # Rate limiting
    requests_per_second: int = 10
    rate_limit_delay: float = 0.1
    max_retries: int = 3
    base_backoff: float = 1.0

    # Logging
    log_level: str = "INFO"

    # Importer
    batch_size: int = 10
    timeout: int = 30

    # Fraud detection
    red_flag_threshold: float = 0.0
    risk_levels: dict = field(default_factory=lambda: {
        "low": (0, 30),
        "medium": (31, 60),
        "high": (61, 85),
        "critical": (86, 100),
    })

    def __post_init__(self):
        """Load config.yaml automatically on instantiation, then apply env overrides."""
        config_paths = [
            os.path.join(os.getcwd(), "config.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"),
            os.path.expanduser("~/.forensic/config.yaml"),
        ]
        for path in config_paths:
            if yaml and os.path.exists(path):
                self._load_from_file(path)
                break

        # Environment variable overrides
        if os.environ.get("FORENSIC_DB_PATH"):
            self.db_path = os.environ["FORENSIC_DB_PATH"]
        if os.environ.get("FORENSIC_MAX_RETRIES"):
            self.max_retries = int(os.environ["FORENSIC_MAX_RETRIES"])
        if os.environ.get("FORENSIC_LOG_LEVEL"):
            self.log_level = os.environ["FORENSIC_LOG_LEVEL"]
        if os.environ.get("FORENSIC_BATCH_SIZE"):
            self.batch_size = int(os.environ["FORENSIC_BATCH_SIZE"])
        if os.environ.get("FORENSIC_TIMEOUT"):
            self.timeout = int(os.environ["FORENSIC_TIMEOUT"])
        if os.environ.get("FORENSIC_REQUESTS_PER_SECOND"):
            self.requests_per_second = int(os.environ["FORENSIC_REQUESTS_PER_SECOND"])

    def _load_from_file(self, path: str):
        """Load configuration from a YAML file."""
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            return

        db = data.get("database", {})
        if "db_path" in db:
            self.db_path = db["db_path"]

        rl = data.get("rate_limiting", {})
        if "requests_per_second" in rl:
            self.requests_per_second = rl["requests_per_second"]
        if "delay" in rl:
            self.rate_limit_delay = rl["delay"]
        if "max_retries" in rl:
            self.max_retries = rl["max_retries"]

        log = data.get("logging", {})
        if "level" in log:
            self.log_level = log["level"]

    def to_dict(self) -> dict:
        """Return config as a nested dict."""
        return {
            "database": {"db_path": self.db_path},
            "rate_limiting": {
                "requests_per_second": self.requests_per_second,
                "rate_limit_delay": self.rate_limit_delay,
                "max_retries": self.max_retries,
                "base_backoff": self.base_backoff,
            },
            "logging": {"level": self.log_level},
            "importer": {"batch_size": self.batch_size, "timeout": self.timeout},
            "fraud_detection": {
                "red_flag_threshold": self.red_flag_threshold,
                "risk_levels": self.risk_levels,
            },
        }


_config_instance: Optional[ForensicConfig] = None


def get_config() -> ForensicConfig:
    """Get or create the global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ForensicConfig()
    return _config_instance
