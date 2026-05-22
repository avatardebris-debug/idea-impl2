"""Module for loading and validating JSON files."""

import json
from typing import Any


def load_json(path: str) -> Any:
    """Load and parse a JSON file.
    
    Args:
        path: Path to the JSON file to load.
        
    Returns:
        The parsed JSON data (dict, list, or primitive).
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid JSON.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {path}: {e}")
