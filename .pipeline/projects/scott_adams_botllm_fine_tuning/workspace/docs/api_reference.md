# API Reference

## Overview

The `sacbot` package provides a complete content generation pipeline for producing Scott Adams-style content across multiple platforms.

## Modules

### `sacbot.config`

Configuration dataclasses for all pipeline components.

#### `Config`

Top-level configuration.

```python
from sacbot.config import Config

config = Config.from_env()  # Load from environment variables
config = Config.from_dict({"openai": {"api_key": "sk-..."}})  # Load from dict
```

**Attributes:**
- `twitter` (`TwitterConfig`): Twitter/X API configuration
- `linkedin` (`LinkedInConfig`): LinkedIn API configuration
- `rss` (`RSSConfig`): RSS feed configuration
- `openai` (`OpenAIConfig`): OpenAI API configuration
- `scheduler_interval_seconds` (`float`): Publishing interval in seconds
- `style_threshold` (`float`): Style match threshold (0-1)
- `default_content_type` (`str`): Default content type
- `topics_path` (`str`): Path to topics.json
- `corpus_path` (`Optional[str]`): Path to corpus.jsonl
- `n_few_shot` (`int`): Number of few-shot examples
- `temperature` (`float`): LLM sampling temperature
- `output_dir` (`str`): Output directory
- `log_level` (`str`): Logging level
- `extra_headers` (`Dict[str, str]`): Extra HTTP headers
- `proxy` (`Optional[str]`): HTTP proxy URL

#### `TwitterConfig`

```python
from sacbot.config import TwitterConfig

config = TwitterConfig(
    api_key="...",
    api_secret="...",
    access_token="...",
    access_token_secret="...",
    mock=True,
)
```

**Attributes:**
- `api_key` (`str`): Twitter API key
- `api_secret` (`str`): Twitter API secret
- `access_token` (`str`): Twitter access token
- `access_token_secret` (`str`): Twitter access token secret
- `mock` (`bool`): Use mock publisher

#### `LinkedInConfig`

```python
from sacbot.config import LinkedInConfig

config = LinkedInConfig(
    access_token="...",
    mock=True,
)
```

**Attributes:**
- `access_token` (`str`): LinkedIn access token
- `mock` (`bool`): Use mock publisher

#### `RSSConfig`

```python
from sacbot.config import RSSConfig

config = RSSConfig(
    feed_path="output/rss/feed.xml",
    site_name="Scott Adams Bot",
    site_url="https://example.com",
    description="AI-generated content in Scott Adams' style",
    mock=True,
)
```

**Attributes:**
- `feed_path` (`str`): RSS feed file path
- `site_name` (`str`): Site name
- `site_url` (`str`): Site URL
- `description` (`str`): Site description
- `mock` (`bool`): Use mock publisher

#### `OpenAIConfig`

```python
from sacbot.config import OpenAIConfig

config = OpenAIConfig(
    api_key="sk-...",
    model="gpt-4o",
    base_url=None,
)
```

**Attributes:**
- `api_key` (`str`): OpenAI API key
- `model` (`str`): OpenAI model to use
- `base_url` (`Optional[str]`): Custom OpenAI base URL

---

### `sacbot.research`

Topic research module.

#### `topic_research(n_topics: int = 1) -> List[str]`

Research and return a list of topics.

```python
from sacbot.research import topic_research

topics = topic_research(n_topics=3)
print(topics)  # ["Productivity", "AI Safety", "Remote Work"]
```

**Parameters:**
- `n_topics` (`int`): Number of topics to research

**Returns:**
- `List[str]`: List of researched topics

---

### `sacbot.generator`

Content generation module.

#### `generate(topic: str, content_type: str, ...) -> GenerationResult`

Generate content in Scott Adams' style.

```python
from sacbot.generator import generate

result = generate(
    topic="Productivity",
    content_type="blog",
    corpus_path="corpus.jsonl",
    n_few_shot=3,
    model="gpt-4o",
    api_key="sk-...",
    temperature=0.7,
)
print(result.content)
print(result.title)
print(result.tags)
print(result.hashtags)
```

**Parameters:**
- `topic` (`str`): Topic to write about
- `content_type` (`str`): Content type (`blog`, `tweet`, `linkedin`)
- `corpus_path` (`Optional[str]`): Path to corpus.jsonl
- `n_few_shot` (`int`): Number of few-shot examples
- `model` (`str`): OpenAI model to use
- `api_key` (`str`): OpenAI API key
- `temperature` (`float`): Sampling temperature

**Returns:**
- `GenerationResult`: Generated content with metadata

