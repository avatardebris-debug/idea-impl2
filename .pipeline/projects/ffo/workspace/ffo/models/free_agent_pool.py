"""Free agent pool manager for FFO."""

from __future__ import annotations

from typing import Optional

from ffo.models.player import FreeAgent
from ffo.models.valuation import value_player, rank_by_efficiency


class FreeAgentPool:
    """Holds a collection of available free agents.

    Supports filtering by position, rating range, and querying
    top candidates within a budget.
    """

    def __init__(self, agents: Optional[list[FreeAgent]] = None):
        self._agents: list[FreeAgent] = list(agents or [])

    @property
    def count(self) -> int:
        """Number of agents in the pool."""
        return len(self._agents)

    def add_agent(self, agent: FreeAgent) -> None:
        """Add a free agent to the pool."""
        self._agents.append(agent)

    def add_agents(self, agents: list[FreeAgent]) -> None:
        """Add multiple free agents to the pool."""
        self._agents.extend(agents)

    def remove_agent(self, name: str) -> None:
        """Remove an agent by name."""
        self._agents = [a for a in self._agents if a.name != name]

    def filter_by_position(self, position: str) -> list[FreeAgent]:
        """Filter agents by position (exact match)."""
        return [a for a in self._agents if a.position == position]

    def filter_by_positions(self, positions: list[str]) -> list[FreeAgent]:
        """Filter agents by a list of positions."""
        return [a for a in self._agents if a.position in positions]

    def filter_by_rating_range(
        self, min_rating: float, max_rating: float
    ) -> list[FreeAgent]:
        """Filter agents by overall rating range (inclusive)."""
        return [
            a for a in self._agents
            if min_rating <= a.overall_rating <= max_rating
        ]

    def filter_by_salary_range(
        self, min_salary: float, max_salary: float
    ) -> list[FreeAgent]:
        """Filter agents by salary range (inclusive)."""
        return [
            a for a in self._agents
            if min_salary <= a.salary <= max_salary
        ]

    def get_available(self) -> list[FreeAgent]:
        """Return all available free agents."""
        return [a for a in self._agents if a.available]

    def get_top_candidates(
        self,
        n: int,
        budget: Optional[float] = None,
        position: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        age_weight: float = 1.0,
        contract_weight: float = 1.0,
    ) -> list[tuple[FreeAgent, float]]:
        """Get top N candidates sorted by valuation.

        Args:
            n: Number of top candidates to return.
            budget: Optional maximum salary for each candidate.
            position: Optional position filter.
            min_rating: Optional minimum rating filter.
            max_rating: Optional maximum rating filter.
            age_weight: Weight for age factor in valuation.
            contract_weight: Weight for contract factor in valuation.

        Returns:
            List of (agent, score) tuples sorted by score descending.
        """
        candidates = self.get_available()

        if position:
            candidates = [a for a in candidates if a.position == position]
        if min_rating is not None:
            candidates = [a for a in candidates if a.overall_rating >= min_rating]
        if max_rating is not None:
            candidates = [a for a in candidates if a.overall_rating <= max_rating]
        if budget is not None:
            candidates = [a for a in candidates if a.salary <= budget]

        ranked = rank_by_efficiency(candidates, age_weight, contract_weight)
        return ranked[:n]

    def get_all(self) -> list[FreeAgent]:
        """Return all agents in the pool."""
        return list(self._agents)

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"FreeAgentPool(count={len(self._agents)})"
