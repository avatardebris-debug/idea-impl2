"""Structured logging configuration for URL Health Checker.

Provides JSON-formatted structured logging by default, with support
for writing to a file or stdout.
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON string representation of the log record."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include extra fields if present
        for key in ("url", "status_code", "response_time_ms", "is_up", "error"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        return json.dumps(log_data)


def setup_logging(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
) -> logging.Logger:
    """Set up structured logging for the URL Health Checker.

    Args:
        log_file: Path to a log file. If None, logs go to stdout.
        log_level: Logging level string (e.g. 'INFO', 'DEBUG').

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("url_health_checker")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    formatter = JSONFormatter()

    if log_file:
        # File handler — write to file
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logger.addHandler(file_handler)

        # Console handler — warnings and above to stderr
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        # Stdout handler — all logs to stdout
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def log_check_result(
    logger: logging.Logger,
    url: str,
    status_code: Optional[int],
    response_time_ms: Optional[float],
    is_up: bool,
    level: str = "INFO",
) -> None:
    """Log a URL check result as a structured JSON line.

    Args:
        logger: Logger instance.
        url: The URL that was checked.
        status_code: HTTP status code (or None).
        response_time_ms: Response time in milliseconds (or None).
        is_up: Whether the URL is up.
        level: Log level string ('INFO' or 'ERROR').
    """
    extra = {
        "url": url,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "is_up": is_up,
    }
    message = (
        f"URL check: {url} -> status={status_code}, "
        f"time={response_time_ms}ms, up={is_up}"
    )
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra)


def log_error(
    logger: logging.Logger,
    url: str,
    error: Exception,
) -> None:
    """Log an error event.

    Args:
        logger: Logger instance.
        url: The URL that caused the error.
        error: The exception that occurred.
    """
    extra = {
        "url": url,
        "error": str(error),
    }
    logger.error(f"URL error: {url} -> {error}", extra=extra)
