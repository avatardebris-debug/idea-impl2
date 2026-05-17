"""
Signal processor for the Sports/Event Bet Front Runner pipeline.

Processes latency gap signals and generates actionable trading signals
with confidence scoring and risk management.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

from src.pipeline.config import BacktestConfig, LatencyConfig
from src.pipeline.models import (
    LatencyGap,
    Signal,
    SignalType,
    SeverityLevel,
    SportType,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessedSignal:
    """A signal that has been processed and enriched with metadata."""
    signal: Signal
    processed_at: float = field(default_factory=time.time)
    confidence_adjusted: float = 0.0
    risk_score: float = 0.0
    action: str = "monitor"  # monitor, bet, skip
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalStats:
    """Statistics for processed signals."""
    total_processed: int = 0
    total_bets: int = 0
    total_skipped: int = 0
    total_monitored: int = 0
    avg_confidence: float = 0.0
    avg_risk_score: float = 0.0
    signals_by_type: Dict[str, int] = field(default_factory=dict)
    signals_by_sport: Dict[str, int] = field(default_factory=dict)
    recent_signals: deque = field(default_factory=lambda: deque(maxlen=100))

    def update(self, processed: ProcessedSignal) -> None:
        """Update statistics with a new processed signal."""
        self.total_processed += 1
        if processed.action == "bet":
            self.total_bets += 1
        elif processed.action == "skip":
            self.total_skipped += 1
        else:
            self.total_monitored += 1

        self.signals_by_type[processed.signal.signal_type.value] = \
            self.signals_by_type.get(processed.signal.signal_type.value, 0) + 1
        self.signals_by_sport[processed.signal.sport.value] = \
            self.signals_by_sport.get(processed.signal.sport.value, 0) + 1

        self.recent_signals.append(processed)

    @property
    def bet_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.total_bets / self.total_processed

    @property
    def avg_confidence_adjusted(self) -> float:
        if not self.recent_signals:
            return 0.0
        return sum(s.confidence_adjusted for s in self.recent_signals) / len(self.recent_signals)

    @property
    def avg_risk_adjusted(self) -> float:
        if not self.recent_signals:
            return 0.0
        return sum(s.risk_score for s in self.recent_signals) / len(self.recent_signals)


class SignalProcessor:
    """
    Processes latency gap signals and generates actionable trading signals.

    Applies confidence scoring, risk management, and signal filtering
    to determine whether to bet, monitor, or skip each signal.
    """

    def __init__(
        self,
        latency_config: Optional[LatencyConfig] = None,
        backtest_config: Optional[BacktestConfig] = None,
    ):
        self.latency_config = latency_config or LatencyConfig()
        self.backtest_config = backtest_config or BacktestConfig()
        self._stats = SignalStats()
        self._signal_handlers: List[Callable[[Signal], Coroutine[Any, Any, None]]] = []
        self._processed_count = 0
        self._running = False
        self._recent_gaps: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self._signal_history: deque = deque(maxlen=1000)

    @property
    def stats(self) -> SignalStats:
        return self._stats

    @property
    def processed_count(self) -> int:
        return self._processed_count

    @property
    def is_running(self) -> bool:
        return self._running

    def add_signal_handler(
        self,
        handler: Callable[[Signal], Coroutine[Any, Any, None]],
    ) -> None:
        """Add a handler for processed signals."""
        self._signal_handlers.append(handler)
        logger.info(f"Added signal handler. Total handlers: {len(self._signal_handlers)}")

    def remove_signal_handler(
        self,
        handler: Callable[[Signal], Coroutine[Any, Any, None]],
    ) -> None:
        """Remove a signal handler."""
        if handler in self._signal_handlers:
            self._signal_handlers.remove(handler)
            logger.info(f"Removed signal handler. Total handlers: {len(self._signal_handlers)}")

    def process_signal(self, signal: Signal) -> ProcessedSignal:
        """
        Process a latency gap signal and determine the appropriate action.

        Returns a ProcessedSignal with the action to take.
        """
        self._processed_count += 1
        self._signal_history.append(signal)

        # Calculate adjusted confidence
        confidence_adjusted = self._calculate_confidence(signal)

        # Calculate risk score
        risk_score = self._calculate_risk(signal)

        # Determine action
        action = self._determine_action(signal, confidence_adjusted, risk_score)

        # Create processed signal
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=confidence_adjusted,
            risk_score=risk_score,
            action=action,
            metadata={
                "original_confidence": signal.confidence,
                "gap_seconds": signal.gap.gap_seconds if signal.gap else 0.0,
                "severity": signal.gap.severity.value if signal.gap else "unknown",
            },
        )

        # Update statistics
        self._stats.update(processed)

        # Track recent gaps for this sport
        sport_key = signal.sport.value
        if signal.gap:
            self._recent_gaps[sport_key].append(signal.gap.gap_seconds)

        # Log the processed signal
        logger.info(
            f"Processed signal: {signal.signal_id}, type={signal.signal_type.value}, "
            f"confidence={confidence_adjusted:.3f}, risk={risk_score:.3f}, action={action}"
        )

        # Notify handlers
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._notify_handlers(signal))
        except RuntimeError:
            # No running event loop, skip async notification
            pass

        return processed

    def process_signals(self, signals: List[Signal]) -> List[ProcessedSignal]:
        """Process a list of signals and return processed results."""
        return [self.process_signal(s) for s in signals]

    def _calculate_confidence(self, signal: Signal) -> float:
        """Calculate adjusted confidence score for a signal."""
        if not signal.gap:
            return 0.0

        gap = signal.gap
        base_confidence = signal.confidence

        # Adjust based on gap severity
        severity_multiplier = {
            SeverityLevel.CRITICAL: 1.2,
            SeverityLevel.HIGH: 1.1,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.LOW: 0.9,
        }.get(gap.severity, 1.0)

        # Adjust based on gap size
        gap_factor = min(gap.gap_seconds / self.latency_config.gap_threshold_seconds, 2.0)
        gap_multiplier = 0.5 + (gap_factor * 0.5)

        # Adjust based on recent gap frequency for this sport
        sport_key = signal.sport.value
        recent_gaps = self._recent_gaps[sport_key]
        if len(recent_gaps) > 5:
            avg_recent_gap = sum(recent_gaps) / len(recent_gaps)
            if avg_recent_gap > self.latency_config.gap_threshold_seconds:
                # Frequent gaps suggest systematic issue, increase confidence
                frequency_multiplier = 1.1
            else:
                frequency_multiplier = 0.95
        else:
            frequency_multiplier = 1.0

        adjusted = base_confidence * severity_multiplier * gap_multiplier * frequency_multiplier
        return min(adjusted, 1.0)

    def _calculate_risk(self, signal: Signal) -> float:
        """Calculate risk score for a signal (0-1, lower is better)."""
        if not signal.gap:
            return 0.5

        gap = signal.gap
        risk = 0.0

        # Lower gaps are riskier (less reliable)
        if gap.gap_seconds < self.latency_config.low_confidence_threshold:
            risk += 0.3
        elif gap.gap_seconds < self.latency_config.high_confidence_threshold:
            risk += 0.1

        # Higher severity gaps are less risky (more reliable)
        risk -= {
            SeverityLevel.CRITICAL: 0.2,
            SeverityLevel.HIGH: 0.1,
            SeverityLevel.MEDIUM: 0.0,
            SeverityLevel.LOW: 0.1,
        }.get(gap.severity, 0.0)

        # Recent gap frequency increases risk
        sport_key = signal.sport.value
        recent_gaps = self._recent_gaps[sport_key]
        if len(recent_gaps) > 10:
            risk += 0.1  # Too many gaps might indicate noise

        return max(0.0, min(1.0, risk))

    def _determine_action(
        self,
        signal: Signal,
        confidence: float,
        risk: float,
    ) -> str:
        """Determine the action to take based on confidence and risk."""
        # Check minimum gap threshold
        if signal.gap and signal.gap.gap_seconds < self.backtest_config.min_exploitable_gap_seconds:
            return "skip"

        # High confidence, low risk -> bet
        if confidence >= 0.7 and risk <= 0.3:
            return "bet"

        # Medium confidence, medium risk -> monitor
        if confidence >= 0.4 and risk <= 0.6:
            return "monitor"

        # Low confidence or high risk -> skip
        return "skip"

    async def _notify_handlers(self, signal: Signal) -> None:
        """Notify all signal handlers about a new signal."""
        for handler in self._signal_handlers:
            try:
                await handler(signal)
            except Exception as e:
                logger.error(f"Error in signal handler: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get signal processing statistics."""
        return {
            "total_processed": self._stats.total_processed,
            "total_bets": self._stats.total_bets,
            "total_skipped": self._stats.total_skipped,
            "total_monitored": self._stats.total_monitored,
            "bet_rate": self._stats.bet_rate,
            "avg_confidence_adjusted": self._stats.avg_confidence_adjusted,
            "avg_risk_score": self._stats.avg_risk_adjusted,
            "signals_by_type": dict(self._stats.signals_by_type),
            "signals_by_sport": dict(self._stats.signals_by_sport),
        }

    def get_recent_signals(self, count: int = 10) -> List[Signal]:
        """Get the most recent signals."""
        return list(self._signal_history)[-count:]

    def reset(self) -> None:
        """Reset all signal processor state."""
        self._stats = SignalStats()
        self._processed_count = 0
        self._recent_gaps.clear()
        self._signal_history.clear()
        logger.info("Signal processor reset")

    def start(self) -> None:
        """Start the signal processor."""
        self._running = True
        logger.info("Signal processor started")

    def stop(self) -> None:
        """Stop the signal processor."""
        self._running = False
        logger.info("Signal processor stopped")
