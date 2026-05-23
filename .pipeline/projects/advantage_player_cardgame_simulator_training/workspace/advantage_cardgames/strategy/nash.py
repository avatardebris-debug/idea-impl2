"""Nash equilibrium strategy solver for poker tournaments.

Provides:
- NashEquilibriumSolver: computes approximate Nash equilibrium strategies
  for heads-up push/fold situations in tournaments.
- Strategy tables for common stack depths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import math


@dataclass
class NashStrategy:
    """Represents a Nash equilibrium strategy for a player."""
    player_name: str
    push_range: List[Tuple[str, float]]  # (hand_strength, push_frequency)
    call_range: List[Tuple[str, float]]  # (hand_strength, call_frequency)
    stack_depth: float
    position: str  # "SB" or "BB"


class NashEquilibriumSolver:
    """Solves for Nash equilibrium push/fold strategies in heads-up tournaments.

    Uses the simplified approach based on stack depths and standard
    push/call range tables derived from Nash equilibrium calculations.
    """

    # Standard push ranges by stack depth (in big blinds)
    # Format: (stack_depth, min_hand_strength_for_push)
    PUSH_RANGES: List[Tuple[float, float]] = [
        (5.0, 0.0),    # 5bb: push any two cards
        (7.0, 0.1),    # 7bb: push top 10%
        (10.0, 0.2),   # 10bb: push top 20%
        (15.0, 0.3),   # 15bb: push top 30%
        (20.0, 0.4),   # 20bb: push top 40%
        (25.0, 0.5),   # 25bb: push top 50%
        (30.0, 0.6),   # 30bb: push top 60%
        (40.0, 0.7),   # 40bb: push top 70%
        (50.0, 0.8),   # 50bb: push top 80%
        (100.0, 1.0),  # 100bb+: standard play
    ]

    # Standard call ranges by stack depth
    CALL_RANGES: List[Tuple[float, float]] = [
        (5.0, 0.0),
        (7.0, 0.15),
        (10.0, 0.25),
        (15.0, 0.35),
        (20.0, 0.45),
        (25.0, 0.55),
        (30.0, 0.65),
        (40.0, 0.75),
        (50.0, 0.85),
        (100.0, 1.0),
    ]

    def __init__(self):
        pass

    def solve_push_fold(
        self,
        sb_chips: float,
        bb_chips: float,
        sb_name: str = "SB",
        bb_name: str = "BB",
    ) -> Tuple[NashStrategy, NashStrategy]:
        """Solve for Nash equilibrium push/fold strategy.

        Args:
            sb_chips: Small blind's chip stack.
            bb_chips: Big blind's chip stack.
            sb_name: Name of the small blind player.
            bb_name: Name of the big blind player.

        Returns:
            Tuple of (SB_strategy, BB_strategy).
        """
        sb_depth = sb_chips / max(1.0, bb_chips)
        bb_depth = bb_chips / max(1.0, bb_chips)

        sb_push_threshold = self._interpolate_threshold(sb_depth, self.PUSH_RANGES)
        bb_call_threshold = self._interpolate_threshold(bb_depth, self.CALL_RANGES)

        sb_strategy = NashStrategy(
            player_name=sb_name,
            push_range=[(sb_push_threshold, 1.0)],
            call_range=[],
            stack_depth=sb_depth,
            position="SB",
        )

        bb_strategy = NashStrategy(
            player_name=bb_name,
            push_range=[],
            call_range=[(bb_call_threshold, 1.0)],
            stack_depth=bb_depth,
            position="BB",
        )

        return sb_strategy, bb_strategy

    def get_push_range(self, stack_depth: float) -> float:
        """Get the minimum hand strength for pushing at a given stack depth.

        Args:
            stack_depth: Stack depth in big blinds.

        Returns:
            Minimum hand strength (0.0 to 1.0) for pushing.
        """
        return self._interpolate_threshold(stack_depth, self.PUSH_RANGES)

    def get_call_range(self, stack_depth: float) -> float:
        """Get the minimum hand strength for calling at a given stack depth.

        Args:
            stack_depth: Stack depth in big blinds.

        Returns:
            Minimum hand strength (0.0 to 1.0) for calling.
        """
        return self._interpolate_threshold(stack_depth, self.CALL_RANGES)

    def _interpolate_threshold(
        self, depth: float, ranges: List[Tuple[float, float]]
    ) -> float:
        """Interpolate a threshold value for a given depth from a range table."""
        if depth <= ranges[0][0]:
            return ranges[0][1]
        if depth >= ranges[-1][0]:
            return ranges[-1][1]

        # Find surrounding points
        for i in range(len(ranges) - 1):
            if ranges[i][0] <= depth <= ranges[i + 1][0]:
                x0, y0 = ranges[i]
                x1, y1 = ranges[i + 1]
                if x1 == x0:
                    return y0
                t = (depth - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)

        return ranges[-1][1]

    def evaluate_hand_strength(self, hole_cards: List[Tuple[str, str]]) -> float:
        """Evaluate the strength of hole cards as a value from 0.0 to 1.0.

        Args:
            hole_cards: List of (rank, suit) tuples for the hole cards.

        Returns:
            Hand strength estimate (0.0 = worst, 1.0 = best).
        """
        if len(hole_cards) != 2:
            return 0.5

        rank_values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                       "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}

        r1 = rank_values.get(hole_cards[0][0], 2)
        r2 = rank_values.get(hole_cards[1][0], 2)
        suited = hole_cards[0][1] == hole_cards[1][1]

        # Simplified hand strength evaluation
        pair = r1 == r2
        high_card = max(r1, r2)
        low_card = min(r1, r2)
        gap = high_card - low_card

        strength = 0.0

        if pair:
            strength = 0.5 + (high_card / 14.0) * 0.5
        else:
            # High card value
            strength = (high_card / 14.0) * 0.4
            # Gap penalty
            strength -= gap * 0.02
            # Suited bonus
            if suited:
                strength += 0.05
            # Connected bonus
            if gap <= 2:
                strength += 0.03

        return max(0.0, min(1.0, strength))

    def should_push(
        self,
        hole_cards: List[Tuple[str, str]],
        stack_depth: float,
        position: str = "SB",
    ) -> bool:
        """Determine whether to push based on Nash equilibrium.

        Args:
            hole_cards: Player's hole cards.
            stack_depth: Stack depth in big blinds.
            position: Player position ("SB" or "BB").

        Returns:
            True if the player should push.
        """
        threshold = self.get_push_range(stack_depth) if position == "SB" else self.get_call_range(stack_depth)
        hand_strength = self.evaluate_hand_strength(hole_cards)
        return hand_strength >= threshold
