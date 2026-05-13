"""JSON I/O utilities for FFO.

Provides helpers for loading and saving roster and free agent pool
data in JSON format.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class IOError(Exception):
    """Raised when a file I/O operation fails."""

    def __init__(self, message: str, path: str = ""):
        self.path = path
        super().__init__(message)


def load_json(path: str | Path) -> Any:
    """Load and parse a JSON file.

    Args:
        path: Path to the JSON file to load.

    Returns:
        The parsed JSON data (dict, list, or primitive).

    Raises:
        IOError: If the file does not exist or contains invalid JSON.
    """
    path = Path(path)
    if not path.exists():
        raise IOError(f"File not found: {path}", str(path))
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise IOError(f"Invalid JSON in file {path}: {e}", str(path))


def save_json(data: Any, path: str | Path) -> None:
    """Save data to a JSON file.

    Args:
        data: The data to serialize (must be JSON-serializable).
        path: Destination file path.

    Raises:
        IOError: If the file cannot be written.
    """
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except (OSError, TypeError) as e:
        raise IOError(f"Cannot write JSON to {path}: {e}", str(path))
