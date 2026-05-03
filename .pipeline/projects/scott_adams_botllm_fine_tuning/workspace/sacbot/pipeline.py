"""End-to-end content pipeline — orchestrates topic research, generation, review, and publishing."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sacbot.config import Config
from sacbot.generator import generate, GenerationResult
from sacbot.topic_research import suggest_topics
from sacbot.review import review, ReviewResult
from sacbot.types import ContentType
from sacbot.publishers import ContentPublisher, GeneratedContent, PublishResult
from sacbot.scheduler import Scheduler, ScheduledContent
from sacbot.dashboard import PipelineDashboard, PipelineStats

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""
    success: bool
    topics_researched: int = 0
    content_generated: int = 0
    content_reviewed: int = 0
    content_published: int = 0
    content_failed: int = 0
    publish_results: Dict[str, PublishResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    latency_seconds: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class ContentPipeline:
    """End-to-end content pipeline orchestrator."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.dashboard = PipelineDashboard()
        self.scheduler = Scheduler(
            interval_seconds=self.config.scheduler_interval_seconds,
        )
        self._stats = PipelineStats()
        self._start_time: Optional[float] = None

    def run(
        self,
        topic: Optional[str] = None,
        content_type: ContentType = "blog",
        n_topics: int = 1,
        publish: bool = True,
    ) -> PipelineResult:
        """Run the full pipeline for one or more topics.

        Args:
            topic: Specific topic to research (if None, auto-research)
            content_type: Type of content to generate
            n_topics: Number of topics to research
            publish: Whether to publish the content

        Returns:
            PipelineResult with summary statistics
        """
        self._start_time = time.time()
        result = PipelineResult(start_time=self._start_time)

        try:
            # Step 1: Topic Research
            if topic:
                topics = [topic]
            else:
                topics = suggest_topics(n_topics=n_topics)
            result.topics_researched = len(topics)
            self._stats.topics_researched += len(topics)

            # Step 2: Content Generation
            generated_contents: List[GeneratedContent] = []
            for t in topics:
                gen_result = generate(
                    topic=t,
                    content_type=content_type,
                    corpus_path=self.config.corpus_path,
                    n_few_shot=self.config.n_few_shot,
                    model=self.config.openai.model,
                    api_key=self.config.openai.api_key,
                    temperature=self.config.temperature,
                )
                generated_contents.append(GeneratedContent(
                    topic=t,
                    content_type=content_type,
                    content=gen_result.content,
                    title=gen_result.title,
                    tags=gen_result.tags,
                    hashtags=gen_result.hashtags,
                    metadata=gen_result.metadata,
                ))
            result.content_generated = len(generated_contents)
            self._stats.content_generated += len(generated_contents)

            # Step 3: Content Review
            reviewed_contents: List[ReviewResult] = []
            for gc in generated_contents:
                review_result = review(gc.content, gc.content_type)
                reviewed_contents.append(review_result)
            result.content_reviewed = len(reviewed_contents)
            self._stats.content_reviewed += len(reviewed_contents)

            # Step 4: Publishing
            if publish:
                publisher = ContentPublisher(
                    twitter=None,  # TODO: Initialize from config
                    linkedin=None,
                    rss=None,
                )
                for gc, rr in zip(generated_contents, reviewed_contents):
                    if rr.passed:
                        pub_result = publisher.publish_to_platform(gc, content_type)
                        result.publish_results[gc.topic] = pub_result
                        if pub_result.success:
                            result.content_published += 1
                            self._stats.published_count += 1
                        else:
                            result.content_failed += 1
                            self._stats.failed_count += 1
                            result.errors.append(f"Failed to publish {gc.topic}: {pub_result.error}")
                    else:
                        result.errors.append(f"Content failed review for topic {gc.topic}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Pipeline error: {e}", exc_info=True)
        finally:
            result.end_time = time.time()
            result.success = result.content_published > 0 or not result.errors
            result.latency_seconds = result.duration
            self._update_dashboard_stats()

        return result

    def schedule_topic(
        self,
        topic: str,
        content_type: ContentType = "blog",
        publish_at: Optional[datetime] = None,
    ) -> ScheduledContent:
        """Schedule a topic for future processing."""
        scheduled = self.scheduler.schedule(
            content=topic,
            content_type=content_type,
            topic=topic,
            publish_at=publish_at,
        )
        return scheduled

    def run_scheduled(self) -> List[PipelineResult]:
        """Run all scheduled topics."""
        results = []
        while not self.scheduler.queue.is_empty():
            scheduled = self.scheduler.queue.dequeue()
            if scheduled:
                result = self.run(
                    topic=scheduled.content,
                    content_type=scheduled.content_type,
                    publish=True,
                )
                results.append(result)
        return results

    def get_dashboard(self) -> str:
        """Get the current dashboard string."""
        self._update_dashboard_stats()
        return self.dashboard.render()

    def _update_dashboard_stats(self) -> None:
        """Update dashboard stats from internal counters."""
        self.dashboard.update_stats(self._stats)

    def get_stats(self) -> PipelineStats:
        """Get current pipeline statistics."""
        self._update_dashboard_stats()
        return self._stats


# Convenience function for quick pipeline runs
def run_pipeline(
    topic: Optional[str] = None,
    content_type: ContentType = "blog",
    n_topics: int = 1,
    publish: bool = True,
    config: Optional[Config] = None,
) -> PipelineResult:
    """Run the full content pipeline.

    Args:
        topic: Specific topic to research
        content_type: Type of content to generate
        n_topics: Number of topics to research
        publish: Whether to publish the content
        config: Optional configuration

    Returns:
        PipelineResult with summary statistics
    """
    pipeline = ContentPipeline(config=config)
    return pipeline.run(
        topic=topic,
        content_type=content_type,
        n_topics=n_topics,
        publish=publish,
    )
