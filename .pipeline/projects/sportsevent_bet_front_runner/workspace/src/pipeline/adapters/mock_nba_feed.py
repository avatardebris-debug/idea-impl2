"""
Mock NBA game feed adapter for testing.

Simulates NBA game data with configurable latency gaps.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import AsyncIterator

from src.pipeline.feed_adapter import FeedAdapter
from src.pipeline.models import FeedEvent, FeedRecord, EventType, SportType

logger = logging.getLogger(__name__)


class MockNBAGameFeed(FeedAdapter):
    """Mock NBA game feed that simulates game events."""

    def __init__(self, config: dict = None):
        super().__init__(feed_id="mock_nba", config=config or {})
        self._seed = self.config.get("seed", 42)
        self._event_counter = 0
        self._latency_gaps = self.config.get("latency_gaps", [3.0, 6.0, 15.0])
        self._gap_index = 0

    async def connect(self) -> None:
        logger.info("Connected to mock NBA game feed")

    async def disconnect(self) -> None:
        logger.info("Disconnected from mock NBA game feed")

    async def get_events(self) -> AsyncIterator[FeedRecord]:
        """Generate mock NBA game events with periodic latency gaps."""
        random.seed(self._seed)
        base_time = time.time()
        max_events = self.config.get("max_events", 100)

        while self._running and self._event_counter < max_events:
            self._event_counter += 1

            # Determine if this event should have a latency gap
            if self._gap_index < len(self._latency_gaps):
                gap_seconds = self._latency_gaps[self._gap_index]
                self._gap_index += 1
            else:
                gap_seconds = random.uniform(0.1, 1.0)

            raw_ts = base_time - (self._event_counter * 1.5)
            broadcast_ts = raw_ts + gap_seconds

            # Generate event type
            event_types = [
                EventType.SCORE,
                EventType.PLAY,
                EventType.HALF_END,
                EventType.PLAY,
                EventType.SCORE,
            ]
            event_type = random.choice(event_types)

            event = FeedEvent(
                event_id=f"nba_{self._event_counter:04d}",
                sport=SportType.NBA,
                event_type=event_type,
                raw_timestamp=raw_ts,
                data={
                    "team": random.choice(["LAL", "GSW", "BOS", "MIA"]),
                    "play_type": random.choice(["shot", "dunk", "three_pointer"]),
                    "quarter": random.randint(1, 4),
                },
            )

            record = FeedRecord(
                feed_id=self.feed_id,
                event=event,
                raw_timestamp=raw_ts,
                broadcast_timestamp=broadcast_ts,
                processing_latency_ms=random.uniform(5.0, 30.0),
            )

            yield record
            await asyncio.sleep(0.1)
