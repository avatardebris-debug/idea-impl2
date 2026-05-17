"""
Unit and integration tests for SignalProcessor and FeedManager.
"""

import asyncio
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, "/workspace/idea impl")

from src.pipeline.config import BacktestConfig, LatencyConfig, PipelineConfig, FeedConfig
from src.pipeline.models import (
    FeedEvent,
    FeedRecord,
    LatencyGap,
    Signal,
    SignalType,
    SeverityLevel,
    SportType,
    EventType,
)
from src.pipeline.signal_processor import SignalProcessor, ProcessedSignal, SignalStats
from src.pipeline.feed_manager import FeedManager, FeedStats, FeedManagerStats


class TestProcessedSignal(unittest.TestCase):
    """Test ProcessedSignal dataclass."""

    def test_creation(self):
        gap = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_001",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap,
            description="Test",
            confidence=0.75,
        )
        processed = ProcessedSignal(
            signal=signal,
            confidence_adjusted=0.8,
            risk_score=0.2,
            action="bet",
        )

        self.assertEqual(processed.signal.signal_id, "sig_001")
        self.assertEqual(processed.confidence_adjusted, 0.8)
        self.assertEqual(processed.risk_score, 0.2)
        self.assertEqual(processed.action, "bet")
        self.assertIsNotNone(processed.processed_at)


class TestSignalStats(unittest.TestCase):
    """Test SignalStats dataclass."""

    def test_initial_state(self):
        stats = SignalStats()
        self.assertEqual(stats.total_processed, 0)
        self.assertEqual(stats.total_bets, 0)
        self.assertEqual(stats.bet_rate, 0.0)

    def test_update(self):
        stats = SignalStats()
        gap = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_001",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap,
            description="Test",
            confidence=0.75,
        )
        processed = ProcessedSignal(signal=signal, action="bet", confidence_adjusted=0.8, risk_score=0.2)

        stats.update(processed)
        self.assertEqual(stats.total_processed, 1)
        self.assertEqual(stats.total_bets, 1)
        self.assertEqual(stats.bet_rate, 1.0)
        self.assertEqual(stats.signals_by_type["score_delayed"], 1)
        self.assertEqual(stats.signals_by_sport["nfl"], 1)


