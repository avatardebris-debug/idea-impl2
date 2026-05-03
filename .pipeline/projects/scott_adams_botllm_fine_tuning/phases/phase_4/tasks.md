# Phase 4 Tasks

- [ ] Task 1: Topic research module
  - What: Build a topic research module that aggregates potential topics from current events and Adams' canonical subject areas (success, management, probability, habits, psychology, systems). Produces ranked topic suggestions with metadata (relevance score, source, suggested content type).
  - Files:
    - Create `sacbot/topic_research.py` — TopicSuggestion dataclass, `fetch_trending_topics()` (mockable HTTP calls to news RSS / Google Trends API), `suggest_topics()` (combines trending with Adams' canonical topics using a scoring function), `TopicPipeline` class that orchestrates the research
    - Create `sacbot/topics.json` — canonical Adams topic seed list with weights
    - Update `sacbot/__init__.py` — expose `topic_research`
  - Done when: `suggest_topics(n=10)` returns 10 TopicSuggestion objects with relevance scores ≥ 0.3, at least 3 sourced from current events and at least 3 from Adams' canonical topics; module works with mocked HTTP (no live network required for tests)

- [ ] Task 2: Content review system
  - What: Build an automated content review system that checks generated content for style match (≥ 80% threshold), quality filters (profanity, coherence, minimum length, no hallucinated facts), and produces a review report. Supports both automated pass/fail and human-review flagging.
  - Files:
    - Create `sacbot/review.py` — ReviewResult dataclass, `check_style_match()` (reuses `_compute_style_match` from `eval.py` with ≥ 0.8 threshold), `check_quality()` (profanity via `badwords` or custom list, coherence via sentence count / avg length, hallucination check via factoid detection), `ContentReviewer` class that runs all checks and returns ReviewResult
    - Update `sacbot/types.py` — add `ReviewResult` type alias or import from review module
    - Update `sacbot/__init__.py` — expose `review`
  - Done when: `ContentReviewer().review(sample)` returns ReviewResult with `passed=True` for a known-good Adams-style sample and `passed=False` for a known-bad sample; automated checks cover style match, profanity, coherence, and length; test coverage ≥ 80%

- [ ] Task 3: Platform integrations
  - What: Build publisher adapters for Twitter/X API, LinkedIn API, and RSS feed publishing. Each publisher implements a common `ContentPublisher` interface. Includes mock implementations for testing.
  - Files:
    - Create `sacbot/publishers.py` — `ContentPublisher` abstract base class with `publish(content: GeneratedContent) -> PublishResult`; concrete classes `TwitterPublisher`, `LinkedInPublisher`, `RSSEditor`; `PublishResult` dataclass; mock implementations `MockTwitterPublisher`, `MockLinkedInPublisher`, `MockRSSEditor` for testing
    - Create `sacbot/config.py` — configuration dataclass for API keys, endpoints, RSS metadata
    - Update `sacbot/__init__.py` — expose `publishers`
  - Done when: All three mock publishers can publish content without errors; real TwitterPublisher works with a valid API key (documented in README); `publishers.py` test coverage ≥ 80%; at least one platform integration successfully posts content (mock or real)

- [ ] Task 4: Scheduler and CLI dashboard
  - What: Build a cron-based content scheduler that queues content and dispatches it to publishers at configured intervals. Build a CLI dashboard that displays real-time pipeline status (pending, in-progress, published, failed counts).
  - Files:
    - Create `sacbot/scheduler.py` — `ScheduledContent` dataclass, `ContentQueue` (thread-safe priority queue), `Scheduler` class with `schedule(content: GeneratedContent, publish_at: datetime)`, `run()` (cron loop), `stop()` methods; supports configurable intervals (default: every 4 hours)
    - Create `sacbot/dashboard.py` — `PipelineDashboard` class with `render()` method that prints a text-based dashboard showing: pending count, in-progress count, published count, failed count, last publish time, next scheduled publish; CLI entry point `sacbot-dashboard`
    - Update `sacbot/cli.py` — add `pipeline schedule` and `pipeline dashboard` subcommands
    - Update `sacbot/__init__.py` — expose `scheduler` and `dashboard`
  - Done when: `Scheduler` can queue and dispatch content at configured intervals; `PipelineDashboard.render()` displays current pipeline status; CLI commands `sacbot pipeline schedule` and `sacbot pipeline dashboard` work; test coverage ≥ 80%

- [ ] Task 5: End-to-end pipeline, CLI integration, and documentation
  - What: Build the orchestration layer that connects topic research → generation → review → publishing into a single pipeline. Update CLI with a `pipeline run` command. Create deployment guide and API reference documentation.
  - Files:
    - Create `sacbot/pipeline.py` — `ContentPipeline` class with `run()` method that: (1) fetches topics via `topic_research`, (2) generates content via `generator.generate()`, (3) reviews via `review.ContentReviewer`, (4) publishes via selected `publisher`, (5) logs results; supports batch mode (e.g., 7-day content)
    - Update `sacbot/cli.py` — add `pipeline run` subcommand that invokes `ContentPipeline.run()` with configurable parameters (num_topics, content_type, publisher, schedule_interval)
    - Create `docs/` directory with:
      - `docs/README.md` — project overview
      - `docs/deployment_guide.md` — deployment instructions, API key setup, cron configuration
      - `docs/api_reference.md` — API reference for all public modules
    - Create `sacbot/tests/test_pipeline.py` — end-to-end test using mock publishers and mocked topic research
    - Update `sacbot/__init__.py` — expose `pipeline`
  - Done when: `ContentPipeline.run()` completes end-to-end (topic → generate → review → publish) using mock components; `sacbot pipeline run` CLI command works; pipeline can generate and publish a week's worth of content autonomously; documentation covers deployment, API keys, and cron configuration; test coverage ≥ 80%