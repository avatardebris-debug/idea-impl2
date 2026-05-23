"""Hand class with blackjack and poker hand evaluation.

Provides:
- Hand: manages a collection of cards with blackjack-specific evaluation
  (soft/hard totals, bust detection, blackjack detection, push/win/loss).
- PokerHandEvaluator: evaluates poker hands (5+ cards) for ranking
  (pairs, two pair, three of a kind, straight, flush, full house,
   four of a kind, straight flush, royal flush).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from advantage_cardgames.core.deck import Card


class HandType(Enum):
    """Types of blackjack hands."""
    HARD = "HARD"
    SOFT = "SOFT"
    PAIR = "PAIR"


class Outcome(Enum):
    """Possible outcomes of a blackjack hand."""
    BLACKJACK = "BLACKJACK"
    WIN = "WIN"
    PUSH = "PUSH"
    LOSS = "LOSS"
    BUST = "BUST"
    FOLD = "FOLD"  # surrendered


# ---------------------------------------------------------------------------
# Poker hand ranking
# ---------------------------------------------------------------------------

class PokerHandRank(Enum):
    """Rank of a poker hand, from lowest to highest."""
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


@dataclass(frozen=True)
class PokerHandResult:
    """Result of evaluating a poker hand.

    Attributes:
        rank: The poker hand rank.
        rank_value: Numeric value for comparison (higher is better).
        kickers: Tie-breaking card ranks in descending order.
        description: Human-readable description (e.g. "Full House, Kings over Fives").
    """
    rank: PokerHandRank
    rank_value: int
    kickers: Tuple[int, ...]
    description: str

    def __lt__(self, other: "PokerHandResult") -> bool:
        if self.rank_value != other.rank_value:
            return self.rank_value < other.rank_value
        return self.kickers < other.kickers

    def __le__(self, other: "PokerHandResult") -> bool:
        return self == other or self < other

    def __gt__(self, other: "PokerHandResult") -> bool:
        if self.rank_value != other.rank_value:
            return self.rank_value > other.rank_value
        return self.kickers > other.kickers

    def __ge__(self, other: "PokerHandResult") -> bool:
        return self == other or self > other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PokerHandResult):
            return False
        return self.rank_value == other.rank_value and self.kickers == other.kickers


# Rank of each card for poker purposes (Ace is high = 14, low = 1 in wheel straights)
_RANK_MAP: dict[str, int] = {}
for i, r in enumerate(["2", "3", "4", "5", "6", "7", "8", "9", "10",
                        "J", "Q", "K", "A"]):
    _RANK_MAP[r] = i + 2  # 2..14


def _rank_value(card: Card) -> int:
    """Return numeric rank for a card (2-14)."""
    return _RANK_MAP.get(card.rank.name, 2)


def _is_flush(cards: List[Card]) -> bool:
    """Check if all cards share the same suit."""
    if len(cards) < 5:
        return False
    suit = cards[0].suit
    return all(c.suit == suit for c in cards)


def _is_straight(ranks: List[int]) -> Tuple[bool, List[int]]:
    """Check if ranks form a straight. Returns (is_straight, sorted_ranks_desc).

    Handles wheel straight (A-2-3-4-5) where Ace is low.
    """
    unique_ranks = sorted(set(ranks), reverse=True)
    if len(unique_ranks) < 5:
        return False, []

    # Normal straight check
    for i in range(len(unique_ranks) - 4):
        window = unique_ranks[i:i + 5]
        if window[0] - window[4] == 4:
            return True, window

    # Wheel straight: A-2-3-4-5 (ranks 14,2,3,4,5)
    if 14 in unique_ranks and 2 in unique_ranks and 3 in unique_ranks and 4 in unique_ranks and 5 in unique_ranks:
        return True, [5, 4, 3, 2, 1]

    return False, []


def _describe_hand(rank: PokerHandRank, kickers: Tuple[int, ...]) -> str:
    """Create a human-readable description of a poker hand."""
    _REVERSE_RANK: dict[int, str] = {
        14: "A", 13: "K", 12: "Q", 11: "J", 10: "10", 9: "9",
        8: "8", 7: "7", 6: "6", 5: "5", 4: "4", 3: "3", 2: "2",
    }

    rank_names = {
        PokerHandRank.HIGH_CARD: "High Card",
        PokerHandRank.ONE_PAIR: "Pair",
        PokerHandRank.TWO_PAIR: "Two Pair",
        PokerHandRank.THREE_OF_A_KIND: "Three of a Kind",
        PokerHandRank.STRAIGHT: "Straight",
        PokerHandRank.FLUSH: "Flush",
        PokerHandRank.FULL_HOUSE: "Full House",
        PokerHandRank.FOUR_OF_A_KIND: "Four of a Kind",
        PokerHandRank.STRAIGHT_FLUSH: "Straight Flush",
        PokerHandRank.ROYAL_FLUSH: "Royal Flush",
    }

    base = rank_names.get(rank, "Unknown")
    if kickers:
        kicker_strs = [_REVERSE_RANK.get(k, str(k)) for k in kickers]
        return f"{base}, {', '.join(kicker_strs)}"
    return base


def evaluate_poker_hand(cards: List[Card]) -> PokerHandResult:
    """Evaluate a 5+ card poker hand and return the best 5-card result.

    Uses exhaustive enumeration of all 5-card subsets to find the best hand.
    """
    if len(cards) < 5:
        # Not enough cards — return high card
        ranked = sorted([_rank_value(c) for c in cards], reverse=True)
        return PokerHandResult(
            rank=PokerHandRank.HIGH_CARD,
            rank_value=1,
            kickers=tuple(ranked),
            description=_describe_hand(PokerHandRank.HIGH_CARD, tuple(ranked)),
        )

    # For 7-card hands (like Stud), enumerate all 5-card subsets
    from itertools import combinations
    best: Optional[PokerHandResult] = None

    for subset in combinations(cards, 5):
        result = _evaluate_five_card(list(subset))
        if best is None or result > best:
            best = result

    return best if best else PokerHandResult(
        rank=PokerHandRank.HIGH_CARD,
        rank_value=1,
        kickers=tuple(sorted([_rank_value(c) for c in cards], reverse=True)),
        description="High Card",
    )


def _evaluate_five_card(cards: List[Card]) -> PokerHandResult:
    """Evaluate exactly 5 cards."""
    ranks = [_rank_value(c) for c in cards]
    suits = [c.suit for c in cards]

    is_flush = _is_flush(cards)
    is_straight, straight_ranks = _is_straight(ranks)

    rank_counts = Counter(ranks)
    most_common = rank_counts.most_common()
    groups = [count for _, count in most_common]

    # Royal flush: A-K-Q-J-10 of same suit
    if is_flush and is_straight and straight_ranks == [14, 13, 12, 11, 10]:
        return PokerHandResult(
            rank=PokerHandRank.ROYAL_FLUSH,
            rank_value=10,
            kickers=tuple(straight_ranks),
            description=_describe_hand(PokerHandRank.ROYAL_FLUSH, tuple(straight_ranks)),
        )

    # Straight flush
    if is_flush and is_straight:
        return PokerHandResult(
            rank=PokerHandRank.STRAIGHT_FLUSH,
            rank_value=9,
            kickers=tuple(straight_ranks),
            description=_describe_hand(PokerHandRank.STRAIGHT_FLUSH, tuple(straight_ranks)),
        )

    # Four of a kind
    if groups == [4, 1]:
        quad_rank = [r for r, c in rank_counts.items() if c == 4][0]
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return PokerHandResult(
            rank=PokerHandRank.FOUR_OF_A_KIND,
            rank_value=8,
            kickers=(quad_rank, kicker),
            description=_describe_hand(PokerHandRank.FOUR_OF_A_KIND, (quad_rank, kicker)),
        )

    # Full house
    if groups == [3, 2]:
        trip_rank = [r for r, c in rank_counts.items() if c == 3][0]
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        return PokerHandResult(
            rank=PokerHandRank.FULL_HOUSE,
            rank_value=7,
            kickers=(trip_rank, pair_rank),
            description=_describe_hand(PokerHandRank.FULL_HOUSE, (trip_rank, pair_rank)),
        )

    # Flush
    if is_flush:
        return PokerHandResult(
            rank=PokerHandRank.FLUSH,
            rank_value=6,
            kickers=tuple(sorted(ranks, reverse=True)),
            description=_describe_hand(PokerHandRank.FLUSH, tuple(sorted(ranks, reverse=True))),
        )

    # Straight
    if is_straight:
        return PokerHandResult(
            rank=PokerHandRank.STRAIGHT,
            rank_value=5,
            kickers=tuple(straight_ranks),
            description=_describe_hand(PokerHandRank.STRAIGHT, tuple(straight_ranks)),
        )

    # Three of a kind
    if groups == [3, 1, 1]:
        trip_rank = [r for r, c in rank_counts.items() if c == 3][0]
        kickers = tuple(sorted([r for r, c in rank_counts.items() if c == 1], reverse=True))
        return PokerHandResult(
            rank=PokerHandRank.THREE_OF_A_KIND,
            rank_value=4,
            kickers=(trip_rank,) + kickers,
            description=_describe_hand(PokerHandRank.THREE_OF_A_KIND, (trip_rank,) + kickers),
        )

    # Two pair
    if groups == [2, 2, 1]:
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return PokerHandResult(
            rank=PokerHandRank.TWO_PAIR,
            rank_value=3,
            kickers=tuple(pairs + [kicker]),
            description=_describe_hand(PokerHandRank.TWO_PAIR, tuple(pairs + [kicker])),
        )

    # One pair
    if groups == [2, 1, 1, 1]:
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = tuple(sorted([r for r, c in rank_counts.items() if c == 1], reverse=True))
        return PokerHandResult(
            rank=PokerHandRank.ONE_PAIR,
            rank_value=2,
            kickers=(pair_rank,) + kickers,
            description=_describe_hand(PokerHandRank.ONE_PAIR, (pair_rank,) + kickers),
        )

    # High card
    return PokerHandResult(
        rank=PokerHandRank.HIGH_CARD,
        rank_value=1,
        kickers=tuple(sorted(ranks, reverse=True)),
        description=_describe_hand(PokerHandRank.HIGH_CARD, tuple(sorted(ranks, reverse=True))),
    )


# ---------------------------------------------------------------------------
# Blackjack Hand (unchanged core)
# ---------------------------------------------------------------------------

@dataclass
class Hand:
    """A blackjack hand with card management and evaluation."""

    cards: List[Card] = field(default_factory=list)
    is_split: bool = False
    is_doubled: bool = False
    is_surrendered: bool = False
    is_finished: bool = False

    def add_card(self, card: Card) -> None:
        """Add a card to the hand."""
        self.cards.append(card)

    def remove_card(self, card: Card) -> None:
        """Remove a specific card from the hand."""
        if card in self.cards:
            self.cards.remove(card)

    def clear(self) -> None:
        """Clear all cards and reset state."""
        self.cards.clear()
        self.is_split = False
        self.is_doubled = False
        self.is_surrendered = False
        self.is_finished = False

    @property
    def is_empty(self) -> bool:
        return len(self.cards) == 0

    @property
    def is_blackjack(self) -> bool:
        """Check if hand is a natural blackjack (2 cards totaling 21)."""
        return (
            len(self.cards) == 2
            and self.blackjack_total == 21
        )

    @property
    def is_bust(self) -> bool:
        """Check if hand has busted (hard total > 21)."""
        return self.hard_total > 21

    @property
    def is_soft(self) -> bool:
        """Check if hand is a soft hand (contains an ace counted as 11)."""
        return self.soft_total == self.hard_total and self._has_ace_as_11

    @property
    def hard_total(self) -> int:
        """Calculate the hard total of the hand (aces count as 1)."""
        total = 0
        aces = 0

        for card in self.cards:
            if card.rank.is_ace:
                aces += 1
                total += 1
            elif card.rank.is_face:
                total += 10
            else:
                total += card.rank.value

        return total

    @property
    def soft_total(self) -> int:
        """Calculate the soft total of the hand (aces count as 11 if beneficial)."""
        total = 0
        aces = 0

        for card in self.cards:
            if card.rank.is_ace:
                aces += 1
                total += 1
            elif card.rank.is_face:
                total += 10
            else:
                total += card.rank.value

        # Add 10 for each ace if it doesn't cause bust
        while aces > 0 and total + 10 <= 21:
            total += 10
            aces -= 1

        return total

    @property
    def blackjack_total(self) -> int:
        """Calculate the best total for blackjack purposes."""
        if self.is_blackjack:
            return 21
        return self.soft_total

    @property
    def _has_ace_as_11(self) -> bool:
        """Check if hand has an ace counted as 11."""
        total = 0
        aces = 0

        for card in self.cards:
            if card.rank.is_ace:
                aces += 1
                total += 1
            elif card.rank.is_face:
                total += 10
            else:
                total += card.rank.value

        return aces > 0 and total + 10 <= 21

    @property
    def hand_type(self) -> HandType:
        """Determine the type of hand."""
        if len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank:
            return HandType.PAIR
        elif self.is_soft:
            return HandType.SOFT
        else:
            return HandType.HARD

    @property
    def total(self) -> int:
        """Get the best total for the hand."""
        if self.is_bust:
            return self.hard_total
        return self.soft_total

    @total.setter
    def total(self, value: int) -> None:
        """Set the total (for testing purposes)."""
        self._total = value

    @property
    def stood(self) -> bool:
        """Check if player has stood."""
        return self.is_finished

    @property
    def double(self) -> bool:
        """Check if hand is doubled."""
        return self.is_doubled

    @property
    def blackjack(self) -> bool:
        """Check if hand is blackjack."""
        return self.is_blackjack

    @property
    def can_split(self) -> bool:
        """Check if hand can be split (has exactly 2 cards of same rank)."""
        return (
            len(self.cards) == 2 and
            self.cards[0].rank == self.cards[1].rank and
            not self.is_split
        )

    def to_dict(self) -> dict:
        """Convert hand to dictionary."""
        return {
            "cards": [card.to_dict() for card in self.cards],
            "is_split": self.is_split,
            "is_doubled": self.is_doubled,
            "is_surrendered": self.is_surrendered,
            "is_finished": self.is_finished,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Hand":
        """Create hand from dictionary."""
        from advantage_cardgames.core.deck import Card
        hand = cls(
            cards=[Card.from_dict(card_dict) for card_dict in d["cards"]],
            is_split=d["is_split"],
            is_doubled=d["is_doubled"],
            is_surrendered=d["is_surrendered"],
            is_finished=d["is_finished"],
        )
        return hand

    def __str__(self) -> str:
        cards_str = ", ".join(str(card) for card in self.cards)
        return f"Hand([{cards_str}])"

    def __repr__(self) -> str:
        return f"Hand(cards={self.cards}, is_split={self.is_split})"

    def __len__(self) -> int:
        return len(self.cards)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return False
        return (
            self.cards == other.cards and
            self.is_split == other.is_split and
            self.is_doubled == other.is_doubled
        )

    def copy(self) -> "Hand":
        """Create a copy of this hand."""
        new_hand = Hand(
            cards=self.cards.copy(),
            is_split=self.is_split,
            is_doubled=self.is_doubled,
            is_surrendered=self.is_surrendered,
            is_finished=self.is_finished,
        )
        return new_hand