#### `GenerationResult`

```python
from sacbot.generator import GenerationResult

result = GenerationResult(
    content="Content here...",
    title="Title here",
    tags=["tag1", "tag2"],
    hashtags=["#tag1", "#tag2"],
    metadata={"word_count": 500, "style_score": 0.9},
)
```

**Attributes:**
- `content` (`str`): Generated content
- `title` (`str`): Generated title
- `tags` (`List[str]`): Content tags
- `hashtags` (`List[str]`): Content hashtags
- `metadata` (`Dict[str, Any]`): Generation metadata

---

### `sacbot.review`

Content review module.

#### `review(content: str, content_type: str) -> ReviewResult`

Review content for style, coherence, and safety.

```python
from sacbot.review import review

result = review(
    content="Your content here...",
    content_type="blog",
)
print(result.passed)
print(result.score)
print(result.style_score)
print(result.profanity_score)
print(result.coherence_score)
print(result.hallucination_risk)
print(result.errors)
```

**Parameters:**
- `content` (`str`): Content to review
- `content_type` (`str`): Content type

**Returns:**
- `ReviewResult`: Review results with scores and errors

#### `ReviewResult`

```python
from sacbot.review import ReviewResult

result = ReviewResult(
    passed=True,
    score=0.9,
    style_score=0.95,
    profanity_score=0.0,
    coherence_score=0.85,
    hallucination_risk=0.1,
    errors=[],
)
```

**Attributes:**
- `passed` (`bool`): Whether content passed review
- `score` (`float`): Overall review score (0-1)
- `style_score` (`float`): Style match score (0-1)
- `profanity_score` (`float`): Profanity score (0-1, lower is better)
- `coherence_score` (`float`): Coherence score (0-1)
- `hallucination_risk` (`float`): Hallucination risk (0-1, lower is better)
- `errors` (`List[str]`): List of review errors

---

### `sacbot.publishers`

Multi-platform publishing module.

#### `ContentPublisher`

```python
from sacbot.publishers import ContentPublisher, GeneratedContent

publisher = ContentPublisher(
    twitter=None,  # TwitterConfig or None
    linkedin=None,  # LinkedInConfig or None
    rss=None,  # RSSConfig or None
)

content = GeneratedContent(
    topic="Productivity",
    content_type="blog",
    content="Content here...",
    title="Title here",
    tags=["tag1"],
    hashtags=["#tag1"],
    metadata={},
)

result = publisher.publish_to_platform(content, "blog")
print(result.success)
print(result.url)
```

**Attributes:**
- `twitter` (`Optional[TwitterConfig]`): Twitter configuration
- `linkedin` (`Optional[LinkedInConfig]`): LinkedIn configuration
- `rss` (`Optional[RSSConfig]`): RSS configuration

**Methods:**
- `publish_to_platform(content: GeneratedContent, content_type: str) -> PublishResult`

#### `GeneratedContent`

```python
from sacbot.publishers import GeneratedContent

content = GeneratedContent(
    topic="Productivity",
    content_type="blog",
    content="Content here...",
    title="Title here",
    tags=["tag1"],
    hashtags=["#tag1"],
    metadata={},
)
```

**Attributes:**
- `topic` (`str`): Content topic
- `content_type` (`str`): Content type
- `content` (`str`): Content text
- `title` (`str`): Content title
- `tags` (`List[str]`): Content tags
- `hashtags` (`List[str]`): Content hashtags
- `metadata` (`Dict[str, Any]`): Content metadata

#### `PublishResult`

```python
from sacbot.publishers import PublishResult

result = PublishResult(
    success=True,
    url="https://example.com/post/123",
    error=None,
)
```

**Attributes:**
- `success` (`bool`): Whether publishing succeeded
- `url` (`Optional[str]`): Published content URL
- `error` (`Optional[str]`): Error message if failed

---

### `sacbot.scheduler`

Content scheduling module.

#### `Scheduler`

```python
from sacbot.scheduler import Scheduler

scheduler = Scheduler(interval_seconds=14400)
scheduled = scheduler.schedule(
    content="Productivity",
    content_type="blog",
    topic="Productivity",
    publish_at=None,
)
```

**Attributes:**
- `interval_seconds` (`float`): Publishing interval in seconds
- `queue` (`ContentQueue`): Content queue

**Methods:**
- `schedule(content: str, content_type: str, topic: str, publish_at: Optional[datetime]) -> ScheduledContent`
- `get_next_publish_time() -> Optional[datetime]`
- `get_queue_size() -> int`

#### `ScheduledContent`

