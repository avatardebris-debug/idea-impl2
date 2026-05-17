"""
Tests for the Sports/Event Bet Front Runner Pipeline.

Tests all components: models, config, latency detector, mock feeds, backtest harness, and pipeline.
"""

from __future__ import annotations

import asyncio
import time
import unittest
from unittest.mock import MagicMock, patch

from src.pipeline.config import (
    LatencyConfig,
    PipelineConfig,
    SignalConfig,
    BacktestConfig,
    FeedConfig,
)
from src.pipeline.models import (
    FeedEvent,
    FeedRecord,
    LatencyGap,
    ProcessedSignal,
    Signal,
    SignalStats,
    FeedStats,
    FeedManagerStats,
    EventType,
    SignalType,
    SportType,
    SeverityLevel,
)
from src.pipeline.latency_detector import LatencyDetector
from src.pipeline.adapters.mock_nfl_feed import MockNFLFeed
from src.pipeline.adapters.mock_nba_feed import MockNBAGameFeed
from src.backtest.backtest_harness import BacktestHarness, BetResult, BacktestResult


class TestLatencyConfig(unittest.TestCase):
    """Tests for LatencyConfig."""

    def test_default_values(self):
        config = LatencyConfig()
        self.assertEqual(config.gap_threshold, 2.0)
        self.assertEqual(config.confidence_base, 0.5)
        self.assertEqual(config.confidence_increment, 0.1)
        self.assertEqual(config.confidence_multiplier_high, 0.1)
        self.assertEqual(config.confidence_multiplier_low, -0.1)

    def test_severity_thresholds(self):
        config = LatencyConfig()
        self.assertEqual(config.severity_thresholds["low"], 1.0)
        self.assertEqual(config.severity_thresholds["medium"], 2.0)
        self.assertEqual(config.severity_thresholds["high"], 5.0)
        self.assertEqual(config.severity_thresholds["critical"], 10.0)


class TestSignalConfig(unittest.TestCase):
    """Tests for SignalConfig."""

    def test_default_values(self):
        config = SignalConfig()
        self.assertEqual(config.score_delay_threshold, 2.0)
        self.assertEqual(config.play_delay_threshold, 1.5)
        self.assertEqual(config.quarter_end_delay_threshold, 3.0)
        self.assertEqual(config.anomaly_threshold, 10.0)
        self.assertEqual(config.min_confidence, 0.6)
        self.assertEqual(config.max_confidence, 1.0)


class TestBacktestConfig(unittest.TestCase):
    """Tests for BacktestConfig."""

    def test_default_values(self):
        config = BacktestConfig()
        self.assertEqual(config.bet_amount, 100.0)
        self.assertEqual(config.odds, 2.0)
        self.assertEqual(config.commission_rate, 0.05)
        self.assertEqual(config.max_bets, 1000)
        self.assertEqual(config.initial_bankroll, 10000.0)


class TestPipelineConfig(unittest.TestCase):
    """Tests for PipelineConfig."""

    def test_default_values(self):
        config = PipelineConfig()
        self.assertIsInstance(config.latency, LatencyConfig)
        self.assertIsInstance(config.signal, SignalConfig)
        self.assertIsInstance(config.backtest, BacktestConfig)
        self.assertEqual(config.feeds, [])
        self.assertFalse(config.debug)
        self.assertEqual(config.max_events, 10000)

    def test_add_feed(self):
        config = PipelineConfig()
        feed = FeedConfig(feed_id="test", sport="nfl", url="http://test")
        config.add_feed(feed)
        self.assertEqual(len(config.feeds), 1)
        self.assertEqual(config.feeds[0].feed_id, "test")

    def test_get_feed_config(self):
        config = PipelineConfig()
        feed = FeedConfig(feed_id="test", sport="nfl", url="http://test")
        config.add_feed(feed)
        result = config.get_feed_config("test")
        self.assertIsNotNone(result)
        self.assertEqual(result.feed_id, "test")

    def test_get_feed_config_not_found(self):
        config = PipelineConfig()
        result = config.get_feed_config("nonexistent")
        self.assertIsNone(result)


