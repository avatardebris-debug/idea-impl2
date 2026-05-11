"""Configuration for SEC Importer 2."""

from __future__ import annotations

import os
from pathlib import Path

# Default paths
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sec_importer.db")
DEFAULT_TICKERS_FILE = os.path.join(os.path.dirname(__file__), "tickers.csv")
DEFAULT_LOG_LEVEL = "INFO"

# SEC API settings
SEC_BASE_URL = "https://data.sec.gov/submissions/"
SEC_USER_AGENT = "SECImporter/0.1.0 (contact: sec-importer@example.com)"
SEC_RATE_LIMIT_DELAY = 0.1  # seconds between requests
SEC_MAX_RETRIES = 5
SEC_BASE_DELAY = 1.0  # base delay for exponential backoff


def get_config() -> dict:
    """Get the default configuration."""
    return {
        "db_path": DEFAULT_DB_PATH,
        "tickers_file": DEFAULT_TICKERS_FILE,
        "log_level": DEFAULT_LOG_LEVEL,
        "sec_user_agent": SEC_USER_AGENT,
        "sec_rate_limit_delay": SEC_RATE_LIMIT_DELAY,
        "sec_max_retries": SEC_MAX_RETRIES,
        "sec_base_delay": SEC_BASE_DELAY,
    }
