"""
Data models for the Sports/Event Bet Front Runner Pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SportType(Enum):
    """Supported sports."""
    NFL = "nfl"
    NBA = "nba"


class EventType(Enum):
    """Types of events in the feed."""
    SCORE = "score"
    PLAY = "play"
    QUARTER_END = "quarter_end"
    HALF_END = "half_end"


class SignalType(Enum):
    """Types of signals generated."""
    SCORE_DELAYED = "score_delayed"
    PLAY_DELAYED = "play_delayed"
    QUARTER_END_DELAYED = "quarter_end_delayed"
    ANOMALY_DETECTED = "anomaly_detected"


class SeverityLevel(Enum):
    """Severity levels for latency gaps."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LatencyGap:
    """Represents a latency gap between raw and broadcast timestamps."""
    event_id: str
    sport: SportType
    raw_timestamp: float
    broadcast_timestamp: float
    gap_seconds: float
    confidence_score: float
    severity: SeverityLevel

    def __post_init__(self):
        if self.gap_seconds > 10.0:
            self.severity = SeverityLevel.CRITICAL
        elif self.gap_seconds > 5.0:
            self.severity = SeverityLevel.HIGH
        elif self.gap_seconds > 2.0:
            self.severity = SeverityLevel.MEDIUM
        else:
            self.severity = SeverityLevel.LOW


@dataclass
class FeedEvent:
    """Represents an event from a feed."""
    event_id: str
    event_type: EventType
    sport: SportType
    raw_timestamp: float
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedRecord:
    """Represents a processed feed record."""
    feed_id: str
    event: FeedEvent
    raw_timestamp: float
    broadcast_timestamp: float
    processing_latency_ms: float


@dataclass
class Signal:
    """Represents a generated signal."""
    signal_id: str
    signal_type: SignalType
    event_id: str
    sport: SportType
    gap: LatencyGap
    description: str
    confidence: float


@dataclass
class ProcessedSignal:
    """Represents a processed signal ready for action."""
    signal: Signal
    confidence_adjusted: float
    risk_score: float
    action: str  # "bet", "monitor", "skip"
    processed_at: float = field(default_factory=time.time)


@dataclass
class SignalStats:
    """Statistics for signal processing."""
    total_processed: int = 0
    total_bets: int = 0
    total_skipped: int = 0
    total_monitored: int = 0
    signals_by_type: dict[str, int] = field(default_factory=dict)
    signals_by_sport: dict[str, int] = field(default_factory=dict)

    def update(self, processed: ProcessedSignal) -> None:
        """Update stats with a processed signal."""
        self.total_processed += 1
        if processed.action == "bet":
            self.total_bets += 1
        elif processed.action == "skip":
            self.total_skipped += 1
        elif processed.action == "monitor":
            self.total_monitored += 1

        signal_type = processed.signal.signal_type.value
        self.signals_by_type[signal_type] = self.signals_by_type.get(signal_type, 0) + 1

        sport = processed.signal.sport.value
        self.signals_by_sport[sport] = self.signals_by_sport.get(sport, 0) + 1

    @property
    def bet_rate(self) -> float:
        """Calculate the bet rate."""
        if self.total_processed == 0:
            return 0.0
        return self.total_bets / self.total_processed


@dataclass
class FeedStats:
    """Statistics for a single feed."""
    feed_id: str
    total_events_received: int = 0
    total_records_processed: int = 0
    total_errors: int = 0
    start_time: float | None = None
    end_time: float | None = None
    _latency_sum: float = 0.0

    @property
    def events_per_second(self) -> float:
        """Calculate events per second."""
        if self.start_time and self.end_time and self.end_time > self.start_time:
            duration = self.end_time - self.start_time
            return self.total_events_received / duration if duration > 0 else 0.0
        return 0.0

    @property
    def avg_processing_latency_ms(self) -> float:
        """Calculate average processing latency."""
        if self.total_records_processed == 0:
            return 0.0
        return self._latency_sum / self.total_records_processed

    def update_record(self, record: FeedRecord) -> None:
        """Update stats with a processed record."""
        self.total_records_processed += 1
        self._latency_sum += record.processing_latency_ms
        if self.start_time is None:
            self.start_time = time.time()

    def update_error(self) -> None:
        """Update stats with an error."""
        self.total_errors += 1


@dataclass
class FeedManagerStats:
    """Statistics for the feed manager."""
    total_feeds: int = 0
    active_feeds: int = 0
    total_events_received: int = 0
    total_records_processed: int = 0
    total_errors: int = 0

    def update(self, feed_stats: FeedStats) -> None:
        """Update stats with feed statistics."""
        self.total_feeds += 1
        self.active_feeds += 1
        self.total_events_received += feed_stats.total_events_received
        self.total_records_processed += feed_stats.total_records_processed
        self.total_errors += feed_stats.total_errors