```python
from sacbot.scheduler import ScheduledContent

scheduled = ScheduledContent(
    content="Productivity",
    content_type="blog",
    topic="Productivity",
    publish_at=datetime(2024, 1, 15, 10, 0),
)
```

**Attributes:**
- `content` (`str`): Content to publish
- `content_type` (`str`): Content type
- `topic` (`str`): Content topic
- `publish_at` (`datetime`): Scheduled publish time

---

### `sacbot.dashboard`

Real-time dashboard module.

#### `PipelineDashboard`

```python
from sacbot.dashboard import PipelineDashboard

dashboard = PipelineDashboard()
dashboard.update_stats(stats)
dashboard_str = dashboard.render()
print(dashboard_str)
```

**Methods:**
- `update_stats(stats: PipelineStats) -> None`
- `render() -> str`

#### `PipelineStats`

```python
from sacbot.dashboard import PipelineStats

stats = PipelineStats(
    topics_researched=10,
    content_generated=10,
    content_reviewed=10,
    published_count=8,
    failed_count=2,
    total_latency=120.5,
    last_run_time=datetime(2024, 1, 15, 10, 0),
)
```

**Attributes:**
- `topics_researched` (`int`): Total topics researched
- `content_generated` (`int`): Total content generated
- `content_reviewed` (`int`): Total content reviewed
- `published_count` (`int`): Total content published
- `failed_count` (`int`): Total content failed
- `total_latency` (`float`): Total latency in seconds
- `last_run_time` (`Optional[datetime]`): Last run time

---

### `sacbot.pipeline`

End-to-end pipeline orchestrator.

#### `ContentPipeline`

```python
from sacbot.pipeline import ContentPipeline

pipeline = ContentPipeline()
result = pipeline.run(
    topic="Productivity",
    content_type="blog",
    n_topics=1,
    publish=True,
)
print(result)
```

**Attributes:**
- `config` (`Config`): Pipeline configuration
- `dashboard` (`PipelineDashboard`): Pipeline dashboard
- `scheduler` (`Scheduler`): Content scheduler
- `_stats` (`PipelineStats`): Pipeline statistics

**Methods:**
- `run(topic: Optional[str], content_type: str, n_topics: int, publish: bool) -> PipelineResult`
- `schedule_topic(topic: str, content_type: str, publish_at: Optional[datetime]) -> ScheduledContent`
- `run_scheduled() -> List[PipelineResult]`
- `get_dashboard() -> str`
- `get_stats() -> PipelineStats`

#### `PipelineResult`

```python
from sacbot.pipeline import PipelineResult

result = PipelineResult(
    success=True,
    topics_researched=1,
    content_generated=1,
    content_reviewed=1,
    content_published=1,
    content_failed=0,
    publish_results={"Productivity": PublishResult(success=True, url="...")},
    errors=[],
    latency_seconds=10.5,
    start_time=1234567890.0,
    end_time=1234567900.5,
)
```

**Attributes:**
- `success` (`bool`): Whether pipeline succeeded
- `topics_researched` (`int`): Number of topics researched
- `content_generated` (`int`): Number of content items generated
- `content_reviewed` (`int`): Number of content items reviewed
- `content_published` (`int`): Number of content items published
- `content_failed` (`int`): Number of content items failed
- `publish_results` (`Dict[str, PublishResult]`): Publish results by topic
- `errors` (`List[str]`): List of errors
- `latency_seconds` (`float`): Pipeline latency in seconds
- `start_time` (`Optional[float]`): Pipeline start time
- `end_time` (`Optional[float]`): Pipeline end time

**Properties:**
- `duration` (`float`): Pipeline duration in seconds

#### `run_pipeline(topic, content_type, n_topics, publish, config)`

Convenience function for quick pipeline runs.

```python
from sacbot import run_pipeline

result = run_pipeline(
    topic="Productivity",
    content_type="blog",
    n_topics=1,
    publish=True,
)
print(result)
```

**Parameters:**
- `topic` (`Optional[str]`): Specific topic to research
- `content_type` (`str`): Content type
- `n_topics` (`int`): Number of topics to research
- `publish` (`bool`): Whether to publish the content
- `config` (`Optional[Config]`): Optional configuration

**Returns:**
- `PipelineResult`: Pipeline result with summary statistics

---

### `sacbot.types`

Type definitions.

#### `ContentType`

```python
from sacbot.types import ContentType

content_type: ContentType = "blog"  # "blog", "tweet", or "linkedin"
```

**Values:**
- `"blog"`: Blog post
- `"tweet"`: Twitter/X post
- `"linkedin"`: LinkedIn post
