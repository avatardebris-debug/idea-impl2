"""
Arbitrage detection engine.

Core functionality for identifying profitable arbitrage opportunities
across multiple bookmakers and markets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from dfs_arb.core.models import MarketType, OddsEntry


@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity.

    Attributes:
        market_id: Identifier for the market.
        market_type: Type of market (e.g., TWO_SIDED, MLR).
        event_name: Name of the event.
        event_date: Date of the event.
        sport: Sport type.
        total_implied_prob: Sum of implied probabilities across all outcomes.
        profit_pct: Profit percentage from the arbitrage.
        total_stake: Total amount to stake across all outcomes.
        guaranteed_profit: Guaranteed profit amount.
        stake_distribution: Dictionary mapping side to stake amount.
        outcomes: List of (side, bookmaker, decimal_odds) tuples.
    """
    market_id: str
    market_type: MarketType
    event_name: str
    event_date: str
    sport: str
    total_implied_prob: float
    profit_pct: float
    total_stake: float
    guaranteed_profit: float
    stake_distribution: Dict[str, float]
    outcomes: List[Tuple[str, str, float]]

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "market_id": self.market_id,
            "market_type": self.market_type.value,
            "event_name": self.event_name,
            "event_date": self.event_date,
            "sport": self.sport,
            "total_implied_prob": self.total_implied_prob,
            "profit_pct": self.profit_pct,
            "total_stake": self.total_stake,
            "guaranteed_profit": self.guaranteed_profit,
            "stake_distribution": self.stake_distribution,
            "outcomes": self.outcomes,
        }


def _calculate_implied_prob(odds: float) -> float:
    """Calculate implied probability from decimal odds.

    Args:
        odds: Decimal odds value.

    Returns:
        Implied probability as a float.
    """
    return 1.0 / odds