class TestLatencyGap(unittest.TestCase):
    """Tests for LatencyGap."""

    def test_severity_auto_calculation(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            gap_seconds=5.0,
            confidence_score=0.5,
            severity=SeverityLevel.LOW,  # Will be overwritten
        )
        self.assertEqual(gap.severity, SeverityLevel.HIGH)

    def test_severity_critical(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=115.0,
            gap_seconds=15.0,
            confidence_score=0.5,
            severity=SeverityLevel.LOW,
        )
        self.assertEqual(gap.severity, SeverityLevel.CRITICAL)

    def test_severity_medium(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=101.5,
            gap_seconds=1.5,
            confidence_score=0.5,
            severity=SeverityLevel.LOW,
        )
        self.assertEqual(gap.severity, SeverityLevel.LOW)


class TestFeedEvent(unittest.TestCase):
    """Tests for FeedEvent."""

    def test_creation(self):
        event = FeedEvent(
            event_id="test_1",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=100.0,
            data={"team": "KC"},
        )
        self.assertEqual(event.event_id, "test_1")
        self.assertEqual(event.event_type, EventType.SCORE)
        self.assertEqual(event.sport, SportType.NFL)
        self.assertEqual(event.data["team"], "KC")


class TestFeedRecord(unittest.TestCase):
    """Tests for FeedRecord."""

    def test_creation(self):
        event = FeedEvent(
            event_id="test_1",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=100.0,
        )
        record = FeedRecord(
            feed_id="test_feed",
            event=event,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            processing_latency_ms=25.0,
        )
        self.assertEqual(record.feed_id, "test_feed")
        self.assertEqual(record.processing_latency_ms, 25.0)


class TestSignal(unittest.TestCase):
    """Tests for Signal."""

    def test_creation(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            gap_seconds=5.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_test_1",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_1",
            sport=SportType.NFL,
            gap=gap,
            description="Test signal",
            confidence=0.8,
        )
        self.assertEqual(signal.signal_id, "sig_test_1")
        self.assertEqual(signal.signal_type, SignalType.SCORE_DELAYED)
        self.assertEqual(signal.confidence, 0.8)


class TestProcessedSignal(unittest.TestCase):
    """Tests for ProcessedSignal."""

    def test_creation(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            gap_seconds=5.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_test_1",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_1",
            sport=SportType.NFL,
            gap=gap,
            description="Test signal",
            confidence=0.8,
        )
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=0.75,
            risk_score=0.5,
            action="bet",
        )
        self.assertEqual(processed.action, "bet")
        self.assertEqual(processed.confidence_adjusted, 0.75)


class TestSignalStats(unittest.TestCase):
    """Tests for SignalStats."""

    def test_initial_state(self):
        stats = SignalStats()
        self.assertEqual(stats.total_processed, 0)
        self.assertEqual(stats.total_bets, 0)
        self.assertEqual(stats.total_skipped, 0)
        self.assertEqual(stats.total_monitored, 0)
        self.assertEqual(stats.bet_rate, 0.0)
        self.assertEqual(stats.win_rate, 0.0)

    def test_update_bet(self):
        stats = SignalStats()
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            gap_seconds=5.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_test_1",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_1",
            sport=SportType.NFL,
            gap=gap,
            description="Test signal",
            confidence=0.8,
        )
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=0.75,
            risk_score=0.5,
            action="bet",
        )
        stats.update(processed)
        self.assertEqual(stats.total_processed, 1)
        self.assertEqual(stats.total_bets, 1)
        self.assertEqual(stats.bet_rate, 1.0)

    def test_update_skip(self):
        stats = SignalStats()
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            gap_seconds=5.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_test_1",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_1",
            sport=SportType.NFL,
            gap=gap,
            description="Test signal",
            confidence=0.8,
        )
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=0.75,
            risk_score=0.5,
            action="skip",
        )
        stats.update(processed)
        self.assertEqual(stats.total_processed, 1)
        self.assertEqual(stats.total_skipped, 1)
        self.assertEqual(stats.bet_rate, 0.0)

    def test_update_monitor(self):
        stats = SignalStats()
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            gap_seconds=5.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_test_1",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_1",
            sport=SportType.NFL,
            gap=gap,
            description="Test signal",
            confidence=0.8,
        )
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=0.75,
            risk_score=0.5,
            action="monitor",
        )
        stats.update(processed)
        self.assertEqual(stats.total_processed, 1)
        self.assertEqual(stats.total_monitored, 1)


