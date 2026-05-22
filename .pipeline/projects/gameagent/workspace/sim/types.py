"""Type definitions for simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulationConfig:
    """Configuration for simulation."""

    num_episodes: int = 100
    grid_width: int = 5
    grid_height: int = 5
    goal_position: tuple[int, int] = (4, 4)
    seed: int = 42
    obstacles: list[tuple[int, int]] = field(default_factory=list)
    render: bool = False


@dataclass
class EpisodeResult:
    """Result of a single episode."""

    total_reward: float
    num_steps: int
    terminated: bool
    truncated: bool
    start_time: float
    end_time: float
    seed: int = 42


@dataclass
class SimulationResult:
    """Result of a full simulation."""

    total_episodes: int
    episode_results: list[EpisodeResult]
    mean_reward: float
    std_reward: float
    mean_steps: float
    success_rate: float
    start_time: float
    end_time: float
