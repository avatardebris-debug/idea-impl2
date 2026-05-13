"""
FFO - Football Financial Optimizer

A financial model for valuing players vs salary cap including
a pool of available free agents.
"""

from ffo.models.player import Player, FreeAgent
from ffo.models.salary_cap import SalaryCap
from ffo.models.valuation import value_player, rank_by_efficiency
from ffo.models.free_agent_pool import FreeAgentPool
from ffo.optimizer import optimize_roster

__version__ = "0.1.0"
__all__ = [
    "Player",
    "FreeAgent",
    "SalaryCap",
    "value_player",
    "rank_by_efficiency",
    "FreeAgentPool",
    "optimize_roster",
]
