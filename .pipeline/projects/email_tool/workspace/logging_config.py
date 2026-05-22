"""Logging configuration for Email Tool.

This module provides centralized logging setup for the email_tool package.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class EmailToolFormatter(logging.Formatter):
    """Custom formatter for email_tool logs."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for console output."""
        # Add color to level name
        levelname = record.levelname
        if self.usesColor():
            color = self.COLORS.get(levelname, '')
            levelname = f"{color}{levelname}{self.RESET}"
        
        record.levelname = levelname
        return super().format(record)
    
    def usesColor(self) -> bool:
        """Check if output supports colors."""
        return sys.stderr.isatty()


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    console_output: bool = True,
    use_colors: bool = True
) -> logging.Logger:
    """Set up logging for email_tool.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, defaults to INFO.
        log_file: Path to log file. If None, no file logging.
        console_output: Whether to log to console.
        use_colors: Whether to use ANSI colors in console output.
    
    Returns:
        Configured logger instance.
    """
    # Get root logger
    logger = logging.getLogger('email_tool')
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level - handle both string and integer log levels
    if log_level is None:
        level = logging.INFO
    elif isinstance(log_level, int):
        level = log_level
    else:
        level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create formatter
    if use_colors:
        formatter = EmailToolFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            print(f"Warning: Could not create log file {log_file}: {e}", file=sys.stderr)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Name of the logger (typically __name__).
    
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def configure_from_dict(config: Dict[str, Any]):
    """Configure logging from a dictionary.
    
    Args:
        config: Dictionary with 'log_level' and 'log_file' keys.
    """
    log_level = config.get('log_level', 'INFO')
    log_file = config.get('log_file')
    
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_output=True,
        use_colors=True
    )
