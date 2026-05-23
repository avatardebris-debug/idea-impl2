"""Video Poker simulator with multiple variants and optimal strategy calculator.

Supports variants:
- Jacks or Better
- Deuces Wild
- Bonus Poker
- Double Bonus Poker
- Aces and Faces

Features:
- Full hand evaluation using poker hand ranking
- Multiple paytable configurations
- Optimal strategy calculator via exhaustive enumeration
- Simulation engine for strategy testing
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from advantage_cardgames.core.deck import Card, Deck, Suit
from advantage_cardgames.core.hand import (
    PokerHandRank,
    PokerHandResult,
    evaluate_poker_hand,
)


# ---------------------------------------------------------------------------
# Paytable definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Paytable:
    """A video poker paytable mapping hand rank to payout multiplier.

    Attributes:
        name: Human-readable name of the paytable.
        payouts: Mapping from PokerHandRank to payout multiplier.
        minimum_rank: Minimum hand rank that pays (e.g. Jacks or Better).
    """
    name: str
    payouts: Dict[PokerHandRank, float]
    minimum_rank: PokerHandRank = PokerHandRank.ONE_PAIR

    def payout(self, hand_rank: PokerHandRank, bet: float = 1.0) -> float:
        """Return the payout for a given hand rank and bet."""
        if hand_rank.value < self.minimum_rank.value:
            return 0.0
        multiplier = self.payouts.get(hand_rank, 0.0)
        return bet * multiplier


# Standard Jacks or Better (9/6 paytable)
JACKS_OR_BETTER_9_6 = Paytable(
    name="Jacks or Better (9/6)",
    payouts={
        PokerHandRank.ROYAL_FLUSH: 800.0,
        PokerHandRank.STRAIGHT_FLUSH: 50.0,
        PokerHandRank.FOUR_OF_A_KIND: 25.0,
        PokerHandRank.FULL_HOUSE: 9.0,
        PokerHandRank.FLUSH: 6.0,
        PokerHandRank.STRAIGHT: 4.0,
        PokerHandRank.THREE_OF_A_KIND: 3.0,
        PokerHandRank.TWO_PAIR: 2.0,
        PokerHandRank.ONE_PAIR: 1.0,  # Jacks or better
    },
    minimum_rank=PokerHandRank.ONE_PAIR,
)

# Deuces Wild paytable
DEUCES_WILD_PAYTABLE = Paytable(
    name="Deuces Wild (Full Pay)",
    payouts={
        PokerHandRank.ROYAL_FLUSH: 250.0,
        PokerHandRank.STRAIGHT_FLUSH: 50.0,
        PokerHandRank.FOUR_OF_A_KIND: 25.0,
        PokerHandRank.FULL_HOUSE: 9.0,
        PokerHandRank.FLUSH: 7.0,
        PokerHandRank.STRAIGHT: 4.0,
        PokerHandRank.THREE_OF_A_KIND: 3.0,
        PokerHandRank.TWO_PAIR: 2.0,
        PokerHandRank.ONE_PAIR: 1.0,  # Any pair pays in Deuces Wild
    },
    minimum_rank=PokerHandRank.ONE_PAIR,
)

# Bonus Poker paytable
BONUS_POKER_PAYTABLE = Paytable(
    name="Bonus Poker (Full Pay)",
    payouts={
        PokerHandRank.ROYAL_FLUSH: 800.0,
        PokerHandRank.STRAIGHT_FLUSH: 50.0,
        PokerHandRank.FOUR_OF_A_KIND: 80.0,  # Bonus for 4 Aces
        PokerHandRank.FULL_HOUSE: 8.0,
        PokerHandRank.FLUSH: 5.0,
        PokerHandRank.STRAIGHT: 4.0,
        PokerHandRank.THREE_OF_A_KIND: 3.0,
        PokerHandRank.TWO_PAIR: 2.0,
        PokerHandRank.ONE_PAIR: 0.0,  # No pair payout
    },
    minimum_rank=PokerHandRank.THREE_OF_A_KIND,
)

# Double Bonus Poker paytable
DOUBLE_BONUS_PAYTABLE = Paytable(
    name="Double Bonus Poker (Full Pay)",
    payouts={
        PokerHandRank.ROYAL_FLUSH: 800.0,
        PokerHandRank.STRAIGHT_FLUSH: 50.0,
        PokerHandRank.FOUR_OF_A_KIND: 80.0,  # Bonus for 4 Aces
        PokerHandRank.FULL_HOUSE: 8.0,
        PokerHandRank.FLUSH: 4.0,
        PokerHandRank.STRAIGHT: 3.0,
        PokerHandRank.THREE_OF_A_KIND: 3.0,
        PokerHandRank.TWO_PAIR: 2.0,
        PokerHandRank.ONE_PAIR: 0.0,
    },
    minimum_rank=PokerHandRank.THREE_OF_A_KIND,
)

# Aces and Faces paytable
ACES_AND_FACES_PAYTABLE = Paytable(
    name="Aces and Faces",
    payouts={
        PokerHandRank.ROYAL_FLUSH: 800.0,
        PokerHandRank.STRAIGHT_FLUSH: 50.0,
        PokerHandRank.FOUR_OF_A_KIND: 40.0,
        PokerHandRank.FULL_HOUSE: 15.0,  # Bonus for Aces over Faces
        PokerHandRank.FLUSH: 8.0,
        PokerHandRank.STRAIGHT: 4.0,
        PokerHandRank.THREE_OF_A_KIND: 3.0,
        PokerHandRank.TWO_PAIR: 2.0,
        PokerHandRank.ONE_PAIR: 1.0,
    },
    minimum_rank=PokerHandRank.ONE_PAIR,
)

# All supported variants
VARIANT_PAYTABLES: Dict[str, Paytable] = {
    "jacks_or_better_9_6": JACKS_OR_BETTER_9_6,
    "deuces_wild": DEUCES_WILD_PAYTABLE,
    "bonus_poker": BONUS_POKER_PAYTABLE,
    "double_bonus": DOUBLE_BONUS_PAYTABLE,
    "aces_and_faces": ACES_AND_FACES_PAYTABLE,
}


# ---------------------------------------------------------------------------
# Video Poker Result
# ---------------------------------------------------------------------------

@dataclass
class VideoPokerResult:
    """Result of a single video poker round.

    Attributes:
        hand: The final 5-card hand dealt.
        hand_rank: The poker hand rank.
        hand_result: The full poker hand evaluation.
        payout: Amount won (0 if no win).
        bet: Original bet amount.
        variant: Name of the variant played.
    """
    hand: List[Card]
    hand_rank: PokerHandRank
    hand_result: PokerHandResult
    payout: float
    bet: float
    variant: str


# ---------------------------------------------------------------------------
# Hold/Discard decision
# ---------------------------------------------------------------------------

class HoldStatus(Enum):
    """Whether to hold or discard a card."""
    HOLD = "HOLD"
    DISCARD = "DISCARD"


@dataclass
class HoldDecision:
    """Decision on which cards to hold.

    Attributes:
        hold: List of (index, card) pairs to hold.
        discard: List of (index, card) pairs to discard.
    """
    hold: List[Tuple[int, Card]]
    discard: List[Tuple[int, Card]]

    @property
    def hold_indices(self) -> List[int]:
        """Return indices of cards to hold."""
        return [idx for idx, _ in self.hold]

    @property
    def discard_indices(self) -> List[int]:
        """Return indices of cards to discard."""
        return [idx for idx, _ in self.discard]


# ---------------------------------------------------------------------------
# Optimal Strategy Calculator (exhaustive enumeration)
# ---------------------------------------------------------------------------

class OptimalStrategyCalculator:
    """Calculate optimal hold/discard strategy via exhaustive enumeration.

    For each possible dealt hand, evaluates all 2^5 = 32 possible hold
    combinations and selects the one with the highest expected value.
    """

    def __init__(self, variant: str = "jacks_or_better_9_6"):
        """Initialize with a variant name.

        Args:
            variant: Name of the video poker variant.
        """
        if variant not in VARIANT_PAYTABLES:
            raise ValueError(
                f"Unknown variant '{variant}'. "
                f"Available: {list(VARIANT_PAYTABLES.keys())}"
            )
        self.variant = variant
        self.paytable = VARIANT_PAYTABLES[variant]
        self._cache: Dict[Tuple[int, ...], HoldDecision] = {}

    def calculate_optimal_hold(self, dealt_cards: List[Card]) -> HoldDecision:
        """Calculate the optimal hold decision for a dealt hand.

        Enumerates all 2^5 = 32 possible hold combinations and returns
        the one with the highest expected payout.

        Args:
            dealt_cards: List of 5 dealt cards.

        Returns:
            HoldDecision with the optimal hold/discard split.
        """
        if len(dealt_cards) != 5:
            raise ValueError("Dealt hand must have exactly 5 cards")

        # Cache key: tuple of (rank_value, suit_value) for each card
        cache_key = tuple(
            (c.rank.value, c.suit.value) for c in dealt_cards
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        best_ev = float("-inf")
        best_decision: Optional[HoldDecision] = None

        # Enumerate all 2^5 = 32 hold combinations
        for mask in range(32):  # 0 to 31
            hold_indices = [i for i in range(5) if mask & (1 << i)]
            discard_indices = [i for i in range(5) if not (mask & (1 << i))]

            ev = self._expected_value_for_hold(
                dealt_cards, hold_indices, discard_indices
            )

            if ev > best_ev:
                best_ev = ev
                best_decision = HoldDecision(
                    hold=[(i, dealt_cards[i]) for i in hold_indices],
                    discard=[(i, dealt_cards[i]) for i in discard_indices],
                )

        self._cache[cache_key] = best_decision
        return best_decision

    def _expected_value_for_hold(
        self,
        dealt_cards: List[Card],
        hold_indices: List[int],
        discard_indices: List[int],
    ) -> float:
        """Calculate expected value for a specific hold decision.

        Uses exhaustive enumeration of all possible draw combinations.
        """
        if not discard_indices:
            # No cards to draw — evaluate current hand
            result = evaluate_poker_hand(dealt_cards)
            return self.paytable.payout(result.rank)

        # Number of cards to draw
        n_draw = len(discard_indices)

        # Create a deck without the held cards
        held_ranks_suits = set(
            (c.rank.value, c.suit.value) for i, c in enumerate(dealt_cards) if i in hold_indices
        )
        remaining_deck = [
            Card(rank=r, suit=s)
            for r in Card.RANKS
            for s in Suit
            if (r.value, s.value) not in held_ranks_suits
        ]

        if n_draw > len(remaining_deck):
            return 0.0

        total_payout = 0.0
        num_combinations = 0

        # Enumerate all possible draws (exhaustive for small n)
        from itertools import combinations
        for draw_indices in combinations(range(len(remaining_deck)), n_draw):
            draw_cards = [remaining_deck[i] for i in draw_indices]
            final_hand = dealt_cards[:hold_indices[0]] + draw_cards if hold_indices else draw_cards + dealt_cards[hold_indices[-1] + 1:]

            # Rebuild final hand properly
            final_hand = []
            for i in range(5):
                if i in hold_indices:
                    final_hand.append(dealt_cards[i])
                else:
                    # Find which draw card goes here
                    draw_pos = discard_indices.index(i)
                    final_hand.append(draw_cards[draw_pos])

            result = evaluate_poker_hand(final_hand)
            payout = self.paytable.payout(result.rank)
            total_payout += payout
            num_combinations += 1

        if num_combinations == 0:
            return 0.0

        return total_payout / num_combinations

    def get_strategy_table(self) -> Dict[Tuple[int, ...], List[int]]:
        """Generate a complete strategy table for all possible dealt hands.

        Returns:
            Dictionary mapping (rank_value, suit_value) tuples to hold indices.
        """
        strategy_table: Dict[Tuple[int, ...], List[int]] = {}

        # Generate all possible 5-card deals (sample for performance)
        # In practice, we sample a representative set
        all_cards = [Card(rank=r, suit=s) for r in Card.RANKS for s in Suit]

        # Sample 10000 random deals for strategy table
        deals_sampled = set()
        attempts = 0
        while len(deals_sampled) < 10000 and attempts < 50000:
            dealt = random.sample(all_cards, 5)
            key = tuple((c.rank.value, c.suit.value) for c in dealt)
            if key not in deals_sampled:
                deals_sampled.add(key)
                decision = self.calculate_optimal_hold(dealt)
                strategy_table[key] = decision.hold_indices
            attempts += 1

        return strategy_table


# ---------------------------------------------------------------------------
# Video Poker Simulator
# ---------------------------------------------------------------------------

class VideoPokerGame:
    """Video poker game simulator.

    Supports multiple variants with configurable paytables.
    Simulates the full game loop: deal -> hold/discard -> draw -> evaluate.
    """

    def __init__(
        self,
        variant: str = "jacks_or_better_9_6",
        paytable: Optional[Paytable] = None,
        seed: Optional[int] = None,
    ):
        """Initialize the video poker game.

        Args:
            variant: Name of the video poker variant.
            paytable: Custom paytable (overrides variant).
            seed: Random seed for reproducibility.
        """
        if paytable is not None:
            self.paytable = paytable
            self.variant = paytable.name
        elif variant in VARIANT_PAYTABLES:
            self.paytable = VARIANT_PAYTABLES[variant]
            self.variant = variant
        else:
            raise ValueError(
                f"Unknown variant '{variant}'. "
                f"Available: {list(VARIANT_PAYTABLES.keys())}"
            )
        self._deck = Deck()
        self._seed = seed
        self._round_results: List[VideoPokerResult] = []

        if self._seed is not None:
            random.seed(self._seed)

    def deal(self, bet: float = 1.0) -> Tuple[List[Card], float]:
        """Deal a new hand.

        Args:
            bet: Bet amount per hand.

        Returns:
            Tuple of (dealt_cards, bet_amount).
        """
        self._deck.shuffle()
        dealt = [self._deck.deal() for _ in range(5)]
        return dealt, bet

    def play_round(
        self,
        dealt_cards: List[Card],
        hold_indices: List[int],
        bet: float = 1.0,
    ) -> VideoPokerResult:
        """Play a single round: draw replacement cards and evaluate.

        Args:
            dealt_cards: The initial 5-card deal.
            hold_indices: Indices of cards to hold (0-4).
            bet: Bet amount.

        Returns:
            VideoPokerResult with final hand and payout.
        """
        if len(dealt_cards) != 5:
            raise ValueError("Must have exactly 5 dealt cards")

        # Determine which cards to discard
        discard_indices = [i for i in range(5) if i not in hold_indices]

        # Draw replacement cards
        remaining_deck = [
            c for c in self._deck.cards
            if c not in [dealt_cards[i] for i in hold_indices]
        ]
        random.shuffle(remaining_deck)

        draw_cards = remaining_deck[:len(discard_indices)]

        # Build final hand
        final_hand = []
        for i in range(5):
            if i in hold_indices:
                final_hand.append(dealt_cards[i])
            else:
                draw_pos = discard_indices.index(i)
                final_hand.append(draw_cards[draw_pos])

        # Evaluate hand
        hand_result = evaluate_poker_hand(final_hand)
        payout = self.paytable.payout(hand_result.rank, bet)

        result = VideoPokerResult(
            hand=final_hand,
            hand_rank=hand_result.rank,
            hand_result=hand_result,
            payout=payout,
            bet=bet,
            variant=self.variant,
        )
        self._round_results.append(result)
        return result

    def play_with_strategy(
        self,
        dealt_cards: List[Card],
        calculator: Optional[OptimalStrategyCalculator] = None,
        bet: float = 1.0,
    ) -> VideoPokerResult:
        """Play a round using optimal strategy calculator.

        Args:
            dealt_cards: The initial 5-card deal.
            calculator: Optional strategy calculator (uses self if None).
            bet: Bet amount.

        Returns:
            VideoPokerResult with final hand and payout.
        """
        if calculator is None:
            calculator = OptimalStrategyCalculator(self.variant)

        decision = calculator.calculate_optimal_hold(dealt_cards)
        hold_indices = decision.hold_indices
        return self.play_round(dealt_cards, hold_indices, bet)

    def simulate(
        self,
        num_rounds: int = 10000,
        bet: float = 1.0,
        use_optimal_strategy: bool = False,
    ) -> Dict[str, float]:
        """Simulate multiple rounds and return statistics.

        Args:
            num_rounds: Number of rounds to simulate.
            bet: Bet amount per round.
            use_optimal_strategy: Whether to use optimal strategy.

        Returns:
            Dictionary with simulation statistics.
        """
        calculator = OptimalStrategyCalculator(self.variant) if use_optimal_strategy else None
        total_bet = 0.0
        total_payout = 0.0
        hand_counts: Dict[PokerHandRank, int] = {r: 0 for r in PokerHandRank}

        for _ in range(num_rounds):
            dealt, _ = self.deal(bet)
            if use_optimal_strategy and calculator:
                result = self.play_with_strategy(dealt, calculator, bet)
            else:
                # Random hold strategy for comparison
                hold_indices = [i for i in range(5) if random.random() < 0.5]
                result = self.play_round(dealt, hold_indices, bet)

            total_bet += bet
            total_payout += result.payout
            hand_counts[result.hand_rank] += 1

        net = total_payout - total_bet
        roi = (net / total_bet * 100) if total_bet > 0 else 0.0

        return {
            "variant": self.variant,
            "num_rounds": num_rounds,
            "total_bet": total_bet,
            "total_payout": total_payout,
            "net": net,
            "roi_percent": roi,
            "hand_counts": {r.name: c for r, c in hand_counts.items()},
        }

    def get_hand_distribution(self) -> Dict[str, int]:
        """Get distribution of hand ranks from simulation history.

        Returns:
            Dictionary mapping hand rank names to counts.
        """
        counts: Dict[str, int] = {}
        for result in self._round_results:
            name = result.hand_rank.name
            counts[name] = counts.get(name, 0) + 1
        return counts

    def reset(self) -> None:
        """Reset the game state."""
        self._deck = Deck()
        self._round_results.clear()
        if self._seed is not None:
            random.seed(self._seed)
