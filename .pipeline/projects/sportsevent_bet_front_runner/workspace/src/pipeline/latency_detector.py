"""
Latency gap detection for the Sports/Event Bet Front Runner Pipeline.
"""

from __future__ import annotations

import logging
from src.pipeline.config import LatencyConfig
from src.pipeline.models import (
    FeedRecord,
    LatencyGap,
    SeverityLevel,
    Signal,
    SignalType,
    SportType,
    EventType,
)

logger = logging.getLogger(__name__)


class LatencyDetector:
    """Detects latency gaps between raw and broadcast timestamps."""

    def __init__(self, config: LatencyConfig = None):
        self.config = config or LatencyConfig()

    def detect_gap(self, record: FeedRecord) -> LatencyGap | None:
        """Detect a latency gap from a feed record."""
        gap_seconds = record.broadcast_timestamp - record.raw_timestamp

        if gap_seconds < self.config.gap_threshold:
            return None

        confidence = self._calculate_confidence(gap_seconds)
        severity = self._calculate_severity(gap_seconds)

        gap = LatencyGap(
            event_id=record.event.event_id,
            sport=record.event.sport,
            raw_timestamp=record.raw_timestamp,
            broadcast_timestamp=record.broadcast_timestamp,
            gap_seconds=gap_seconds,
            confidence_score=confidence,
            severity=severity,
        )

        logger.info(
            f"Latency gap detected: event={gap.event_id}, "
            f"gap={gap_seconds:.2f}s, severity={severity.value}, "
            f"confidence={confidence:.2f}"
        )

        return gap

    def generate_signal(self, gap: LatencyGap, event_type: EventType = None) -> Signal:
        """Generate a signal from a latency gap."""
        signal_type = self._map_to_signal_type(gap, event_type)
        confidence = self._calculate_signal_confidence(gap)
        description = self._generate_description(gap, event_type)

        signal = Signal(
            signal_id=f"sig_{gap.event_id}",
            signal_type=signal_type,
            event_id=gap.event_id,
            sport=gap.sport,
            gap=gap,
            description=description,
            confidence=confidence,
        )

        logger.info(
            f"Signal generated: type={signal_type.value}, "
            f"event={gap.event_id}, confidence={confidence:.2f}"
        )

        return signal

    def _calculate_confidence(self, gap_seconds: float) -> float:
        """Calculate confidence score based on gap size."""
        base = self.config.confidence_base
        increment = self.config.confidence_increment
        multiplier = self.config.confidence_multiplier_high

        # Confidence increases with gap size
        confidence = base + (gap_seconds * multiplier)
        return min(confidence, 1.0)

    def _calculate_severity(self, gap_seconds: float) -> SeverityLevel:
        """Calculate severity level based on gap size."""
        thresholds = self.config.severity_thresholds
        if gap_seconds >= thresholds["high"]:
            return SeverityLevel.HIGH
        elif gap_seconds >= thresholds["medium"]:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    def _map_to_signal_type(self, gap: LatencyGap, event_type: EventType = None) -> SignalType:
        """Map a latency gap to a signal type based on event type."""
        if event_type is None:
            event_type = EventType.PLAY  # default
        if gap.sport == SportType.NFL:
            if event_type == EventType.QUARTER_END:
                return SignalType.QUARTER_END_DELAYED
            elif event_type == EventType.SCORE:
                return SignalType.SCORE_DELAYED
            else:
                return SignalType.PLAY_DELAYED
        elif gap.sport == SportType.NBA:
            if event_type == EventType.HALF_END:
                return SignalType.QUARTER_END_DELAYED
            elif event_type == EventType.SCORE:
                return SignalType.SCORE_DELAYED
            else:
                return SignalType.PLAY_DELAYED
        else:
            return SignalType.ANOMALY_DETECTED

    def _calculate_signal_confidence(self, gap: LatencyGap) -> float:
        """Calculate signal confidence based on gap and severity."""
        confidence = gap.confidence_score
        if gap.severity == SeverityLevel.CRITICAL:
            confidence += self.config.confidence_multiplier_high * 2
        elif gap.severity == SeverityLevel.HIGH:
            confidence += self.config.confidence_multiplier_high
        elif gap.severity == SeverityLevel.LOW:
            confidence += self.config.confidence_multiplier_low
        return min(max(confidence, 0.0), 1.0)

    def _generate_description(self, gap: LatencyGap, event_type: EventType = None) -> str:
        """Generate a human-readable description of the gap."""
        if event_type is None:
            event_type = EventType.PLAY
        return (
            f"{gap.sport.value.upper()} {event_type.value} event delayed by "
            f"{gap.gap_seconds:.2f}s (severity: {gap.severity.value})"
        )
