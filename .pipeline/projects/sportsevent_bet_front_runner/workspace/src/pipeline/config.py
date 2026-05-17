"""
Configuration for the Sports/Event Bet Front Runner Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import SportType


@dataclass
class LatencyConfig:
    """Configuration for latency detection."""
    gap_threshold: float = 2.0
    confidence_base: float = 0.5
    confidence_increment: float = 0.1
    severity_thresholds: dict[str, float] = field(default_factory=lambda: {
        "low": 1.0,
        "medium": 2.0,
        "high": 5.0,
        "critical": 10.0,
    })
    confidence_multiplier_high: float = 0.1
    confidence_multiplier_low: float = -0.1
    risk_base: float = 0.5
    risk_decrement_per_second: float = 0.05
    risk_max: float = 1.0
    risk_min: float = 0.0


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    bet_amount: float = 100.0
    odds: float = 2.0
    commission_rate: float = 0.05
    max_bets: int = 1000
    initial_bankroll: float = 10000.0


@dataclass
class FeedConfig:
    """Configuration for a feed."""
    feed_id: str
    sport: SportType
    url: str
    poll_interval: float = 1.0
    seed: int = 42
    enabled: bool = True


@dataclass
class SignalConfig:
    """Configuration for signal generation."""
    score_delay_threshold: float = 2.0
    play_delay_threshold: float = 1.5
    quarter_end_delay_threshold: float = 3.0
    anomaly_threshold: float = 10.0
    min_confidence: float = 0.6
    max_confidence: float = 1.0


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""
    latency: LatencyConfig = field(default_factory=LatencyConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    signal: SignalConfig = field(default_factory=SignalConfig)
    feeds: list[FeedConfig] = field(default_factory=list)
    debug: bool = False
    max_events: int = 10000
    event_types: list[str] = field(default_factory=lambda: ["score", "play", "quarter_end", "half_end"])
    sports: list[str] = field(default_factory=lambda: ["nfl", "nba"])

    def add_feed(self, feed: FeedConfig) -> None:
        """Add a feed to the configuration."""
        self.feeds.append(feed)

    def get_feed_config(self, feed_id: str) -> FeedConfig | None:
        """Get configuration for a specific feed."""
        for feed in self.feeds:
            if feed.feed_id == feed_id:
                return feed
        return None
