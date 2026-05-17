"""Tests for droppain.scheduler module."""

import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from droppain.scheduler import CampaignScheduler, ScheduledPost
from droppain.planner import ContentBrief


class TestScheduledPost:
    """Tests for ScheduledPost dataclass."""

    def test_scheduled_post_creation(self):
        """Test creating a ScheduledPost."""
        brief = ContentBrief(
            title="Test",
            copy="Body",
            target_audience="General",
            platform="facebook",
        )
        post = ScheduledPost(
            content=brief,
            scheduled_at=datetime.now(),
            platform="facebook",
        )
        assert post.status == "scheduled"
        assert post.post_id is None


class TestCampaignScheduler:
    """Tests for CampaignScheduler."""

    def test_init_with_config(self):
        """Test initialization with config."""
        config = type("Config", (), {
            "default_timezone": "UTC",
        })()
        scheduler = CampaignScheduler(config=config)
        assert scheduler.config == config

    def test_schedule_content(self):
        """Test scheduling content."""
        config = type("Config", (), {
            "default_timezone": "UTC",
        })()
        scheduler = CampaignScheduler(config=config)

        briefs = [
            ContentBrief(title="Post 1", copy="Body 1", target_audience="General", platform="facebook"),
            ContentBrief(title="Post 2", copy="Body 2", target_audience="General", platform="facebook"),
            ContentBrief(title="Post 3", copy="Body 3", target_audience="General", platform="facebook"),
        ]

        start = datetime(2024, 1, 1, 10, 0, 0)
        posts = scheduler.schedule_content(briefs, start_date=start)

        assert len(posts) == 3
        assert posts[0].scheduled_at == start
        # facebook: 24h interval
        assert posts[1].scheduled_at == start + timedelta(hours=24)
        assert posts[2].scheduled_at == start + timedelta(hours=48)

    def test_get_interval_for_platform(self):
        """Test interval calculation for different platforms."""
        config = type("Config", (), {
            "default_timezone": "UTC",
        })()
        scheduler = CampaignScheduler(config=config)

        assert scheduler._get_interval_for_platform("facebook") == 24
        assert scheduler._get_interval_for_platform("instagram") == 12
        assert scheduler._get_interval_for_platform("tiktok") == 6
        assert scheduler._get_interval_for_platform("google") == 168
        assert scheduler._get_interval_for_platform("email") == 48
        assert scheduler._get_interval_for_platform("unknown") == 24

    def test_get_upcoming_posts(self):
        """Test getting upcoming posts."""
        config = type("Config", (), {
            "default_timezone": "UTC",
        })()
        scheduler = CampaignScheduler(config=config)

        brief = ContentBrief(title="Test", copy="Body", target_audience="General", platform="facebook")
        start = datetime.now() - timedelta(hours=1)  # Past
        posts = scheduler.schedule_content([brief], start_date=start)

        # Should not be upcoming
        upcoming = scheduler.get_upcoming_posts(limit=10)
        assert len(upcoming) == 0

        # Schedule in future
        future_start = datetime.now() + timedelta(hours=1)
        posts = scheduler.schedule_content([brief], start_date=future_start)
        upcoming = scheduler.get_upcoming_posts(limit=10)
        assert len(upcoming) == 1

    def test_publish_post(self):
        """Test publishing a post."""
        config = type("Config", (), {
            "default_timezone": "UTC",
        })()
        scheduler = CampaignScheduler(config=config)

        brief = ContentBrief(title="Test", copy="Body", target_audience="General", platform="facebook")
        post = ScheduledPost(
            content=brief,
            scheduled_at=datetime.now(),
            platform="facebook",
        )

        result = scheduler.publish_post(post)
        assert result is True
        assert post.status == "published"
        assert post.post_id is not None

    def test_get_schedule_summary(self):
        """Test getting schedule summary."""
        config = type("Config", (), {
            "default_timezone": "UTC",
        })()
        scheduler = CampaignScheduler(config=config)

        briefs = [
            ContentBrief(title="Post 1", copy="Body 1", target_audience="General", platform="facebook"),
            ContentBrief(title="Post 2", copy="Body 2", target_audience="General", platform="instagram"),
        ]
        scheduler.schedule_content(briefs)

        # Publish one
        scheduler.publish_post(scheduler._scheduled_posts[0])

        summary = scheduler.get_schedule_summary()
        assert summary["total"] == 2
        assert summary["scheduled"] == 1
        assert summary["published"] == 1
        assert summary["failed"] == 0
        assert summary["platforms"]["facebook"] == 1
        assert summary["platforms"]["instagram"] == 1
