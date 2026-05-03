# sacbot — Scott Adams Style Content Generator

An AI-powered content generation pipeline that produces blog posts, tweets, and LinkedIn posts in Scott Adams' distinctive writing style.

## Features

- **Topic Research**: Aggregates topics from current events and Scott Adams' canonical subjects
- **Content Generation**: Uses OpenAI's GPT-4o to generate content in Adams' style
- **Content Review**: Automated style checks, profanity detection, coherence scoring, and hallucination risk assessment
- **Multi-Platform Publishing**: Supports Twitter/X, LinkedIn, and RSS feed publishing
- **Content Scheduling**: Queue-based scheduler for automated publishing at configured intervals
- **Real-Time Dashboard**: Text-based dashboard showing pipeline status and statistics
- **CLI Interface**: Full command-line interface for all pipeline operations

## Quick Start

### Installation

```bash
pip install sacbot
```

### Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

Optional: Configure Twitter/X and LinkedIn:

```bash
export TWITTER_API_KEY="..."
export TWITTER_API_SECRET="..."
export TWITTER_ACCESS_TOKEN="..."
export TWITTER_ACCESS_TOKEN_SECRET="..."
export LINKEDIN_ACCESS_TOKEN="..."
```

### Generate Content

Generate a blog post about a specific topic:

```bash
sacbot generate --topic "productivity" --type blog
```

Generate a tweet:

```bash
sacbot generate --topic "AI safety" --type tweet
```

Generate content in JSON format:

```bash
sacbot generate --topic "remote work" --type blog --format json
```

### Run the Full Pipeline

Research topics and generate content:

```bash
sacbot pipeline run --n-topics 3 --type blog
```

Schedule content for future publishing:

```bash
sacbot pipeline schedule --topic "future of work" --type linkedin
```

View the live dashboard:

```bash
sacbot pipeline dashboard
```

## Pipeline Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Topic      │────▶│  Content     │────▶│  Content    │────▶│  Publishing  │
│  Research   │     │  Generation  │     │  Review     │     │  & Scheduling│
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
  Current Events      GPT-4o / GPT-4       Style Checks       Twitter/X
  Scott Adams       Few-Shot Learning     Profanity Detection  LinkedIn
  Canonical Topics  Style Transfer        Coherence Scoring    RSS Feed
                    Hallucination Risk    Hallucination Risk
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o` |
| `OPENAI_BASE_URL` | Custom OpenAI base URL | None |
| `TWITTER_API_KEY` | Twitter API key | None |
| `TWITTER_API_SECRET` | Twitter API secret | None |
| `TWITTER_ACCESS_TOKEN` | Twitter access token | None |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter access token secret | None |
| `TWITTER_MOCK` | Use mock Twitter publisher | `true` |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn access token | None |
| `LINKEDIN_MOCK` | Use mock LinkedIn publisher | `true` |
| `RSS_FEED_PATH` | RSS feed file path | `output/rss/feed.xml` |
| `RSS_MOCK` | Use mock RSS publisher | `true` |
| `SCHEDULER_INTERVAL` | Publishing interval in seconds | `14400` (4 hours) |
| `STYLE_THRESHOLD` | Style match threshold (0-1) | `0.8` |
| `TEMPERATURE` | LLM sampling temperature | `0.7` |
| `OUTPUT_DIR` | Output directory | `output` |

### Configuration File

You can also use a YAML configuration file:

```yaml
openai:
  api_key: "sk-..."
  model: "gpt-4o"

twitter:
  api_key: "..."
  api_secret: "..."
  access_token: "..."
  access_token_secret: "..."
  mock: true

linkedin:
  access_token: "..."
  mock: true

rss:
  feed_path: "output/rss/feed.xml"
  site_name: "Scott Adams Bot"
  mock: true

scheduler_interval_seconds: 14400
style_threshold: 0.8
temperature: 0.7
```

## CLI Reference

### `sacbot generate`

Generate content in Scott Adams' style.

```
Usage: sacbot generate [OPTIONS]

Options:
  --topic TEXT              Topic to write about.  [required]
  --type [blog|tweet|linkedin]
                            Content type to generate.  [default: blog]
  --corpus PATH             Path to corpus.jsonl for few-shot examples.
  --n-few-shot INTEGER      Number of few-shot examples.  [default: 3]
  --model TEXT              OpenAI model to use.  [default: gpt-4o]
  --api-key TEXT            OpenAI API key
  --temperature FLOAT       Sampling temperature.  [default: 0.7]
  --seed INTEGER            Random seed for reproducibility
  --output PATH             Output file path
  --format [text|json]      Output format.  [default: text]
```

### `sacbot pipeline run`

Run the full pipeline for one or more topics.

```
Usage: sacbot pipeline run [OPTIONS]

Options:
  --topic TEXT              Specific topic to research
  --type [blog|tweet|linkedin]
                            Content type to generate.  [default: blog]
  --n-topics INTEGER        Number of topics to research.  [default: 1]
  --publish / --no-publish  Whether to publish the content.  [default: publish]
```

### `sacbot pipeline schedule`

Schedule content for future processing.

```
Usage: sacbot pipeline schedule [OPTIONS]

Options:
  --topic TEXT              Topic to schedule.  [required]
  --type [blog|tweet|linkedin]
                            Content type to generate.  [default: blog]
  --publish-at DATETIME     When to publish (ISO format).  [default: now + interval]
```

### `sacbot pipeline dashboard`

View the live pipeline dashboard.

```
Usage: sacbot pipeline dashboard [OPTIONS]

Options:
  --interval FLOAT          Update interval in seconds.  [default: 2.0]
```

### `sacbot version`

Print version information.

```
Usage: sacbot version
```

## Programmatic Usage

```python
from sacbot import run_pipeline, ContentPipeline, Config

# Quick pipeline run
result = run_pipeline(
    topic="productivity",
    content_type="blog",
    n_topics=1,
    publish=True,
)
print(result)

# Full pipeline with custom config
config = Config.from_env()
pipeline = ContentPipeline(config=config)
result = pipeline.run(
    topic="AI safety",
    content_type="linkedin",
    publish=True,
)
print(result)
```

## Output Structure

```
output/
├── blog/
│   └── 2024-01-15_productivity.md
├── tweets/
│   └── 2024-01-15_ai_safety.txt
├── linkedin/
│   └── 2024-01-15_future_of_work.md
├── rss/
│   └── feed.xml
└── pipeline_results/
    └── 2024-01-15T10_30_00.json
```

## Testing

```bash
# Run all tests
pytest sacbot/tests/

# Run with coverage
pytest sacbot/tests/ --cov=sacbot --cov-report=html
```

## License

MIT
