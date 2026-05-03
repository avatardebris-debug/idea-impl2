"""Newsletter Online Profit Environment for RL Training.

This package provides a simulation environment for training reinforcement learning
agents to manage a newsletter business. The environment tracks subscriber growth,
revenue, costs, and profitability over time.
"""

from .config import SimConfig
from .state import NewsletterState, SimulationHistory
from .observation import Observation
from .simulator import NewsletterSimulator
from .environment import NewsletterEnv

__all__ = [
    "SimConfig",
    "NewsletterState",
    "SimulationHistory",
    "Observation",
    "NewsletterSimulator",
    "NewsletterEnv",
]

__version__ = "0.1.0"
