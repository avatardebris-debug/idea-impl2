"""Funding tracker — monitors investment signals from Crunchbase, PitchBook, etc."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from chronovision_adapter.models import FundingEvent

logger = logging.getLogger(__name__)


@dataclass
class FundingSignal:
    """A processed signal indicating a funding trend."""
    sector: str
    total_funding_usd: float
    event_count: int
    avg_round_size: float
    top_investors: List[str]
    momentum: float  # 0-1 score indicating acceleration
    alert_level: str  # "low", "medium", "high", "critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sector": self.sector,
            "total_funding_usd": self.total_funding_usd,
            "event_count": self.event_count,
            "avg_round_size": self.avg_round_size,
            "top_investors": self.top_investors,
            "momentum": self.momentum,
            "alert_level": self.alert_level,
        }


class FundingTracker:
    """Tracks and analyses funding events to detect industry spikes.

    Uses offline stub data for testing; in production, would pull from
    Crunchbase, PitchBook, CB Insights, YC, and a16z APIs.
    """

    STUB_EVENTS = [
        FundingEvent("fund:001", "OpenAI", 6_700_000_000, "late_stage", ["Microsoft", "Thrive Capital"],
                     "2024-10-01", "AI/ML", "crunchbase", "Series C extension"),
        FundingEvent("fund:002", "Anthropic", 4_000_000_000, "series_d", ["Google", "Salesforce"],
                     "2024-09-15", "AI/ML", "crunchbase", "Safety-focused AI lab"),
        FundingEvent("fund:003", "Scale AI", 1_000_000_000, "series_f", ["Accel", "Tiger Global"],
                     "2024-05-20", "AI/ML", "pitchbook", "Data labeling platform"),
        FundingEvent("fund:004", "Moderna", 500_000_000, "public_offering", ["ARK Invest"],
                     "2024-03-10", "biotech", "cb_insights", "mRNA therapeutics"),
        FundingEvent("fund:005", "Anduril", 1_500_000_000, "series_f", ["Founders Fund", "a16z"],
                     "2024-08-01", "defense_tech", "a16z", "Defense technology"),
        FundingEvent("fund:006", "Stripe", 6_500_000_000, "series_i", ["Sequoia", "a16z"],
                     "2024-02-28", "fintech", "crunchbase", "Payment infrastructure"),
        FundingEvent("fund:007", "xAI", 6_000_000_000, "series_b", ["a16z", "Sequoia"],
                     "2024-12-01", "AI/ML", "pitchbook", "Frontier AI lab"),
        FundingEvent("fund:008", "Neuralink", 280_000_000, "series_d", ["Founders Fund"],
                     "2024-11-10", "neurotech", "crunchbase", "Brain-computer interfaces"),
    ]

    def __init__(self, events: Optional[List[FundingEvent]] = None):
        self.events = events if events is not None else list(self.STUB_EVENTS)

    def search(self, sector: str = "", min_amount: float = 0) -> List[FundingEvent]:
        """Search funding events by sector and minimum amount."""
        results = self.events
        if sector:
            results = [e for e in results if sector.lower() in e.sector.lower()]
        if min_amount > 0:
            results = [e for e in results if e.amount_usd >= min_amount]
        return results

    def get_sector_signal(self, sector: str) -> FundingSignal:
        """Generate a funding signal for a given sector."""
        events = self.search(sector=sector)
        if not events:
            return FundingSignal(
                sector=sector, total_funding_usd=0.0, event_count=0,
                avg_round_size=0.0, top_investors=[], momentum=0.0, alert_level="low",
            )

        total = sum(e.amount_usd for e in events)
        avg = total / len(events)

        # Collect top investors by frequency
        investor_counts: Dict[str, int] = {}
        for e in events:
            for inv in e.investors:
                investor_counts[inv] = investor_counts.get(inv, 0) + 1
        top_investors = sorted(investor_counts, key=investor_counts.get, reverse=True)[:5]

        # Momentum heuristic: based on count and total
        momentum = min(len(events) / 5.0, 1.0) * 0.5 + min(total / 10_000_000_000, 1.0) * 0.5

        # Alert level thresholds
        if momentum >= 0.8:
            alert = "critical"
        elif momentum >= 0.5:
            alert = "high"
        elif momentum >= 0.3:
            alert = "medium"
        else:
            alert = "low"

        return FundingSignal(
            sector=sector,
            total_funding_usd=total,
            event_count=len(events),
            avg_round_size=avg,
            top_investors=top_investors,
            momentum=round(momentum, 3),
            alert_level=alert,
        )

    def get_all_sectors(self) -> List[str]:
        """Return all unique sectors in the event database."""
        return sorted(set(e.sector for e in self.events if e.sector))

    def get_top_funded_sectors(self, top_n: int = 5) -> List[FundingSignal]:
        """Return funding signals for the top-funded sectors."""
        sectors = self.get_all_sectors()
        signals = [self.get_sector_signal(s) for s in sectors]
        signals.sort(key=lambda s: s.total_funding_usd, reverse=True)
        return signals[:top_n]

    def add_event(self, event: FundingEvent) -> None:
        """Add a new funding event to the tracker."""
        self.events.append(event)
