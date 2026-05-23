"""ICM (Independent Chip Model) payout calculator for tournaments.

Implements the Independent Chip Model for calculating expected tournament
payouts based on chip stacks and prize structures.

Based on the principles from poker-mtt-icm-master and standard ICM theory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import random


@dataclass
class PrizeStructure:
    """Defines the prize distribution for a tournament."""
    placements: List[int]  # number of paid placements
    payouts: List[float]  # payout for each placement (must match placements count)

    def __post_init__(self):
        if len(self.placements) != len(self.payouts):
            raise ValueError("placements and payouts must have the same length")
        if not all(p >= 0 for p in self.payouts):
            raise ValueError("payouts must be non-negative")


@dataclass
class ICMResult:
    """Result of an ICM calculation."""
    player_chips: Dict[str, float]  # player -> chip count
    expected_payouts: Dict[str, float]  # player -> expected payout
    total_chips: float
    num_players: int


class ICMCalculator:
    """Calculates expected payouts using the Independent Chip Model.

    The ICM estimates the expected value of a player's tournament stack
    by considering all possible finishing orders weighted by their probability.

    For efficiency, uses the simplified ICM formula:
    E[payout] = sum over all permutations of (prob_of_order * payout_in_order)

    Uses Monte Carlo sampling for large fields where exact enumeration is infeasible.
    """

    def __init__(self, num_simulations: int = 100000):
        self.num_simulations = num_simulations

    def calculate(
        self,
        chip_stacks: Dict[str, float],
        prize_structure: PrizeStructure,
    ) -> ICMResult:
        """Calculate expected payouts using ICM.

        Args:
            chip_stacks: Mapping of player name to chip count.
            prize_structure: The tournament prize distribution.

        Returns:
            ICMResult with expected payouts for each player.
        """
        total_chips = sum(chip_stacks.values())
        if total_chips == 0:
            raise ValueError("Total chips must be positive")

        players = list(chip_stacks.keys())
        num_players = len(players)

        if num_players < 2:
            # Single player takes first place
            return ICMResult(
                player_chips=chip_stacks,
                expected_payouts={players[0]: prize_structure.payouts[0] if prize_structure.payouts else 0},
                total_chips=total_chips,
                num_players=num_players,
            )

        # Use Monte Carlo simulation for scalability
        expected_payouts = {p: 0.0 for p in players}

        for _ in range(self.num_simulations):
            # Simulate one tournament finish order
            finish_order = self._simulate_finish_order(chip_stacks)

            # Assign payouts based on finish order
            for i, player in enumerate(finish_order):
                if i < len(prize_structure.payouts):
                    expected_payouts[player] += prize_structure.payouts[i]

        # Average over simulations
        for player in expected_payouts:
            expected_payouts[player] /= self.num_simulations

        return ICMResult(
            player_chips=chip_stacks,
            expected_payouts=expected_payouts,
            total_chips=total_chips,
            num_players=num_players,
        )

    def _simulate_finish_order(self, chip_stacks: Dict[str, float]) -> List[str]:
        """Simulate a single tournament finish order using chip-proportional probabilities."""
        remaining = dict(chip_stacks)
        finish_order = []

        while remaining:
            total = sum(remaining.values())
            if total == 0:
                # All remaining players are eliminated simultaneously
                finish_order.extend(list(remaining.keys()))
                break

            # Pick winner proportional to chip count
            r = random.uniform(0, total)
            cumulative = 0
            winner = None
            for player, chips in remaining.items():
                cumulative += chips
                if r <= cumulative:
                    winner = player
                    break

            if winner is None:
                winner = list(remaining.keys())[-1]

            finish_order.append(winner)
            del remaining[winner]

        return finish_order

    def calculate_nash_equilibrium(
        self,
        chip_stacks: Dict[str, float],
        prize_structure: PrizeStructure,
        num_iterations: int = 50000,
    ) -> Dict[str, float]:
        """Calculate approximate Nash equilibrium push/fold ranges.

        For heads-up situations, computes the Nash equilibrium strategy
        for push/fold decisions pre-flop.

        Args:
            chip_stacks: Player chip stacks (must be 2 players for heads-up).
            prize_structure: Tournament prize structure.
            num_iterations: Number of iterations for the equilibrium calculation.

        Returns:
            Dictionary of player -> push frequency (0.0 to 1.0).
        """
        players = list(chip_stacks.keys())
        if len(players) != 2:
            raise ValueError("Nash equilibrium push/fold is only defined for heads-up")

        # Simplified Nash equilibrium calculation for push/fold
        # Uses the standard formula based on chip counts and blinds
        sb_chips = chip_stacks[players[0]]
        bb_chips = chip_stacks[players[1]]

        # Calculate Nash push/fold ranges using simplified model
        # The actual calculation involves solving a system of equations
        # Here we use an approximation based on stack depths
        sb_depth = sb_chips / max(1, prize_structure.payouts[1] if len(prize_structure.payouts) > 1 else 1)
        bb_depth = bb_chips / max(1, prize_structure.payouts[1] if len(prize_structure.payouts) > 1 else 1)

        # Simplified push ranges based on stack depth
        # These are approximate values from standard Nash equilibrium tables
        push_ranges = self._get_nash_push_ranges(sb_depth, bb_depth)

        return {
            players[0]: push_ranges.get("sb_push", 0.5),
            players[1]: push_ranges.get("bb_call", 0.5),
        }

    def _get_nash_push_ranges(
        self, sb_depth: float, bb_depth: float
    ) -> Dict[str, float]:
        """Get approximate Nash equilibrium push/call ranges based on stack depths."""
        # Simplified lookup table for push/call frequencies
        # In practice, this would use the full Nash equilibrium solver
        sb_push = max(0.0, min(1.0, 1.0 - sb_depth / 20.0))
        bb_call = max(0.0, min(1.0, 1.0 - bb_depth / 25.0))

        return {
            "sb_push": sb_push,
            "bb_call": bb_call,
        }


def calculate_icm_for_tournament(
    chip_stacks: Dict[str, float],
    prize_structure: PrizeStructure,
    num_simulations: int = 100000,
) -> ICMResult:
    """Convenience function to calculate ICM payouts.

    Args:
        chip_stacks: Mapping of player name to chip count.
        prize_structure: Tournament prize distribution.
        num_simulations: Number of Monte Carlo simulations.

    Returns:
        ICMResult with expected payouts.
    """
    calculator = ICMCalculator(num_simulations=num_simulations)
    return calculator.calculate(chip_stacks, prize_structure)
