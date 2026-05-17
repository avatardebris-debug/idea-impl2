"""
Feed manager for the Sports/Event Bet Front Runner pipeline.

Manages multiple feed adapters, handles connection lifecycle,
and provides unified event access across feeds.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Set

from src.pipeline.config import FeedConfig, PipelineConfig
from src.pipeline.models import FeedEvent, FeedRecord, SportType

logger = logging.getLogger(__name__)


@dataclass
class FeedStats:
    """Statistics for a single feed."""
    feed_id: str
    total_events_received: int = 0
    total_records_processed: int = 0
    total_errors: int = 0
    start_time: Optional[float] = None
    last_event_time: Optional[float] = None
    avg_processing_latency_ms: float = 0.0
    events_by_sport: Dict[str, int] = field(default_factory=dict)
    events_by_type: Dict[str, int] = field(default_factory=dict)

    def update_record(self, record: FeedRecord) -> None:
        """Update statistics with a new record."""
        self.total_records_processed += 1
        self.last_event_time = time.time()
        self.avg_processing_latency_ms = (
            (self.avg_processing_latency_ms * (self.total_records_processed - 1) + record.processing_latency_ms)
            / self.total_records_processed
        )

    def update_error(self) -> None:
        """Update error count."""
        self.total_errors += 1

    @property
    def uptime_seconds(self) -> float:
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    @property
    def events_per_second(self) -> float:
        if self.uptime_seconds == 0:
            return 0.0
        return self.total_events_received / self.uptime_seconds


@dataclass
class FeedManagerStats:
    """Aggregate statistics for all feeds."""
    total_feeds: int = 0
    active_feeds: int = 0
    total_events_received: int = 0
    total_records_processed: int = 0
    total_errors: int = 0
    feeds: Dict[str, FeedStats] = field(default_factory=dict)

    def update(self, feed_stats: FeedStats) -> None:
        """Update aggregate statistics with a feed's stats."""
        self.feeds[feed_stats.feed_id] = feed_stats
        self.total_feeds = len(self.feeds)
        self.active_feeds = sum(1 for f in self.feeds.values() if f.start_time is not None)
        self.total_events_received = sum(f.total_events_received for f in self.feeds.values())
        self.total_records_processed = sum(f.total_records_processed for f in self.feeds.values())
        self.total_errors = sum(f.total_errors for f in self.feeds.values())


