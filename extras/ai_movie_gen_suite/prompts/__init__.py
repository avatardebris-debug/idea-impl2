"""Prompts package — exports all Jinja2 prompt templates."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent

__all__ = [
    "TEMPLATES_DIR",
]
