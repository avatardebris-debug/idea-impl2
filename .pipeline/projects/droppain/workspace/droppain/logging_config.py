"""Logging configuration for droppain.

Provides structured logging with configurable log level, format, and optional
file output. Call setup_logging() at module load or from CLI entry point.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


# Default logging format (structured, stderr-only)
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
DEFAULT_LEVEL = "INFO"


def setup_logging(
    level: str = DEFAULT_LEVEL,
    fmt: Optional[str] = None,
    datefmt: Optional[str] = None,
    log_file: Optional[str] = None,
    propagate: bool = False,
) -> None:
    """Configure the root logger for droppain.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        fmt: Custom log format string. Defaults to structured format.
        datefmt: Custom date format string. Defaults to ISO-like format.
        log_file: Optional file path to also write logs to.
        propagate: Whether to propagate to parent loggers.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    log_fmt = fmt or DEFAULT_FORMAT
    log_datefmt = datefmt or DEFAULT_DATE_FORMAT

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates on repeated calls
    root_logger.handlers.clear()

    # Stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(log_level)
    stderr_handler.setFormatter(logging.Formatter(log_fmt, datefmt=log_datefmt))
    root_logger.addHandler(stderr_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_fmt, datefmt=log_datefmt))
        root_logger.addHandler(file_handler)

    root_logger.propagate = propagate

    # Set third-party loggers to WARNING to reduce noise
    for noisy_logger in ("urllib3", "requests", "httpx"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger configured with the default format.

    Args:
        name: Logger name (typically ``__name__``).

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
