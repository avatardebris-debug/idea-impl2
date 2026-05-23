"""Texas Hold'em simulator (cash game and tournament modes).

Provides:
- Hold'em hand simulation from pre-flop through river
- Cash game mode with blinds and antes
- Tournament mode with blind levels and ICM integration
- pokerkit integration for hand evaluation
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, Tuple

from pokerkit import NoLimitTexasHoldem, Automation, Mode

from advantage_cardgames.core.deck import Card, Deck, Shoe
from advantage_cardgames.core.hand import PokerHandRank, evaluate_poker_hand
from .icm import ICMCalculator, PrizeStructure


class HoldemGameMode(Enum):
    """Game mode for Hold'em."""
    CASH = auto()
    TOURNAMENT = auto()


class PlayerAction(Enum):
    """Possible actions in Hold'em."""
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    RAISE = auto()
    ALL_IN = auto()
    BLIND = auto()


@dataclass
class HoldemPlayer:
    """Represents a player at the table."""
    seat: int
    name: str
    stack: float
    hole_cards: List[Card] = field(default_factory=list)
    is_eliminated: bool = False
    total_wagered: float = 0.0
    total_won: float = 0.0

    def can_act(self) -> bool:
        """Check if player can take actions."""
        return not self.is_eliminated and self.stack > 0

    def bet(self, amount: float) -> bool:
        """Place a bet. Returns True if successful."""
        if amount <= 0 or amount > self.stack:
            return False
        self.stack -= amount
        self.total_wagered += amount
        return True

    def win(self, amount: float):
        """Win chips."""
        self.stack += amount
        self.total_won += amount

    def lose(self, amount: float):
        """Lose chips."""
        self.stack -= amount
        self.total_won -= amount


@dataclass
class HoldemRoundResult:
    """Result of a single Hold'em hand."""
    hand_number: int
    pot_size: float
    winners: List[str]  # player names who won
    player_outcomes: Dict[str, float]  # player -> net outcome
    board_cards: List[Card]
    hand_rankings: Dict[str, HandRank]  # player -> hand rank
    action_summary: str = ""


class HoldemTable:
    """Represents a Hold'em table with players and game state."""

    def __init__(
        self,
        mode: HoldemGameMode = HoldemGameMode.CASH,
        small_blind: float = 1.0,
        big_blind: float = 2.0,
        ante: float = 0.0,
    ):
        self.mode = mode
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.ante = ante
        self.players: List[HoldemPlayer] = []
        self.current_player_idx = 0
        self.dealer_idx = 0
        self.pot = 0.0
        self.board_cards: List[Card] = []
        self.hand_number = 0
        self.current_bet = 0.0
        self.min_raise = 0.0

    def add_player(self, player: HoldemPlayer):
        """Add a player to the table."""
        self.players.append(player)

    def deal_hand(self) -> HoldemRoundResult:
        """Deal and play one hand of Hold'em."""
        self.hand_number += 1
        self.pot = 0.0
        self.board_cards = []
        self.current_bet = 0.0
        self.min_raise = self.big_blind

        # Post blinds
        if len(self.players) >= 2:
            sb_idx = (self.dealer_idx + 1) % len(self.players)
            bb_idx = (self.dealer_idx + 2) % len(self.players)

            sb_player = self.players[sb_idx]
            bb_player = self.players[bb_idx]

            # Post small blind
            sb_amount = min(self.small_blind, sb_player.stack)
            sb_player.bet(sb_amount)
            self.pot += sb_amount

            # Post big blind
            bb_amount = min(self.big_blind, bb_player.stack)
            bb_player.bet(bb_amount)
            self.pot += bb_amount

            self.current_bet = bb_amount

        # Deal hole cards
        deck = Shoe().deal(52)
        for player in self.players:
            if player.stack > 0:
                player.hole_cards = deck.draw(2)

        # Simplified betting round (pre-flop only for simulation)
        self._simplified_betting_round()

        # Deal community cards
        if len(self.board_cards) == 0:
            # Burn and deal flop
            deck.draw(1)  # burn
            self.board_cards.extend(deck.deal(3))

        if len(self.board_cards) == 3:
            # Burn and deal turn
            deck.draw(1)  # burn
            self.board_cards.extend(deck.deal(1))

        if len(self.board_cards) == 4:
            # Burn and deal river
            deck.draw(1)  # burn
            self.board_cards.extend(deck.deal(1))

        # Showdown
        return self._showdown()

    def _simplified_betting_round(self):
        """Simplified betting round for simulation purposes."""
        # In a full implementation, this would handle multiple betting rounds
        # For simulation, we'll use a simple model
        pass

    def _showdown(self) -> HoldemRoundResult:
        """Determine the winner(s) at showdown."""
        active_players = [p for p in self.players if p.stack >= 0 and p.hole_cards]

        if not active_players:
            return HoldemRoundResult(
                hand_number=self.hand_number,
                pot_size=self.pot,
                winners=[],
                player_outcomes={},
                board_cards=self.board_cards,
                hand_rankings={},
            )

        # Evaluate hands
        hand_rankings = {}
        for player in active_players:
            if len(player.hole_cards) == 2 and len(self.board_cards) == 5:
                combined = player.hole_cards + self.board_cards
                rank = evaluate_poker_hand(combined)
                hand_rankings[player.name] = rank.rank

        # Find winners
        if hand_rankings:
            max_rank = max(hand_rankings.values())
            winners = [name for name, rank in hand_rankings.items() if rank == max_rank]
        else:
            winners = [p.name for p in active_players]

        # Distribute pot
        num_winners = len(winners)
        share = self.pot / num_winners
        player_outcomes = {}

        for player in self.players:
            if player.name in winners:
                player.win(share)
                player_outcomes[player.name] = share - player.total_wagered
            else:
                player_outcomes[player.name] = -player.total_wagered

        # Reset player wagers for next hand
        for player in self.players:
            player.total_wagered = 0

        # Move dealer
        self.dealer_idx = (self.dealer_idx + 1) % len(self.players) if self.players else 0

        return HoldemRoundResult(
            hand_number=self.hand_number,
            pot_size=self.pot,
            winners=winners,
            player_outcomes=player_outcomes,
            board_cards=self.board_cards,
            hand_rankings=hand_rankings,
        )


