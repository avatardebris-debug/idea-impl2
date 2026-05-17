"""
Base feed adapter for the Sports/Event Bet Front Runner Pipeline.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.pipeline.models import FeedRecord

logger = logging.getLogger(__name__)


class FeedAdapter(ABC):
    """Abstract base class for feed adapters."""

    def __init__(self, feed_id: str, config: dict = None):
        self.feed_id = feed_id
        self.config = config or {}
        self._running = False

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the feed."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the feed."""
        pass

    @abstractmethod
    async def get_events(self) -> AsyncIterator[FeedRecord]:
        """Get events from the feed."""
        pass

    async def start(self) -> None:
        """Start the feed adapter."""
        self._running = True
        await self.connect()
        logger.info(f"Feed adapter {self.feed_id} started")

    async def stop(self) -> None:
        """Stop the feed adapter."""
        self._running = False
        await self.disconnect()
        logger.info(f"Feed adapter {self.feed_id} stopped")
