"""
Arbitrage engine for detecting and evaluating betting opportunities.

Core module providing the ArbEngine class that orchestrates arbitrage
detection, odds analysis, and promotional offer evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from dfs_arb.core.arbitrage import find_arbitrage, find_arbitrage_with_bankroll
from dfs_arb.core.models import MarketType, OddsEntry
from dfs_arb.core.promos import PromoOffer, PromoEvaluation


@dataclass
class ArbEngine:
    """Main arbitrage engine class.

    Orchestrates the detection and evaluation of arbitrage opportunities
    across multiple bookmakers and markets.

    Attributes:
        entries: List of odds entries to analyze.
        bankroll: Available bankroll for betting.
        min_profit_pct: Minimum profit percentage to consider an opportunity.
        max_stake_pct: Maximum percentage of bankroll to stake.
        promotions: List of promotional offers to evaluate.
    """
    entries: List[OddsEntry]
    bankroll: float = 1000.0
    min_profit_pct: float = 0.0
    max_stake_pct: float = 1.0
    promotions: List[PromoOffer] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate inputs after initialization."""
        if not self.entries:
            raise ValueError("Entries cannot be empty")
        if self.bankroll <= 0:
            raise ValueError("Bankroll must be positive")
        if not (0 <= self.min_profit_pct <= 100):
            raise ValueError("min_profit_pct must be between 0 and 100")
        if not (0 <= self.max_stake_pct <= 1):
            raise ValueError("max_stake_pct must be between 0 and 1")

    def find_opportunities(self) -> List[Dict]:
        """Find all arbitrage opportunities.

        Returns:
            List of dictionaries representing arbitrage opportunities.
        """
        opportunities = []

        # Group entries by market_id
        markets: Dict[str, List[OddsEntry]] = {}
        for entry in self.entries:
            if entry.market_id not in markets:
                markets[entry.market_id] = []
            markets[entry.market_id].append(entry)

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

                    if profit_pct > self.min_profit_pct:
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

                        opportunity = {
                            "market_id": market_id,
                            "market_type": market_type.value,
                            "event_name": market_entries[0].event_name or "",
                            "event_date": market_entries[0].event_date or "",
                            "sport": market_entries[0].sport or "",
                            "total_implied_prob": total_implied_prob,
                            "profit_pct": profit_pct,
                            "total_stake": total_stake,
                            "guaranteed_profit": guaranteed_profit,
                            "stake_distribution": stake_distribution,
                            "outcomes": outcomes,
                        }
                        opportunities.append(opportunity)

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

                    if profit_pct > self.min_profit_pct:
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

                        opportunity = {
                            "market_id": market_id,
                            "market_type": market_type.value,
                            "event_name": market_entries[0].event_name or "",
                            "event_date": market_entries[0].event_date or "",
                            "sport": market_entries[0].sport or "",
                            "total_implied_prob": total_implied_prob,
                            "profit_pct": profit_pct,
                            "total_stake": total_stake,
                            "guaranteed_profit": guaranteed_profit,
                            "stake_distribution": stake_distribution,
                            "outcomes": outcomes,
                        }
                        opportunities.append(opportunity)

        return opportunities

    def _get_over_under_entries(
        self,
        relevant_entries: List[OddsEntry],
    ) -> Optional[Tuple[OddsEntry, OddsEntry]]:
        """Extract over and under entries from a list of relevant entries.

        Args:
            relevant_entries: List of entries for a specific market.

        Returns:
            Tuple of (over_entry, under_entry) if found, None otherwise.
        """
        over_entries = [e for e in relevant_entries if e.side.lower() == "over"]
        under_entries = [e for e in relevant_entries if e.side.lower() == "under"]

        if over_entries and under_entries:
            # Get the best odds for each side
            over_entry = max(over_entries, key=lambda e: e.decimal_odds or e.odds_value)
            under_entry = max(under_entries, key=lambda e: e.decimal_odds or e.odds_value)
            return over_entry, under_entry

        return None

    def run_analysis(self) -> Dict:
        """Run full arbitrage analysis.

        Returns:
            Dictionary containing analysis results.
        """
        # Find best arbitrage opportunity
        best_opportunity = find_arbitrage_with_bankroll(
            self.entries,
            self.bankroll,
            self.min_profit_pct,
            self.max_stake_pct,
        )

        # Evaluate promotions
        promo_evaluations: List[Optional[PromoEvaluation]] = []
        for promo in self.promotions:
            # Find relevant entries for this promotion
            relevant_entries = [
                entry for entry in self.entries
                if entry.market_id == promo.market_id
            ]

            if relevant_entries:
                over_under = self._get_over_under_entries(relevant_entries)
                if over_under:
                    over_entry, under_entry = over_under
                    evaluation = promo.evaluate(
                        over_entry=over_entry,
                        under_entry=under_entry,
                        bankroll=self.bankroll,
                    )
                    promo_evaluations.append(evaluation)
                else:
                    promo_evaluations.append(None)
            else:
                promo_evaluations.append(None)

        return {
            "best_opportunity": best_opportunity.to_dict() if best_opportunity else None,
            "all_opportunities": self.find_opportunities(),
            "promo_evaluations": [
                e.to_dict() if e else None for e in promo_evaluations
            ],
        }

    def get_best_opportunity(self) -> Optional[Dict]:
        """Get the best arbitrage opportunity.

        Returns:
            Dictionary representing the best opportunity, or None if none found.
        """
        best_opportunity = find_arbitrage_with_bankroll(
            self.entries,
            self.bankroll,
            self.min_profit_pct,
            self.max_stake_pct,
        )
        return best_opportunity.to_dict() if best_opportunity else None