class FeedManager:
    """
    Manages multiple feed adapters and provides unified event access.

    Handles connection lifecycle, event routing, and statistics collection
    across all configured feeds.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._feeds: Dict[str, Any] = {}  # feed_id -> feed adapter
        self._feed_configs: Dict[str, FeedConfig] = {}
        self._feed_stats: Dict[str, FeedStats] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._running = False
        self._start_time: Optional[float] = None
        self._aggregate_stats = FeedManagerStats()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def feed_ids(self) -> List[str]:
        return list(self._feeds.keys())

    @property
    def active_feed_count(self) -> int:
        return sum(1 for f in self._feeds.values() if (f.is_running if hasattr(f, 'is_running') else True))

    @property
    def aggregate_stats(self) -> FeedManagerStats:
        return self._aggregate_stats

    def register_feed(self, feed_id: str, feed: Any, config: FeedConfig) -> None:
        """Register a feed adapter with the manager."""
        self._feeds[feed_id] = feed
        self._feed_configs[feed_id] = config
        self._feed_stats[feed_id] = FeedStats(feed_id=feed_id)
        logger.info(f"Registered feed: {feed_id} ({config.sport})")

    def unregister_feed(self, feed_id: str) -> None:
        """Unregister a feed adapter."""
        if feed_id in self._feeds:
            del self._feeds[feed_id]
            del self._feed_configs[feed_id]
            del self._feed_stats[feed_id]
            logger.info(f"Unregistered feed: {feed_id}")

    def get_feed(self, feed_id: str) -> Optional[Any]:
        """Get a feed adapter by ID."""
        return self._feeds.get(feed_id)

    def get_feed_config(self, feed_id: str) -> Optional[FeedConfig]:
        """Get the configuration for a feed."""
        return self._feed_configs.get(feed_id)

    def get_all_feeds(self) -> Dict[str, Any]:
        """Get all registered feeds."""
        return dict(self._feeds)

    async def start_all_feeds(self) -> None:
        """Start all registered feeds."""
        self._running = True
        self._start_time = time.time()

        for feed_id, feed in self._feeds.items():
            try:
                if hasattr(feed, 'start'):
                    await feed.start()
                elif hasattr(feed, '__aenter__'):
                    await feed.__aenter__()
                self._feed_stats[feed_id].start_time = time.time()
                logger.info(f"Started feed: {feed_id}")
            except Exception as e:
                logger.error(f"Failed to start feed {feed_id}: {e}")
                self._feed_stats[feed_id].update_error()

        self._aggregate_stats.update(self._feed_stats[self.feed_ids[0]] if self.feed_ids else FeedStats(feed_id="none"))
        logger.info(f"Started {len(self._feeds)} feeds")

    async def stop_all_feeds(self) -> None:
        """Stop all registered feeds."""
        self._running = False

        for feed_id, feed in self._feeds.items():
            try:
                if hasattr(feed, 'stop'):
                    await feed.stop()
                elif hasattr(feed, '__aexit__'):
                    await feed.__aexit__(None, None, None)
                logger.info(f"Stopped feed: {feed_id}")
            except Exception as e:
                logger.error(f"Failed to stop feed {feed_id}: {e}")

        logger.info(f"Stopped {len(self._feeds)} feeds")

    async def process_feed_event(self, feed_id: str, event: FeedEvent) -> Optional[FeedRecord]:
        """
        Process an event from a specific feed and create a FeedRecord.

        Returns the FeedRecord if successful, None otherwise.
        """
        if feed_id not in self._feed_stats:
            logger.warning(f"Unknown feed_id: {feed_id}")
            return None

        stats = self._feed_stats[feed_id]
        stats.total_events_received += 1

        try:
            # Create a FeedRecord from the event
            record = FeedRecord(
                feed_id=feed_id,
                event=event,
                raw_timestamp=event.raw_timestamp,
                broadcast_timestamp=event.raw_timestamp + 0.1,  # Simulated broadcast delay
                processing_latency_ms=5.0,  # Simulated processing latency
            )

            stats.update_record(record)
            await self._event_queue.put(record)

            # Update aggregate stats
            self._aggregate_stats.update(stats)

            return record

        except Exception as e:
            stats.update_error()
            logger.error(f"Error processing event from {feed_id}: {e}")
            return None

    async def get_next_event(self, timeout: Optional[float] = None) -> Optional[FeedRecord]:
        """Get the next event from the queue."""
        try:
            if timeout:
                return await asyncio.wait_for(self._event_queue.get(), timeout=timeout)
            return await self._event_queue.get()
        except asyncio.TimeoutError:
            return None
        except asyncio.CancelledError:
            return None

    def get_queue_size(self) -> int:
        """Get the current size of the event queue."""
        return self._event_queue.qsize()

    def get_feed_stats(self, feed_id: str) -> Optional[FeedStats]:
        """Get statistics for a specific feed."""
        return self._feed_stats.get(feed_id)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all feeds."""
        return {
            feed_id: {
                "total_events_received": stats.total_events_received,
                "total_records_processed": stats.total_records_processed,
                "total_errors": stats.total_errors,
                "avg_processing_latency_ms": stats.avg_processing_latency_ms,
                "events_per_second": stats.events_per_second,
                "uptime_seconds": stats.uptime_seconds,
                "events_by_sport": stats.events_by_sport,
                "events_by_type": stats.events_by_type,
            }
            for feed_id, stats in self._feed_stats.items()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all feed statistics."""
        return {
            "total_feeds": len(self._feeds),
            "active_feeds": self.active_feed_count,
            "total_events_received": self._aggregate_stats.total_events_received,
            "total_records_processed": self._aggregate_stats.total_records_processed,
            "total_errors": self._aggregate_stats.total_errors,
            "queue_size": self.get_queue_size(),
            "feeds": self.get_all_stats(),
        }

    def reset(self) -> None:
        """Reset all feed manager state."""
        self._feed_stats.clear()
        self._aggregate_stats = FeedManagerStats()
        self._start_time = None
        # Clear the event queue
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("Feed manager reset")

    def start(self) -> None:
        """Start the feed manager."""
        self._running = True
        self._start_time = time.time()
        logger.info("Feed manager started")

    def stop(self) -> None:
        """Stop the feed manager."""
        self._running = False
        logger.info("Feed manager stopped")
