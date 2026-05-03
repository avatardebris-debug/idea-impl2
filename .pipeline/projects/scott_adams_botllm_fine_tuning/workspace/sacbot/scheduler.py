"""Content scheduler — queues and dispatches content at configured intervals."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from queue import PriorityQueue, Empty


@dataclass(order=True)
class ScheduledContent:
    """Content scheduled for publishing."""
    publish_at: float  # Unix timestamp for priority ordering
    content_type: str = ""
    topic: str = ""
    content: str = ""
    title: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, in_progress, published, failed
    post_id: Optional[str] = None
    error: Optional[str] = None


class ContentQueue:
    """Thread-safe priority queue for scheduled content."""

    def __init__(self):
        self._queue = PriorityQueue()
        self._lock = threading.Lock()
        self._counter = 0

    def enqueue(self, content: ScheduledContent) -> None:
        """Add content to the queue."""
        with self._lock:
            self._counter += 1
            # Use counter as tiebreaker for same publish_at times
            self._queue.put((content.publish_at, self._counter, content))

    def dequeue(self, timeout: float = 0) -> Optional[ScheduledContent]:
        """Remove and return the next item from the queue."""
        try:
            _, _, content = self._queue.get(timeout=timeout)
            return content
        except Empty:
            return None

    def peek(self) -> Optional[ScheduledContent]:
        """Look at the next item without removing it."""
        try:
            _, _, content = self._queue.get(block=False)
            self._queue.put((content.publish_at, self._counter, content))
            return content
        except Empty:
            return None

    def size(self) -> int:
        """Get the current queue size."""
        return self._queue.qsize()

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()


class Scheduler:
    """Content scheduler that dispatches queued content at configured intervals."""

    def __init__(
        self,
        interval_seconds: float = 14400.0,  # Default: 4 hours
        queue: Optional[ContentQueue] = None,
    ):
        self.interval_seconds = interval_seconds
        self.queue = queue or ContentQueue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats = {
            "total_queued": 0,
            "total_published": 0,
            "total_failed": 0,
            "last_publish_time": None,
            "next_publish_time": None,
        }

    def schedule(
        self,
        content: str,
        content_type: str = "blog",
        topic: str = "",
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        publish_at: Optional[datetime] = None,
    ) -> ScheduledContent:
        """Schedule content for publishing.

        Args:
            content: The content text
            content_type: Type of content
            topic: Topic of the content
            title: Optional title
            tags: Optional tags
            hashtags: Optional hashtags
            metadata: Optional metadata dict
            publish_at: When to publish (default: now + interval)

        Returns:
            ScheduledContent object
        """
        if publish_at is None:
            publish_at = datetime.now() + __import__('datetime').timedelta(seconds=self.interval_seconds)

        scheduled = ScheduledContent(
            publish_at=publish_at.timestamp(),
            content_type=content_type,
            topic=topic,
            content=content,
            title=title,
            tags=tags or [],
            hashtags=hashtags or [],
            metadata=metadata or {},
        )
        self.queue.enqueue(scheduled)
        self._stats["total_queued"] += 1
        return scheduled

    def dispatch(self, content: ScheduledContent, publisher_func=None) -> bool:
        """Dispatch a single piece of content.

        Args:
            content: The content to dispatch
            publisher_func: Optional callable(content) -> PublishResult

        Returns:
            True if dispatch was successful
        """
        content.status = "in_progress"
        try:
            if publisher_func:
                result = publisher_func(content)
                content.post_id = getattr(result, 'post_id', None)
                content.error = getattr(result, 'error', None)
                content.status = "published" if result.success else "failed"
            else:
                # Mock dispatch for testing
                content.post_id = f"mock_{int(time.time())}"
                content.status = "published"

            if content.status == "published":
                self._stats["total_published"] += 1
            else:
                self._stats["total_failed"] += 1

            self._stats["last_publish_time"] = time.time()
            return content.status == "published"
        except Exception as e:
            content.status = "failed"
            content.error = str(e)
            self._stats["total_failed"] += 1
            return False

    def _dispatch_loop(self) -> None:
        """Internal dispatch loop (runs in thread)."""
        while self._running:
            now = time.time()
            next_item = self.queue.peek()

            if next_item and next_item.publish_at <= now:
                content = self.queue.dequeue()
                if content:
                    self.dispatch(content)
            else:
                time.sleep(1)

    def run(self) -> None:
        """Start the scheduler loop."""
        self._running = True
        self._thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._thread = None

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return self._stats.copy()

    def get_next_publish_time(self) -> Optional[datetime]:
        """Get the next scheduled publish time."""
        next_item = self.queue.peek()
        if next_item:
            return datetime.fromtimestamp(next_item.publish_at)
        return None

    def clear_queue(self) -> int:
        """Clear the queue and return the number of items removed."""
        count = 0
        while not self.queue.is_empty():
            self.queue.dequeue()
            count += 1
        return count
