"""Core optimizer for FFO.

Provides the main optimize_roster function that takes a current roster,
salary cap, and free agent pool, then returns an optimized roster by
adding/subtracting players to maximize total team value within cap constraints.
"""

from __future__ import annotations

from ffo.models.player import Player, FreeAgent
from ffo.models.salary_cap import SalaryCap, SalaryCapError
from ffo.models.valuation import value_player, rank_by_efficiency
from ffo.models.free_agent_pool import FreeAgentPool


def optimize_roster(
    roster: list[Player],
    cap: SalaryCap,
    pool: FreeAgentPool,
    age_weight: float = 1.0,
    contract_weight: float = 1.0,
) -> list[Player]:
    """Optimize a roster by adding/subtracting players to maximize total team value.

    Strategy:
    1. Calculate current team value (sum of all player value_scores).
    2. Evaluate all possible additions from the free agent pool.
    3. Evaluate all possible removals from the current roster.
    4. Use a greedy approach: repeatedly add the best affordable agent
       and remove the worst player if it frees up enough budget.

    Args:
        roster: Current list of players.
        cap: Salary cap with current payroll tracking.
        pool: Free agent pool to draw from.
        age_weight: Weight for age factor in valuation.
        contract_weight: Weight for contract factor in valuation.

    Returns:
        Optimized list of players within cap constraints.
    """
    # Work with a copy of the roster
    current_roster = list(roster)
    current_cap = SalaryCap(cap_limit=cap.cap_limit)

    # Add current roster players to the cap
    for player in current_roster:
        try:
            current_cap.add_player(player)
        except SalaryCapError:
            # If the roster already exceeds cap, skip the player
            pass

    # Get available free agents
    available = pool.get_available()

    # If no free agents, return current roster
    if not available:
        return current_roster

    # Calculate current team value
    def team_value(roster: list[Player]) -> float:
        return sum(value_player(p, age_weight, contract_weight) for p in roster)

    best_roster = list(current_roster)
    best_value = team_value(best_roster)

    # Greedy optimization: try adding each available agent
    for agent in available:
        if current_cap.can_afford(agent):
            # Try adding this agent
            test_roster = list(current_roster) + [agent]
            test_cap = SalaryCap(cap_limit=cap.cap_limit)
            try:
                for p in test_roster:
                    test_cap.add_player(p)
            except SalaryCapError:
                # If the test roster exceeds cap, skip it
                continue

            test_value = team_value(test_cap.get_roster())
            if test_value > best_value:
                best_roster = test_cap.get_roster()
                best_value = test_value

    # Try removing worst players and adding better ones
    # Sort current roster by value (worst first)
    ranked_roster = rank_by_efficiency(current_roster, age_weight, contract_weight)

    for worst_player in ranked_roster:
        # Remove this player to free up budget
        freed_budget = worst_player.salary
        remaining_budget = current_cap.remaining + freed_budget

        if remaining_budget <= 0:
            continue

        # Find best available agent within freed budget
        top_candidates = pool.get_top_candidates(
            n=1,
            budget=remaining_budget,
            age_weight=age_weight,
            contract_weight=contract_weight,
        )

        if not top_candidates:
            continue

        best_agent, best_agent_score = top_candidates[0]

        # Only swap if the new player has a better score
        if best_agent_score > value_player(worst_player, age_weight, contract_weight):
            # Perform the swap
            new_roster = [p for p in current_roster if p.name != worst_player.name]
            new_roster.append(best_agent)

            # Verify cap compliance
            new_cap = SalaryCap(cap_limit=cap.cap_limit)
            try:
                for p in new_roster:
                    new_cap.add_player(p)
            except SalaryCapError:
                # If the new roster exceeds cap, skip it
                continue

            new_value = team_value(new_cap.get_roster())
            if new_value > best_value:
                best_roster = new_cap.get_roster()
                best_value = new_value

    return best_roster