def find_arbitrage(
    entries: List[OddsEntry],
    min_profit_pct: float = 0.0,
) -> Optional[ArbitrageOpportunity]:
    """Find arbitrage opportunities in a list of odds entries.

    Args:
        entries: List of odds entries to analyze.
        min_profit_pct: Minimum profit percentage to consider an opportunity.

    Returns:
        ArbitrageOpportunity if found, None otherwise.
    """
    if not entries:
        return None

    # Group entries by market_id
    markets: Dict[str, List[OddsEntry]] = {}
    for entry in entries:
        if entry.market_id not in markets:
            markets[entry.market_id] = []
        markets[entry.market_id].append(entry)

    best_opportunity: Optional[ArbitrageOpportunity] = None

    for market_id, market_entries in markets.items():
        # Get unique sides in this market
        sides = list(set(e.side for e in market_entries))

        # Determine market type from entries
        market_type = market_entries[0].market_type if market_entries else MarketType.TWO_SIDED

        # Check for three-way markets first (regardless of declared market_type)
        if len(sides) == 3:
            # Three-way market (e.g., home/draw/away)
            # Find best odds for each side
            best_odds: Dict[str, float] = {}
            for side in sides:
                side_entries = [e for e in market_entries if e.side == side]
                if side_entries:
                    best_odds[side] = max(e.decimal_odds or e.odds_value for e in side_entries)

            if len(best_odds) == 3:
                total_implied_prob = sum(1.0 / odds for odds in best_odds.values())
                profit_pct = (1.0 / total_implied_prob - 1.0) * 100

                if profit_pct > min_profit_pct:
                    # Calculate stake distribution
                    total_stake = 100.0  # Normalize to 100
                    stake_distribution = {}
                    for side, odds in best_odds.items():
                        stake_distribution[side] = total_stake / total_implied_prob / odds

                    guaranteed_profit = total_stake / total_implied_prob - total_stake

                    outcomes = [
                        (side, max(e.bookmaker for e in market_entries if e.side == side), odds)
                        for side, odds in best_odds.items()
                    ]

                    opportunity = ArbitrageOpportunity(
                        market_id=market_id,
                        market_type=market_type,
                        event_name=market_entries[0].event_name or "",
                        event_date=market_entries[0].event_date or "",
                        sport=market_entries[0].sport or "",
                        total_implied_prob=total_implied_prob,
                        profit_pct=profit_pct,
                        total_stake=total_stake,
                        guaranteed_profit=guaranteed_profit,
                        stake_distribution=stake_distribution,
                        outcomes=outcomes,
                    )

                    if best_opportunity is None or profit_pct > best_opportunity.profit_pct:
                        best_opportunity = opportunity

        elif len(sides) == 2:
            # Two-sided market (e.g., over/under)
            # Find best odds for each side
            best_odds: Dict[str, float] = {}
            for side in sides:
                side_entries = [e for e in market_entries if e.side == side]
                if side_entries:
                    best_odds[side] = max(e.decimal_odds or e.odds_value for e in side_entries)

            if len(best_odds) == 2:
                total_implied_prob = sum(1.0 / odds for odds in best_odds.values())
                profit_pct = (1.0 / total_implied_prob - 1.0) * 100

                if profit_pct > min_profit_pct:
                    # Calculate stake distribution
                    total_stake = 100.0  # Normalize to 100
                    stake_distribution = {}
                    for side, odds in best_odds.items():
                        stake_distribution[side] = total_stake / total_implied_prob / odds

                    guaranteed_profit = total_stake / total_implied_prob - total_stake

                    outcomes = [
                        (side, max(e.bookmaker for e in market_entries if e.side == side), odds)
                        for side, odds in best_odds.items()
                    ]

                    opportunity = ArbitrageOpportunity(
                        market_id=market_id,
                        market_type=market_type,
                        event_name=market_entries[0].event_name or "",
                        event_date=market_entries[0].event_date or "",
                        sport=market_entries[0].sport or "",
                        total_implied_prob=total_implied_prob,
                        profit_pct=profit_pct,
                        total_stake=total_stake,
                        guaranteed_profit=guaranteed_profit,
                        stake_distribution=stake_distribution,
                        outcomes=outcomes,
                    )

                    if best_opportunity is None or profit_pct > best_opportunity.profit_pct:
                        best_opportunity = opportunity

    return best_opportunity


def find_arbitrage_with_bankroll(
    entries: List[OddsEntry],
    bankroll: float,
    min_profit_pct: float = 0.0,
    max_stake_pct: float = 1.0,
) -> Optional[ArbitrageOpportunity]:
    """Find arbitrage opportunities with bankroll constraints.

    Args:
        entries: List of odds entries to analyze.
        bankroll: Available bankroll.
        min_profit_pct: Minimum profit percentage to consider.
        max_stake_pct: Maximum percentage of bankroll to stake.

    Returns:
        ArbitrageOpportunity if found, None otherwise.
    """
    opportunity = find_arbitrage(entries, min_profit_pct)

    if opportunity is None:
        return None

    # Apply bankroll constraints
    max_stake = bankroll * max_stake_pct
    total_stake = min(opportunity.total_stake, max_stake)

    # Scale stake distribution
    scale_factor = total_stake / opportunity.total_stake
    scaled_stake_distribution = {
        side: stake * scale_factor
        for side, stake in opportunity.stake_distribution.items()
    }

    scaled_guaranteed_profit = opportunity.guaranteed_profit * scale_factor

    return ArbitrageOpportunity(
        market_id=opportunity.market_id,
        market_type=opportunity.market_type,
        event_name=opportunity.event_name,
        event_date=opportunity.event_date,
        sport=opportunity.sport,
        total_implied_prob=opportunity.total_implied_prob,
        profit_pct=opportunity.profit_pct,
        total_stake=total_stake,
        guaranteed_profit=scaled_guaranteed_profit,
        stake_distribution=scaled_stake_distribution,
        outcomes=opportunity.outcomes,
    )
