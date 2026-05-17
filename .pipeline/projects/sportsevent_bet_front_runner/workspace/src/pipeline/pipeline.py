"""
Core pipeline for the Sports/Event Bet Front Runner.

Manages feed connections, message routing, latency detection, and signal generation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any, Callable, Coroutine, Dict, List, Optional

from src.pipeline.config import PipelineConfig
from src.pipeline.latency_detector import LatencyDetector
from src.pipeline.models import FeedRecord, LatencyGap, Signal, SportType

logger = logging.getLogger(__name__)


class Pipeline:
    """Core pipeline that manages feed connections and processes events."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.detector = LatencyDetector(self.config.latency)
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._signal_handlers: List[Callable[[Signal], Coroutine]] = []
        self._event_queue: deque = deque()
        self._lock = asyncio.Lock()
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def start_time(self) -> Optional[float]:
        return self._start_time

    @property
    def end_time(self) -> Optional[float]:
        return self._end_time

    @property
    def duration(self) -> Optional[float]:
        if self._start_time and self._end_time:
            return self._end_time - self._start_time
        return None

    def add_signal_handler(self, handler: Callable[[Signal], Coroutine]) -> None:
        """Add a signal handler.

        Args:
            handler: Async function to call when a signal is generated.
        """
        self._signal_handlers.append(handler)

    def register_feed(self, feed_adapter) -> None:
        """Register a feed adapter.

        Args:
            feed_adapter: A feed adapter instance to register.
        """
        if not hasattr(self, '_feeds'):
            self._feeds = []
        self._feeds.append(feed_adapter)
        logger.info(f"Registered feed: {feed_adapter}")

    def register_event_handler(self, handler) -> None:
        """Register an event handler.

        Args:
            handler: Event handler to register.
        """
        if not hasattr(self, '_event_handlers'):
            self._event_handlers = []
        self._event_handlers.append(handler)
        logger.info("Registered event handler")

    async def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.

        Returns:
            Dictionary with pipeline statistics.
        """
        return {
            "total_processed": self.detector.total_processed,
            "total_gaps_detected": self.detector.total_gaps_detected,
            "is_running": self._running,
            "duration": self.duration,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "signal_handlers": len(self._signal_handlers),
        }

    async def start(self) -> None:
        """Start the pipeline."""
        if self._running:
            return
        self._running = True
        self._start_time = time.time()
        logger.info("Pipeline started")

    async def stop(self) -> None:
        """Stop the pipeline."""
        if not self._running:
            return
        self._running = False
        self._end_time = time.time()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Pipeline stopped")

    async def process_record(self, record: FeedRecord) -> Optional[Signal]:
        """Process a feed record through the pipeline.

        Args:
            record: The feed record to process.

        Returns:
            A Signal if one was generated, None otherwise.
        """
        async with self._lock:
            gap = self.detector.process_record(record)

        if gap is None:
            return None

        signals = self.detector.generate_signals(gap)

        # Dispatch signals to handlers
        for signal in signals:
            for handler in self._signal_handlers:
                try:
                    await handler(signal)
                except Exception as e:
                    logger.error(f"Error in signal handler: {e}")

        return signals[0] if signals else None

    async def run_feed(self, feed_adapter) -> None:
        """Run a feed adapter through the pipeline.

        Args:
            feed_adapter: A feed adapter instance.
        """
        async for record in feed_adapter.get_events():
            if not self._running:
                break
            await self.process_record(record)
            await asyncio.sleep(0)  # Allow other coroutines to run

    async def run(self, feed_adapters: List) -> None:
        """Run the pipeline with multiple feed adapters.

        Args:
            feed_adapters: List of feed adapter instances.
        """
        await self.start()

        for adapter in feed_adapters:
            task = asyncio.create_task(self.run_feed(adapter))
            self._tasks.append(task)

        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.stop()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of pipeline execution.

        Returns:
            Dictionary with summary statistics.
        """
        summary = self.detector.get_summary()
        summary["pipeline_duration_seconds"] = self.duration
        summary["pipeline_start_time"] = self._start_time
        summary["pipeline_end_time"] = self._end_time
        return summary

    def reset(self) -> None:
        """Reset pipeline state."""
        self.detector.reset()
        self._start_time = None
        self._end_time = None
        self._tasks.clear()
