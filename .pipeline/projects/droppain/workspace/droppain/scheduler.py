"""Scheduler for droppain.

Handles scheduling and timing of campaign content publishing.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from droppain.config import Config, get_config
from droppain.planner import ContentBrief

logger = logging.getLogger(__name__)


@dataclass
class ScheduledPost:
    """A post scheduled for a specific time."""

    content: ContentBrief
    scheduled_at: datetime
    platform: str
    post_id: Optional[str] = None
    status: str = "scheduled"  # scheduled, published, failed


class CampaignScheduler:
    """Schedules campaign content for optimal publishing times."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the scheduler.

        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        self.config = config or get_config()
        self._scheduled_posts: List[ScheduledPost] = []

    def schedule_content(
        self,
        briefs: List[ContentBrief],
        start_date: Optional[datetime] = None,
        timezone: Optional[str] = None,
    ) -> List[ScheduledPost]:
        """Schedule content for publishing.

        Args:
            briefs: List of content briefs to schedule.
            start_date: Start date for scheduling. Defaults to now.
            timezone: Timezone string. Defaults to config timezone.

        Returns:
            List of ScheduledPost objects.
        """
        if start_date is None:
            start_date = datetime.now()

        tz = timezone or self.config.default_timezone
        logger.info(
            "Scheduling %d posts starting from %s (tz=%s)",
            len(briefs),
            start_date.isoformat(),
            tz,
        )

        self._scheduled_posts = []

        for i, brief in enumerate(briefs):
            # Calculate scheduled time with staggered intervals
            interval_hours = self._get_interval_for_platform(brief.platform)
            scheduled_time = start_date + timedelta(hours=i * interval_hours)

            post = ScheduledPost(
                content=brief,
                scheduled_at=scheduled_time,
                platform=brief.platform,
            )
            self._scheduled_posts.append(post)

        logger.info("Scheduled %d posts", len(self._scheduled_posts))
        return self._scheduled_posts

    def _get_interval_for_platform(self, platform: str) -> float:
        """Get recommended posting interval for a platform (in hours)."""
        intervals = {
            "facebook": 24,
            "instagram": 12,
            "tiktok": 6,
            "google": 168,  # weekly
            "email": 48,
        }
        return intervals.get(platform, 24)

    def get_upcoming_posts(
        self,
        from_time: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[ScheduledPost]:
        """Get upcoming scheduled posts.

        Args:
            from_time: Start time for query. Defaults to now.
            limit: Maximum number of posts to return.

        Returns:
            List of ScheduledPost objects.
        """
        if from_time is None:
            from_time = datetime.now()

        upcoming = [
            post for post in self._scheduled_posts
            if post.scheduled_at >= from_time and post.status == "scheduled"
        ]
        upcoming.sort(key=lambda p: p.scheduled_at)
        return upcoming[:limit]

    def publish_post(self, post: ScheduledPost) -> bool:
        """Publish a scheduled post.

        Args:
            post: The ScheduledPost to publish.

        Returns:
            True if published successfully.
        """
        logger.info("Publishing post for %s at %s", post.platform, post.scheduled_at)

        # In a real implementation, this would call the platform's API
        post.status = "published"
        post.post_id = f"pub_{random.randint(1000, 9999)}"
        return True

    def get_schedule_summary(self) -> dict:
        """Get a summary of the current schedule."""
        total = len(self._scheduled_posts)
        scheduled = sum(1 for p in self._scheduled_posts if p.status == "scheduled")
        published = sum(1 for p in self._scheduled_posts if p.status == "published")
        failed = sum(1 for p in self._scheduled_posts if p.status == "failed")

        platforms = {}
        for post in self._scheduled_posts:
            platforms[post.platform] = platforms.get(post.platform, 0) + 1

        return {
            "total": total,
            "scheduled": scheduled,
            "published": published,
            "failed": failed,
            "platforms": platforms,
        }