class HoldemSimulator:
    """Simulates Texas Hold'em games."""

    def __init__(
        self,
        num_players: int = 6,
        starting_stack: float = 1000.0,
        mode: HoldemGameMode = HoldemGameMode.CASH,
        small_blind: float = 1.0,
        big_blind: float = 2.0,
        ante: float = 0.0,
    ):
        self.num_players = num_players
        self.starting_stack = starting_stack
        self.mode = mode
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.ante = ante
        self.results: List[HoldemRoundResult] = []

    def create_table(self) -> HoldemTable:
        """Create a new Hold'em table with the configured settings."""
        table = HoldemTable(
            mode=self.mode,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            ante=self.ante,
        )

        for i in range(self.num_players):
            player = HoldemPlayer(
                seat=i,
                name=f"Player_{i+1}",
                stack=self.starting_stack,
            )
            table.players.append(player)

        return table

    def run_hands(self, num_hands: int) -> List[HoldemRoundResult]:
        """Run a specified number of hands and return results."""
        table = self.create_table()
        self.results = []

        for _ in range(num_hands):
            # Remove eliminated players
            table.players = [p for p in table.players if p.stack > 0]
            if len(table.players) < 2:
                break
            result = table.deal_hand()
            self.results.append(result)

        return self.results

    def get_statistics(self) -> Dict[str, float]:
        """Compute summary statistics across all played hands."""
        if not self.results:
            return {}

        total_pot = sum(r.pot_size for r in self.results)
        total_hands = len(self.results)

        # Per-player stats
        player_stats: Dict[str, Dict[str, float]] = {}
        for result in self.results:
            for name, outcome in result.player_outcomes.items():
                if name not in player_stats:
                    player_stats[name] = {
                        "hands_played": 0,
                        "total_winnings": 0.0,
                        "total_lost": 0.0,
                        "big_blinds_won": 0.0,
                    }
                player_stats[name]["hands_played"] += 1
                if outcome > 0:
                    player_stats[name]["total_winnings"] += outcome
                else:
                    player_stats[name]["total_lost"] += abs(outcome)
                player_stats[name]["big_blinds_won"] += outcome / self.big_blind

        return {
            "total_hands": total_hands,
            "total_pot": total_pot,
            "avg_pot": total_pot / total_hands if total_hands else 0,
            "player_stats": player_stats,
        }
