"""
Promotional offer evaluation.

Provides functionality to evaluate promotional offers from bookmakers
and determine their expected value for arbitrage strategies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from dfs_arb.core.models import OddsEntry, PromoOffer as PromoOfferModel


@dataclass
class PromoEvaluation:
    """Result of evaluating a promotional offer.

    Attributes:
        promo: The promotional offer evaluated.
        expected_value: Expected value of the promotion.
        max_stake: Maximum stake to maximize expected value.
        is_profitable: Whether the promotion is profitable.
        details: Additional details about the evaluation.
    """
    promo: PromoOfferModel
    expected_value: float
    max_stake: float
    is_profitable: bool
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "promo": self.promo.to_dict(),
            "expected_value": self.expected_value,
            "max_stake": self.max_stake,
            "is_profitable": self.is_profitable,
            "details": self.details,
        }


def evaluate_promo(
    promo: PromoOfferModel,
    over_entry: OddsEntry,
    under_entry: OddsEntry,
) -> PromoEvaluation:
    """Evaluate a promotional offer for expected value.

    Args:
        promo: The promotional offer to evaluate.
        over_entry: Odds entry for the over side.
        under_entry: Odds entry for the under side.

    Returns:
        PromoEvaluation with expected value and details.
    """
    # Calculate implied probabilities
    over_prob = 1.0 / over_entry.decimal_odds
    under_prob = 1.0 / under_entry.decimal_odds

    # Calculate true probabilities (normalized)
    total_prob = over_prob + under_prob
    true_over_prob = over_prob / total_prob
    true_under_prob = under_prob / total_prob

    # Calculate expected value based on promotion type
    expected_value = 0.0
    max_stake = 0.0

    if promo.promo_type == "RISK_FREE_BET":
        # Risk-free bet: get stake back if lose
        # EV = (win_prob * odds * stake) + (lose_prob * -stake * (1 - refund_pct))
        # Simplified: EV = stake * (win_prob * (odds - 1) + lose_prob * refund_pct)
        win_prob = true_over_prob if promo.side == "over" else true_under_prob
        lose_prob = 1.0 - win_prob

        # Use the better odds for calculation
        best_odds = max(over_entry.decimal_odds, under_entry.decimal_odds)
        odds = best_odds

        # Calculate EV per unit stake
        ev_per_stake = win_prob * (odds - 1) + lose_prob * promo.refund_pct

        # Find max stake where EV is positive
        if ev_per_stake > 0:
            expected_value = ev_per_stake * promo.max_stake
            max_stake = promo.max_stake
        else:
            expected_value = 0.0
            max_stake = 0.0

    elif promo.promo_type == "BONUS_BET":
        # Bonus bet: get winnings only if win (no stake return)
        # EV = win_prob * (odds - 1) * stake
        win_prob = true_over_prob if promo.side == "over" else true_under_prob

        # Use the better odds for calculation
        best_odds = max(over_entry.decimal_odds, under_entry.decimal_odds)
        odds = best_odds

        # Calculate EV per unit stake
        ev_per_stake = win_prob * (odds - 1)

        # Bonus bets typically have lower value due to restrictions
        bonus_multiplier = promo.refund_pct  # Use refund_pct as multiplier for bonus value

        expected_value = ev_per_stake * promo.max_stake * bonus_multiplier
        max_stake = promo.max_stake

    elif promo.promo_type == "MATCHED_BET":
        # Matched bet: get stake matched if lose
        # Similar to risk-free bet but with different mechanics
        win_prob = true_over_prob if promo.side == "over" else true_under_prob
        lose_prob = 1.0 - win_prob

        best_odds = max(over_entry.decimal_odds, under_entry.decimal_odds)
        odds = best_odds

        ev_per_stake = win_prob * (odds - 1) + lose_prob * promo.refund_pct

        if ev_per_stake > 0:
            expected_value = ev_per_stake * promo.max_stake
            max_stake = promo.max_stake
        else:
            expected_value = 0.0
            max_stake = 0.0

    else:
        # Unknown promo type
        expected_value = 0.0
        max_stake = 0.0

    return PromoEvaluation(
        promo=promo,
        expected_value=expected_value,
        max_stake=max_stake,
        is_profitable=expected_value > 0,
        details={
            "true_over_prob": true_over_prob,
            "true_under_prob": true_under_prob,
            "over_odds": over_entry.decimal_odds,
            "under_odds": under_entry.decimal_odds,
        },
    )


def evaluate_promo_with_entries(
    promo: PromoOfferModel,
    entries: List[OddsEntry],
) -> PromoEvaluation:
    """Evaluate a promotional offer using a list of entries.

    Args:
        promo: The promotional offer to evaluate.
        entries: List of odds entries containing over and under entries.

    Returns:
        PromoEvaluation with expected value and details.
    """
    # Find over and under entries
    over_entry = None
    under_entry = None

    for entry in entries:
        if entry.side == "over":
            over_entry = entry
        elif entry.side == "under":
            under_entry = entry

    if over_entry is None or under_entry is None:
        return PromoEvaluation(
            promo=promo,
            expected_value=0.0,
            max_stake=0.0,
            is_profitable=False,
            details={"error": "Missing over or under entry"},
        )

    return evaluate_promo(promo, over_entry, under_entry)
