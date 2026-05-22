"""Logging configuration for the invoice processor."""

import logging
import os
import sys
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
) -> logging.Logger:
    """Set up a logger with file and console handlers.

    Args:
        name: Logger name. If None, uses the root logger.
        log_file: Path to log file. If None, logs to stderr only.
        log_level: Logging level string (e.g. 'DEBUG', 'INFO').

    Returns:
        Configured logger instance.
    """
    log_level = log_level or os.environ.get("LOG_LEVEL", "INFO")
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    logger = logging.getLogger(name or "invoice_processor")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler (warnings and above)
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.WARNING)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (if requested)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            pass  # Silently skip file logging if it fails

    return logger


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a named logger."""
    return setup_logger(name=name)