class TestFeedStats(unittest.TestCase):
    """Tests for FeedStats."""

    def test_initial_state(self):
        stats = FeedStats()
        self.assertEqual(stats.total_events, 0)
        self.assertEqual(stats.total_gaps, 0)
        self.assertEqual(stats.avg_latency_ms, 0.0)
        self.assertEqual(stats.avg_gap_seconds, 0.0)

    def test_update(self):
        stats = FeedStats()
        record = FeedRecord(
            feed_id="test_feed",
            event=FeedEvent(
                event_id="test_1",
                event_type=EventType.SCORE,
                sport=SportType.NFL,
                raw_timestamp=100.0,
            ),
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            processing_latency_ms=25.0,
        )
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=105.0,
            gap_seconds=5.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        stats.update(record, gap)
        self.assertEqual(stats.total_events, 1)
        self.assertEqual(stats.total_gaps, 1)
        self.assertEqual(stats.avg_latency_ms, 25.0)
        self.assertEqual(stats.avg_gap_seconds, 5.0)


class TestFeedManagerStats(unittest.TestCase):
    """Tests for FeedManagerStats."""

    def test_initial_state(self):
        stats = FeedManagerStats()
        self.assertEqual(stats.total_feeds, 0)
        self.assertEqual(stats.active_feeds, 0)
        self.assertEqual(stats.total_events, 0)
        self.assertEqual(stats.total_gaps, 0)

    def test_update(self):
        stats = FeedManagerStats()
        stats.update(total_feeds=5, active_feeds=3, total_events=100, total_gaps=10)
        self.assertEqual(stats.total_feeds, 5)
        self.assertEqual(stats.active_feeds, 3)
        self.assertEqual(stats.total_events, 100)
        self.assertEqual(stats.total_gaps, 10)


