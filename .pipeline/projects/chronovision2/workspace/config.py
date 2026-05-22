"""Base configuration for Chronovision2."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SimulationConfig:
    """Configuration for a single world simulation."""
    hypothesis_id: str = "default"
    time_horizon: int = 10
    random_seed: int | None = None
    rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionConfig:
    """Configuration for the prediction engine."""
    num_simulations: int = 5
    composite_method: str = "weighted_average"  # weighted_average, median, max_likelihood
    default_time_horizon: int = 10


@dataclass
class SurpriseConfig:
    """Configuration for the surprise meter."""
    default_metric: str = "l2"  # l1, l2
    normalize: bool = True


@dataclass
class HypothesisConfig:
    """Configuration for a hypothesis in the hypothesis manager."""
    hypothesis_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    score: float = 0.0
    survival_count: int = 0


@dataclass
class ChronovisionConfig:
    """Top-level configuration for Chronovision2."""
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    prediction: PredictionConfig = field(default_factory=PredictionConfig)
    surprise: SurpriseConfig = field(default_factory=SurpriseConfig)

    @classmethod
    def from_env(cls) -> "ChronovisionConfig":
        """Create config from environment variables with defaults."""
        return cls()
