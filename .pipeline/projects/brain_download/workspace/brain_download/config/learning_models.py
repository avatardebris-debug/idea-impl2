"""DESSC framework configuration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OutputFormat(Enum):
    """Output format for course generation."""
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class DESSCConfig:
    """Configuration for the DESSC (Deconstruction, Selection, Sequencing, Stakes, Compression) framework."""
    version: str = "1.0.0"
    pareto_threshold: float = 0.20  # 20% of skills for 80% of outcomes
    min_module_size: int = 3
    max_module_size: int = 6
    default_module_size: int = 4
    min_skill_importance: float = 0.30
    max_skill_importance: float = 1.0
    default_skill_importance: float = 0.50
    min_estimated_minutes: int = 15
    max_estimated_minutes: int = 120
    default_estimated_minutes: int = 30
    enable_pareto_filtering: bool = True
    enable_domain_profiles: bool = True
    output_format: OutputFormat = OutputFormat.JSON  # json or markdown


def get_dessc_config() -> DESSCConfig:
    """Get the default DESSC configuration."""
    return DESSCConfig()
