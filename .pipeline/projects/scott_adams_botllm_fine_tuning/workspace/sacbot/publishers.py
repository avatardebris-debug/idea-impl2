"""Platform integrations — Twitter/X, LinkedIn, and RSS publishers."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GeneratedContent:
    """Content ready for publishing."""
    topic: str
    content_type: str  # "blog", "tweet", "linkedin"
    content: str
    title: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishResult:
    """Result of a publish attempt."""
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    latency_seconds: float = 0.0


class Publisher(ABC):
    """Abstract base class for platform publishers."""

    @abstractmethod
    def publish(self, content: GeneratedContent) -> PublishResult:
        """Publish content to the platform.

        Args:
            content: The content to publish

        Returns:
            PublishResult with success status and metadata
        """
        ...

    @abstractmethod
    def validate(self, content: GeneratedContent) -> tuple[bool, List[str]]:
        """Validate content for platform constraints.

        Args:
            content: The content to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        ...


class TwitterPublisher(Publisher):
    """Publisher for Twitter/X."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        mock: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.mock = mock
        self.max_chars = 280

    def validate(self, content: GeneratedContent) -> tuple[bool, List[str]]:
        """Validate content for Twitter constraints."""
        errors = []
        if content.content_type != "tweet":
            errors.append("Content type must be 'tweet' for Twitter")
        if len(content.content) > self.max_chars:
            errors.append(f"Content length {len(content.content)} exceeds {self.max_chars} chars")
        return len(errors) == 0, errors

    def publish(self, content: GeneratedContent) -> PublishResult:
        """Publish to Twitter/X."""
        start_time = time.time()
        is_valid, errors = self.validate(content)
        if not is_valid:
            return PublishResult(
                success=False,
                platform="twitter",
                error=f"Validation failed: {'; '.join(errors)}",
                latency_seconds=time.time() - start_time,
            )

        if self.mock:
            # Simulate successful publish
            post_id = f"mock_tw_{int(time.time())}"
            return PublishResult(
                success=True,
                platform="twitter",
                post_id=post_id,
                url=f"https://twitter.com/mock/status/{post_id}",
                latency_seconds=time.time() - start_time,
            )

        # TODO: Implement actual Twitter API v2 publish
        # Requires tweepy or direct API calls
        raise NotImplementedError("Twitter API integration not yet implemented")


class LinkedInPublisher(Publisher):
    """Publisher for LinkedIn."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        mock: bool = False,
    ):
        self.access_token = access_token
        self.mock = mock
        self.max_chars = 3000

    def validate(self, content: GeneratedContent) -> tuple[bool, List[str]]:
        """Validate content for LinkedIn constraints."""
        errors = []
        if content.content_type != "linkedin":
            errors.append("Content type must be 'linkedin' for LinkedIn")
        if len(content.content) > self.max_chars:
            errors.append(f"Content length {len(content.content)} exceeds {self.max_chars} chars")
        return len(errors) == 0, errors

    def publish(self, content: GeneratedContent) -> PublishResult:
        """Publish to LinkedIn."""
        start_time = time.time()
        is_valid, errors = self.validate(content)
        if not is_valid:
            return PublishResult(
                success=False,
                platform="linkedin",
                error=f"Validation failed: {'; '.join(errors)}",
                latency_seconds=time.time() - start_time,
            )

        if self.mock:
            post_id = f"mock_li_{int(time.time())}"
            return PublishResult(
                success=True,
                platform="linkedin",
                post_id=post_id,
                url=f"https://linkedin.com/posts/mock/{post_id}",
                latency_seconds=time.time() - start_time,
            )

        # TODO: Implement LinkedIn API v2 publish
        # Requires OAuth2 and POST to /ugcPosts
        raise NotImplementedError("LinkedIn API integration not yet implemented")


class RssPublisher(Publisher):
    """Publisher for RSS feed."""

    def __init__(
        self,
        feed_path: str = "output/rss/feed.xml",
        mock: bool = False,
    ):
        self.feed_path = Path(feed_path)
        self.mock = mock

    def validate(self, content: GeneratedContent) -> tuple[bool, List[str]]:
        """Validate content for RSS."""
        errors = []
        if not content.title:
            errors.append("RSS items require a title")
        if not content.content:
            errors.append("RSS items require content")
        return len(errors) == 0, errors

    def publish(self, content: GeneratedContent) -> PublishResult:
        """Publish to RSS feed."""
        start_time = time.time()
        is_valid, errors = self.validate(content)
        if not is_valid:
            return PublishResult(
                success=False,
                platform="rss",
                error=f"Validation failed: {'; '.join(errors)}",
                latency_seconds=time.time() - start_time,
            )

        if self.mock:
            # Simulate RSS entry creation
            entry = {
                "title": content.title,
                "content": content.content,
                "tags": content.tags,
                "timestamp": time.time(),
            }
            # In production, this would append to an RSS XML file
            return PublishResult(
                success=True,
                platform="rss",
                post_id=f"mock_rss_{int(time.time())}",
                url=f"/rss/entry/{content.title}",
                latency_seconds=time.time() - start_time,
            )

        # TODO: Implement RSS XML generation
        raise NotImplementedError("RSS feed integration not yet implemented")


class ContentPublisher:
    """Orchestrates publishing across multiple platforms."""

    def __init__(
        self,
        twitter: Optional[TwitterPublisher] = None,
        linkedin: Optional[LinkedInPublisher] = None,
        rss: Optional[RssPublisher] = None,
    ):
        self.twitter = twitter
        self.linkedin = linkedin
        self.rss = rss

    def publish_to_platform(
        self,
        content: GeneratedContent,
        platform: str = "twitter",
    ) -> PublishResult:
        """Publish content to a specific platform.

        Args:
            content: The content to publish
            platform: Platform name ("twitter", "linkedin", "rss")

        Returns:
            PublishResult
        """
        if platform == "twitter":
            if self.twitter:
                return self.twitter.publish(content)
            return PublishResult(
                success=False,
                platform="twitter",
                error="Twitter publisher not configured",
            )
        elif platform == "linkedin":
            if self.linkedin:
                return self.linkedin.publish(content)
            return PublishResult(
                success=False,
                platform="linkedin",
                error="LinkedIn publisher not configured",
            )
        elif platform == "rss":
            if self.rss:
                return self.rss.publish(content)
            return PublishResult(
                success=False,
                platform="rss",
                error="RSS publisher not configured",
            )
        else:
            return PublishResult(
                success=False,
                platform=platform,
                error=f"Unknown platform: {platform}",
            )

    def publish_to_all(
        self,
        content: GeneratedContent,
    ) -> Dict[str, PublishResult]:
        """Publish content to all configured platforms.

        Args:
            content: The content to publish

        Returns:
            Dict mapping platform name to PublishResult
        """
        results: Dict[str, PublishResult] = {}

        if self.twitter:
            results["twitter"] = self.twitter.publish(content)
        if self.linkedin:
            results["linkedin"] = self.linkedin.publish(content)
        if self.rss:
            results["rss"] = self.rss.publish(content)

        return results

    def get_summary(self, results: Dict[str, PublishResult]) -> str:
        """Get a summary of publish results.

        Args:
            results: Dict of platform to PublishResult

        Returns:
            Summary string
        """
        lines = ["Publish Summary:"]
        for platform, result in results.items():
            status = "✓" if result.success else "✗"
            lines.append(f"  {status} {platform}: {result.platform} ({result.post_id or 'no ID'})")
            if result.error:
                lines.append(f"    Error: {result.error}")
        return "\n".join(lines)
