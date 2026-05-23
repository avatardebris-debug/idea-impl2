"""Simulators module for advantage card games.

This module provides game simulators for testing and training:
- BlackjackGame: Complete blackjack game simulation
- BlackjackResult: Enum for round outcomes
- SimulatorStats: Statistics tracking for simulations
- VideoPokerGame: Video poker simulator with multiple variants
- Paytable: Video poker paytable configuration
- OptimalStrategyCalculator: Exhaustive enumeration strategy calculator
"""

from advantage_cardgames.simulators.blackjack import BlackjackGame, BlackjackResult, SimulatorStats
from advantage_cardgames.simulators.video_poker import (
    ACES_AND_FACES_PAYTABLE,
    BONUS_POKER_PAYTABLE,
    DOUBLE_BONUS_PAYTABLE,
    DEUCES_WILD_PAYTABLE,
    JACKS_OR_BETTER_9_6,
    HoldDecision,
    HoldStatus,
    OptimalStrategyCalculator,
    Paytable,
    VARIANT_PAYTABLES,
    VideoPokerGame,
    VideoPokerResult,
)

__all__ = [
    # Blackjack
    "BlackjackGame",
    "BlackjackResult",
    "SimulatorStats",
    # Video Poker
    "VideoPokerGame",
    "VideoPokerResult",
    "Paytable",
    "HoldDecision",
    "HoldStatus",
    "OptimalStrategyCalculator",
    "VARIANT_PAYTABLES",
    # Predefined paytables
    "JACKS_OR_BETTER_9_6",
    "DEUCES_WILD_PAYTABLE",
    "BONUS_POKER_PAYTABLE",
    "DOUBLE_BONUS_PAYTABLE",
    "ACES_AND_FACES_PAYTABLE",
]
