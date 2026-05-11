"""Schemas package — exports JSON schemas."""

from pathlib import Path

SCHEMAS_DIR = Path(__file__).parent

__all__ = [
    "SCHEMAS_DIR",
]
