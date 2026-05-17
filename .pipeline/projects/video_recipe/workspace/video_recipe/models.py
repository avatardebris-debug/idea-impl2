"""Data models for the Video Recipe Browser."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Video:
    """Represents an uploaded video."""
    video_id: str
    filename: str
    task_type: Optional[str] = None
    duration: Optional[float] = None
    original_path: Optional[str] = None


@dataclass
class RecipeStep:
    """Represents a single step in a recipe."""
    step_index: int
    description: str
    timestamp: float
    inferred_tools: list = field(default_factory=list)
    inferred_materials: list = field(default_factory=list)


@dataclass
class Recipe:
    """Represents a complete recipe extracted from a video."""
    video_id: str
    title: str
    summary: str
    steps: list = field(default_factory=list)
    task_type: Optional[str] = None