class TestSignalProcessor(unittest.TestCase):
    """Test SignalProcessor class."""

    def setUp(self):
        self.config = LatencyConfig()
        self.backtest_config = BacktestConfig()
        self.processor = SignalProcessor(self.config, self.backtest_config)

    def test_initial_state(self):
        self.assertEqual(self.processor.processed_count, 0)
        self.assertFalse(self.processor.is_running)
        self.assertEqual(self.processor.stats.total_processed, 0)

    def test_process_signal_bet_action(self):
        """Test that high confidence, low risk signals result in 'bet' action."""
        gap = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_001",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap,
            description="Test",
            confidence=0.75,
        )

        processed = self.processor.process_signal(signal)
        self.assertEqual(processed.action, "bet")
        self.assertEqual(self.processor.processed_count, 1)
        self.assertEqual(self.processor.stats.total_bets, 1)

    def test_process_signal_skip_action(self):
        """Test that low confidence signals result in 'skip' action."""
        gap = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 0.5,  # Below threshold
            gap_seconds=0.5,
            confidence_score=0.5,
            severity=SeverityLevel.LOW,
        )
        signal = Signal(
            signal_id="sig_002",
            signal_type=SignalType.QUARTER_END_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap,
            description="Test",
            confidence=0.5,
        )

        processed = self.processor.process_signal(signal)
        self.assertEqual(processed.action, "skip")
        self.assertEqual(self.processor.stats.total_skipped, 1)

    def test_process_signal_monitor_action(self):
        """Test that medium confidence signals result in 'monitor' action."""
        gap = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 2.0,
            gap_seconds=2.0,
            confidence_score=0.6,
            severity=SeverityLevel.MEDIUM,
        )
        signal = Signal(
            signal_id="sig_003",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap,
            description="Test",
            confidence=0.6,
        )

        processed = self.processor.process_signal(signal)
        self.assertEqual(processed.action, "monitor")
        self.assertEqual(self.processor.stats.total_monitored, 1)

    def test_process_signals_batch(self):
        """Test processing multiple signals at once."""
        signals = []
        for i in range(5):
            gap = LatencyGap(
                event_id=f"test_{i}",
                sport=SportType.NFL,
                raw_timestamp=time.time(),
                broadcast_timestamp=time.time() + 5.0,
                gap_seconds=5.0,
                confidence_score=0.75,
                severity=SeverityLevel.HIGH,
            )
            signal = Signal(
                signal_id=f"sig_{i}",
                signal_type=SignalType.SCORE_DELAYED,
                event_id=f"test_{i}",
                sport=SportType.NFL,
                gap=gap,
                description="Test",
                confidence=0.75,
            )
            signals.append(signal)

        processed_signals = self.processor.process_signals(signals)
        self.assertEqual(len(processed_signals), 5)
        self.assertEqual(self.processor.stats.total_processed, 5)

    def test_add_remove_signal_handler(self):
        """Test adding and removing signal handlers."""
        async def handler(signal: Signal):
            pass

        self.processor.add_signal_handler(handler)
        self.assertEqual(len(self.processor._signal_handlers), 1)

        self.processor.remove_signal_handler(handler)
        self.assertEqual(len(self.processor._signal_handlers), 0)

    def test_get_stats(self):
        """Test getting signal processing statistics."""
        gap = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_001",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap,
            description="Test",
            confidence=0.75,
        )

        self.processor.process_signal(signal)
        stats = self.processor.get_stats()

        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["total_bets"], 1)
        self.assertEqual(stats["bet_rate"], 1.0)

    def test_get_recent_signals(self):
        """Test getting recent signals."""
        for i in range(5):
            gap = LatencyGap(
                event_id=f"test_{i}",
                sport=SportType.NFL,
                raw_timestamp=time.time(),
                broadcast_timestamp=time.time() + 5.0,
                gap_seconds=5.0,
                confidence_score=0.75,
                severity=SeverityLevel.HIGH,
            )
            signal = Signal(
                signal_id=f"sig_{i}",
                signal_type=SignalType.SCORE_DELAYED,
                event_id=f"test_{i}",
                sport=SportType.NFL,
                gap=gap,
                description="Test",
                confidence=0.75,
            )
            self.processor.process_signal(signal)

        recent = self.processor.get_recent_signals(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[-1].signal_id, "sig_4")

    def test_reset(self):
        """Test resetting signal processor state."""
        gap = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal = Signal(
            signal_id="sig_001",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap,
            description="Test",
            confidence=0.75,
        )

        self.processor.process_signal(signal)
        self.assertEqual(self.processor.stats.total_processed, 1)

        self.processor.reset()
        self.assertEqual(self.processor.stats.total_processed, 0)
        self.assertEqual(self.processor.processed_count, 0)

    def test_start_stop(self):
        """Test starting and stopping the processor."""
        self.assertFalse(self.processor.is_running)
        self.processor.start()
        self.assertTrue(self.processor.is_running)
        self.processor.stop()
        self.assertFalse(self.processor.is_running)

    def test_confidence_calculation(self):
        """Test confidence calculation with different severities."""
        # High severity should increase confidence
        gap_high = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal_high = Signal(
            signal_id="sig_001",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap_high,
            description="Test",
            confidence=0.75,
        )
        processed_high = self.processor.process_signal(signal_high)

        # Low severity should decrease confidence
        gap_low = LatencyGap(
            event_id="test_002",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.LOW,
        )
        signal_low = Signal(
            signal_id="sig_002",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_002",
            sport=SportType.NFL,
            gap=gap_low,
            description="Test",
            confidence=0.75,
        )
        processed_low = self.processor.process_signal(signal_low)

        self.assertGreater(processed_high.confidence_adjusted, processed_low.confidence_adjusted)

    def test_risk_calculation(self):
        """Test risk calculation with different gap sizes."""
        # Small gap should have higher risk
        gap_small = LatencyGap(
            event_id="test_001",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 0.5,
            gap_seconds=0.5,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal_small = Signal(
            signal_id="sig_001",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_001",
            sport=SportType.NFL,
            gap=gap_small,
            description="Test",
            confidence=0.75,
        )
        processed_small = self.processor.process_signal(signal_small)

        # Large gap should have lower risk
        gap_large = LatencyGap(
            event_id="test_002",
            sport=SportType.NFL,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 5.0,
            gap_seconds=5.0,
            confidence_score=0.75,
            severity=SeverityLevel.HIGH,
        )
        signal_large = Signal(
            signal_id="sig_002",
            signal_type=SignalType.SCORE_DELAYED,
            event_id="test_002",
            sport=SportType.NFL,
            gap=gap_large,
            description="Test",
            confidence=0.75,
        )
        processed_large = self.processor.process_signal(signal_large)

        self.assertGreater(processed_small.risk_score, processed_large.risk_score)


class TestFeedStats(unittest.TestCase):
    """Test FeedStats dataclass."""

    def test_initial_state(self):
        stats = FeedStats(feed_id="test_feed")
        self.assertEqual(stats.total_events_received, 0)
        self.assertIsNone(stats.start_time)
        self.assertEqual(stats.events_per_second, 0.0)

    def test_update_record(self):
        stats = FeedStats(feed_id="test_feed")
        event = FeedEvent(
            event_id="evt_001",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=time.time(),
        )
        record = FeedRecord(
            feed_id="test_feed",
            event=event,
            raw_timestamp=time.time(),
            broadcast_timestamp=time.time() + 0.1,
            processing_latency_ms=5.0,
        )

        stats.update_record(record)
        self.assertEqual(stats.total_records_processed, 1)
        self.assertEqual(stats.avg_processing_latency_ms, 5.0)

    def test_update_error(self):
        stats = FeedStats(feed_id="test_feed")
        stats.update_error()
        self.assertEqual(stats.total_errors, 1)


class TestFeedManagerStats(unittest.TestCase):
    """Test FeedManagerStats dataclass."""

    def test_initial_state(self):
        stats = FeedManagerStats()
        self.assertEqual(stats.total_feeds, 0)
        self.assertEqual(stats.active_feeds, 0)

    def test_update(self):
        stats = FeedManagerStats()
        feed_stats = FeedStats(feed_id="test_feed")
        feed_stats.start_time = time.time()
        feed_stats.total_events_received = 100

        stats.update(feed_stats)
        self.assertEqual(stats.total_feeds, 1)
        self.assertEqual(stats.active_feeds, 1)
        self.assertEqual(stats.total_events_received, 100)


class TestFeedManager(unittest.TestCase):
    """Test FeedManager class."""

    def setUp(self):
        self.config = PipelineConfig()
        self.manager = FeedManager(self.config)

    def test_initial_state(self):
        self.assertFalse(self.manager.is_running)
        self.assertEqual(len(self.manager.feed_ids), 0)

    def test_register_feed(self):
        """Test registering a feed."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)
        self.assertEqual(len(self.manager.feed_ids), 1)
        self.assertIn("test_feed", self.manager.feed_ids)

    def test_unregister_feed(self):
        """Test unregistering a feed."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)
        self.manager.unregister_feed("test_feed")
        self.assertEqual(len(self.manager.feed_ids), 0)

    def test_get_feed(self):
        """Test getting a feed by ID."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)
        retrieved = self.manager.get_feed("test_feed")
        self.assertEqual(retrieved, feed)

    def test_get_feed_config(self):
        """Test getting feed configuration."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)
        retrieved_config = self.manager.get_feed_config("test_feed")
        self.assertEqual(retrieved_config.sport, SportType.NFL)

    def test_start_stop_all_feeds(self):
        """Test starting and stopping all feeds."""
        async def mock_start():
            pass

        async def mock_stop():
            pass

        feed = MagicMock()
        feed.start = mock_start
        feed.stop = mock_stop
        feed.is_running = True

        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)

        asyncio.get_event_loop().run_until_complete(self.manager.start_all_feeds())
        self.assertTrue(self.manager.is_running)

        asyncio.get_event_loop().run_until_complete(self.manager.stop_all_feeds())
        self.assertFalse(self.manager.is_running)

    def test_process_feed_event(self):
        """Test processing a feed event."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)

        event = FeedEvent(
            event_id="evt_001",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=time.time(),
        )

        record = asyncio.get_event_loop().run_until_complete(
            self.manager.process_feed_event("test_feed", event)
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.feed_id, "test_feed")
        self.assertEqual(record.event.event_id, "evt_001")

    def test_get_next_event(self):
        """Test getting the next event from the queue."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)

        event = FeedEvent(
            event_id="evt_001",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=time.time(),
        )

        asyncio.get_event_loop().run_until_complete(
            self.manager.process_feed_event("test_feed", event)
        )

        record = asyncio.get_event_loop().run_until_complete(
            self.manager.get_next_event(timeout=1.0)
        )
        self.assertIsNotNone(record)

    def test_get_queue_size(self):
        """Test getting the event queue size."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)

        event = FeedEvent(
            event_id="evt_001",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=time.time(),
        )

        asyncio.get_event_loop().run_until_complete(
            self.manager.process_feed_event("test_feed", event)
        )

        self.assertEqual(self.manager.get_queue_size(), 1)

    def test_get_feed_stats(self):
        """Test getting statistics for a specific feed."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)

        event = FeedEvent(
            event_id="evt_001",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=time.time(),
        )

        asyncio.get_event_loop().run_until_complete(
            self.manager.process_feed_event("test_feed", event)
        )

        stats = self.manager.get_feed_stats("test_feed")
        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_events_received, 1)

    def test_get_summary(self):
        """Test getting a summary of all feed statistics."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)

        event = FeedEvent(
            event_id="evt_001",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=time.time(),
        )

        asyncio.get_event_loop().run_until_complete(
            self.manager.process_feed_event("test_feed", event)
        )

        summary = self.manager.get_summary()
        self.assertIn("total_feeds", summary)
        self.assertIn("total_events_received", summary)
        self.assertEqual(summary["total_feeds"], 1)

    def test_reset(self):
        """Test resetting feed manager state."""
        feed = MagicMock()
        config = FeedConfig(
            feed_id="test_feed",
            sport=SportType.NFL,
            url="http://test.com",
        )
        self.manager.register_feed("test_feed", feed, config)

        event = FeedEvent(
            event_id="evt_001",
            event_type=EventType.SCORE,
            sport=SportType.NFL,
            raw_timestamp=time.time(),
        )

        asyncio.get_event_loop().run_until_complete(
            self.manager.process_feed_event("test_feed", event)
        )

        self.manager.reset()
        self.assertEqual(self.manager.get_queue_size(), 0)

    def test_start_stop(self):
        """Test starting and stopping the feed manager."""
        self.assertFalse(self.manager.is_running)
        self.manager.start()
        self.assertTrue(self.manager.is_running)
        self.manager.stop()
        self.assertFalse(self.manager.is_running)

    def test_multiple_feeds(self):
        """Test managing multiple feeds."""
        feeds = []
        for i in range(3):
            feed = MagicMock()
            config = FeedConfig(
                feed_id=f"feed_{i}",
                sport=SportType.NFL,
                url=f"http://test{i}.com",
            )
            self.manager.register_feed(f"feed_{i}", feed, config)
            feeds.append(feed)

        self.assertEqual(len(self.manager.feed_ids), 3)

        for i, feed in enumerate(feeds):
            event = FeedEvent(
                event_id=f"evt_{i}",
                event_type=EventType.SCORE,
                sport=SportType.NFL,
                raw_timestamp=time.time(),
            )
            asyncio.get_event_loop().run_until_complete(
                self.manager.process_feed_event(f"feed_{i}", event)
            )

        summary = self.manager.get_summary()
        self.assertEqual(summary["total_events_received"], 3)


if __name__ == "__main__":
    unittest.main()