class TestLatencyDetector(unittest.TestCase):
    """Tests for LatencyDetector."""

    def setUp(self):
        self.config = LatencyConfig()
        self.detector = LatencyDetector(self.config)

    def test_detect_gap_normal(self):
        record = FeedRecord(
            feed_id="test_feed",
            event=FeedEvent(
                event_id="test_1",
                event_type=EventType.SCORE,
                sport=SportType.NFL,
                raw_timestamp=100.0,
            ),
            raw_timestamp=100.0,
            broadcast_timestamp=101.0,  # Only 1s gap
            processing_latency_ms=25.0,
        )
        gap = self.detector.detect_gap(record)
        self.assertIsNone(gap)

    def test_detect_gap_large(self):
        record = FeedRecord(
            feed_id="test_feed",
            event=FeedEvent(
                event_id="test_1",
                event_type=EventType.SCORE,
                sport=SportType.NFL,
                raw_timestamp=100.0,
            ),
            raw_timestamp=100.0,
            broadcast_timestamp=106.0,  # 6s gap
            processing_latency_ms=25.0,
        )
        gap = self.detector.detect_gap(record)
        self.assertIsNotNone(gap)
        self.assertEqual(gap.gap_seconds, 6.0)
        self.assertEqual(gap.severity, SeverityLevel.HIGH)

    def test_generate_signal_score_delayed(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=106.0,
            gap_seconds=6.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = self.detector.generate_signal(gap, EventType.SCORE)
        self.assertEqual(signal.signal_type, SignalType.SCORE_DELAYED)
        self.assertGreater(signal.confidence, 0.5)

    def test_generate_signal_anomaly(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=115.0,
            gap_seconds=15.0,
            confidence_score=0.5,
            severity=SeverityLevel.CRITICAL,
        )
        signal = self.detector.generate_signal(gap, EventType.PLAY)
        self.assertEqual(signal.signal_type, SignalType.ANOMALY_DETECTED)
        self.assertGreater(signal.confidence, 0.5)


class TestMockNFLFeed(unittest.TestCase):
    """Tests for MockNFLFeed."""

    def setUp(self):
        self.feed = MockNFLFeed({"seed": 42, "max_events": 10, "latency_gaps": [5.0, 7.0]})

    def test_connect(self):
        asyncio.get_event_loop().run_until_complete(self.feed.connect())
        self.assertTrue(self.feed.is_connected)

    def test_get_events(self):
        asyncio.get_event_loop().run_until_complete(self.feed.connect())
        asyncio.get_event_loop().run_until_complete(self.feed.start())

        events = []
        for record in asyncio.get_event_loop().run_until_complete(self.feed.get_events()):
            events.append(record)
            if len(events) >= 10:
                break

        self.assertGreater(len(events), 0)
        self.assertEqual(events[0].event.sport, SportType.NFL)

        asyncio.get_event_loop().run_until_complete(self.feed.stop())
        asyncio.get_event_loop().run_until_complete(self.feed.disconnect())


class TestMockNBAGameFeed(unittest.TestCase):
    """Tests for MockNBAGameFeed."""

    def setUp(self):
        self.feed = MockNBAGameFeed({"seed": 123, "max_events": 10, "latency_gaps": [3.0, 6.0]})

    def test_connect(self):
        asyncio.get_event_loop().run_until_complete(self.feed.connect())
        self.assertTrue(self.feed.is_connected)

    def test_get_events(self):
        asyncio.get_event_loop().run_until_complete(self.feed.connect())
        asyncio.get_event_loop().run_until_complete(self.feed.start())

        events = []
        for record in asyncio.get_event_loop().run_until_complete(self.feed.get_events()):
            events.append(record)
            if len(events) >= 10:
                break

        self.assertGreater(len(events), 0)
        self.assertEqual(events[0].event.sport, SportType.NBA)

        asyncio.get_event_loop().run_until_complete(self.feed.stop())
        asyncio.get_event_loop().run_until_complete(self.feed.disconnect())


class TestBacktestHarness(unittest.TestCase):
    """Tests for BacktestHarness."""

    def setUp(self):
        self.harness = BacktestHarness(BacktestConfig(
            bet_amount=100.0,
            odds=2.0,
            commission_rate=0.05,
            max_bets=100,
            initial_bankroll=10000.0,
        ))

    def test_process_signal_bet(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=106.0,
            gap_seconds=6.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_test_1",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_1",
            sport=SportType.NFL,
            gap=gap,
            description="Test signal",
            confidence=0.8,
        )
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=0.75,
            risk_score=0.5,
            action="bet",
        )

        with patch("random.random", return_value=0.6):  # Win
            result = self.harness.process_signal(processed)
            self.assertIsNotNone(result)
            self.assertTrue(result.is_win)
            self.assertGreater(result.net_profit, 0)

    def test_process_signal_skip(self):
        gap = LatencyGap(
            event_id="test_1",
            sport=SportType.NFL,
            raw_timestamp=100.0,
            broadcast_timestamp=106.0,
            gap_seconds=6.0,
            confidence_score=0.5,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_test_1",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_1",
            sport=SportType.NFL,
            gap=gap,
            description="Test signal",
            confidence=0.8,
        )
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=0.75,
            risk_score=0.5,
            action="skip",
        )

        result = self.harness.process_signal(processed)
        self.assertIsNone(result)
        self.assertEqual(self.harness.results.total_bets, 0)

    def test_run_backtest(self):
        signals = []
        for i in range(10):
            gap = LatencyGap(
                event_id=f"test_{i}",
                sport=SportType.NFL,
                raw_timestamp=100.0,
                broadcast_timestamp=106.0,
                gap_seconds=6.0,
                confidence_score=0.5,
                severity=SeverityLevel.HIGH,
            )
            signal = Signal(
                signal_id=f"sig_test_{i}",
                signal_type=SignalType.SCORE_DELAYED,
                event_id=f"test_{i}",
                sport=SportType.NFL,
                gap=gap,
                description="Test signal",
                confidence=0.8,
            )
            processed = ProcessedSignal(
                signal=signal,
                confidence_adjusted=0.75,
                risk_score=0.5,
                action="bet",
            )
            signals.append(processed)

        with patch("random.random", return_value=0.6):  # All wins
            results = self.harness.run_backtest(signals)
            self.assertEqual(results.total_bets, 10)
            self.assertEqual(results.wins, 10)
            self.assertEqual(results.losses, 0)
            self.assertGreater(results.final_bankroll, results.initial_bankroll)


if __name__ == "__main__":
    unittest.main()
