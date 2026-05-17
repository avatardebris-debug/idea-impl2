"""
Entry point for the Sports/Event Bet Front Runner Pipeline.

Runs the pipeline with mock feeds, processes latency gaps, and optionally runs backtests.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from src.pipeline.config import LatencyConfig, PipelineConfig, SignalConfig
from src.pipeline.latency_detector import LatencyDetector
from src.pipeline.models import ProcessedSignal, SignalStats
from src.pipeline.adapters.mock_nfl_feed import MockNFLFeed
from src.pipeline.adapters.mock_nba_feed import MockNBAGameFeed
from src.backtest.backtest_harness import BacktestHarness

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_pipeline(max_events: int = 50) -> tuple[list[ProcessedSignal], SignalStats]:
    """Run the pipeline with mock feeds."""
    config = PipelineConfig(
        latency=LatencyConfig(
            gap_threshold=2.0,
            confidence_base=0.5,
            confidence_increment=0.1,
            confidence_multiplier_high=0.1,
            confidence_multiplier_low=-0.1,
        ),
        signal=SignalConfig(
            score_delay_threshold=2.0,
            play_delay_threshold=1.5,
            quarter_end_delay_threshold=3.0,
            anomaly_threshold=10.0,
            min_confidence=0.6,
            max_confidence=1.0,
        ),
        max_events=max_events,
    )

    detector = LatencyDetector(config.latency)
    all_signals: list[ProcessedSignal] = []
    stats = SignalStats()

    # Create mock feeds
    feeds = [
        MockNFLFeed({
            "seed": 42,
            "max_events": max_events // 2,
            "latency_gaps": [5.0, 7.0, 12.0],
        }),
        MockNBAGameFeed({
            "seed": 123,
            "max_events": max_events // 2,
            "latency_gaps": [3.0, 6.0, 15.0],
        }),
    ]

    # Start feeds
    for feed in feeds:
        await feed.start()

    # Process events from all feeds
    for feed in feeds:
        async for record in feed.get_events():
            # Detect latency gap
            gap = detector.detect_gap(record)
            if gap is None:
                continue

            # Generate signal
            signal = detector.generate_signal(gap, record.event.event_type)

            # Calculate confidence adjusted score and risk
            confidence_adjusted = signal.confidence
            risk_score = max(0.0, min(1.0, 1.0 - (gap.gap_seconds * 0.05)))

            # Determine action
            if confidence_adjusted >= config.signal.min_confidence:
                action = "bet"
            elif confidence_adjusted >= 0.4:
                action = "monitor"
            else:
                action = "skip"

            processed = ProcessedSignal(
                signal=signal,
                confidence_adjusted=confidence_adjusted,
                risk_score=risk_score,
                action=action,
            )

            all_signals.append(processed)
            stats.update(processed)

            logger.info(
                f"Processed: {signal.signal_id}, type={signal.signal_type.value}, "
                f"confidence={confidence_adjusted:.2f}, action={action}"
            )

    # Stop feeds
    for feed in feeds:
        await feed.stop()

    return all_signals, stats


async def run_backtest(signals: list[ProcessedSignal]) -> None:
    """Run a backtest with the given signals."""
    harness = BacktestHarness()
    results = harness.run_backtest(signals)
    summary = results.summary()
    logger.info(f"Backtest Results: {summary}")


async def main() -> None:
    """Main entry point."""
    logger.info("Starting Sports/Event Bet Front Runner Pipeline")

    # Run pipeline
    signals, stats = await run_pipeline(max_events=50)

    logger.info(f"Pipeline complete: {stats.total_processed} signals processed, "
                f"{stats.total_bets} bets, {stats.total_skipped} skipped, "
                f"{stats.total_monitored} monitored")
    logger.info(f"Bet rate: {stats.bet_rate:.2%}, Win rate: {stats.win_rate:.2%}")

    # Run backtest
    if signals:
        await run_backtest(signals)

    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    asyncio.run(main())
