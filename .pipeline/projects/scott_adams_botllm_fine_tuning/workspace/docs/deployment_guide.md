# Deployment Guide

## Prerequisites

- Python 3.10+
- OpenAI API key (or compatible OpenAI endpoint)
- (Optional) Twitter/X API credentials
- (Optional) LinkedIn API credentials
- (Optional) RSS hosting infrastructure

## Local Development

### 1. Clone and Install

```bash
git clone <repo-url>
cd sacbot
pip install -e ".[dev]"
```

### 2. Configure

Create a configuration file `config.yaml`:

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

Or set environment variables directly:

```bash
export OPENAI_API_KEY="sk-..."
export TWITTER_API_KEY="..."
export TWITTER_API_SECRET="..."
export TWITTER_ACCESS_TOKEN="..."
export TWITTER_ACCESS_TOKEN_SECRET="..."
export LINKEDIN_ACCESS_TOKEN="..."
```

### 3. Verify

```bash
sacbot version
sacbot generate --topic "test topic" --type tweet
```

## Production Deployment

### Option A: Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

CMD ["sacbot", "pipeline", "run", "--n-topics", "5", "--publish"]
```

Build and run:

```bash
docker build -t sacbot .
docker run -e OPENAI_API_KEY=sk-... sacbot
```

### Option B: Systemd Service (Linux)

Create `/etc/systemd/system/sacbot.service`:

```ini
[Unit]
Description=Scott Adams Bot Content Pipeline
After=network.target

[Service]
Type=simple
User=sacbot
WorkingDirectory=/opt/sacbot
EnvironmentFile=/opt/sacbot/.env
ExecStart=/opt/sacbot/venv/bin/sacbot pipeline run --n-topics 3 --publish
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable sacbot
sudo systemctl start sacbot
sudo systemctl status sacbot
```

### Option C: Cron Job

```bash
# Run every 4 hours
0 */4 * * * /opt/sacbot/venv/bin/sacbot pipeline run --n-topics 3 --publish >> /var/log/sacbot.log 2>&1
```

### Option D: Cloud Functions

#### AWS Lambda

```python
import json
from sacbot import run_pipeline

def lambda_handler(event, context):
    result = run_pipeline(
        topic=event.get("topic"),
        content_type=event.get("content_type", "blog"),
        n_topics=event.get("n_topics", 1),
        publish=event.get("publish", True),
    )
    return {
        "statusCode": 200,
        "body": json.dumps(result.__dict__),
    }
```

#### Google Cloud Functions

```python
from flask import request, jsonify
from sacbot import run_pipeline

def generate_content(request):
    data = request.get_json()
    result = run_pipeline(
        topic=data.get("topic"),
        content_type=data.get("content_type", "blog"),
        n_topics=data.get("n_topics", 1),
        publish=data.get("publish", True),
    )
    return jsonify(result.__dict__)
```

## Monitoring

### Dashboard

Run the live dashboard:

```bash
sacbot pipeline dashboard --interval 5
```

### Logs

Logs are written to `output/logs/pipeline.log` by default.

### Metrics

The pipeline tracks:
- Topics researched
- Content generated
- Content reviewed
- Content published
- Content failed
- Latency

Access via:

```python
from sacbot import ContentPipeline

pipeline = ContentPipeline()
stats = pipeline.get_stats()
print(stats)
```

## Scaling

### Multiple Instances

For high-volume publishing, run multiple pipeline instances with different topics:

```bash
# Instance 1
sacbot pipeline run --n-topics 2 --publish

# Instance 2
sacbot pipeline run --n-topics 2 --publish
```

### Rate Limiting

The pipeline respects OpenAI rate limits by default. To adjust:

```python
from sacbot.config import Config

config = Config()
config.openai.max_retries = 5
config.openai.retry_delay = 1.0
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Verify `OPENAI_API_KEY` is set and valid
2. **Twitter Publishing Fails**: Check Twitter API credentials and permissions
3. **LinkedIn Publishing Fails**: Verify LinkedIn access token has `w_member_social` scope
4. **RSS Feed Not Generated**: Check `RSS_FEED_PATH` directory exists and is writable
5. **Content Fails Review**: Adjust `STYLE_THRESHOLD` in config

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
sacbot pipeline run --n-topics 1 --publish
```

### Manual Testing

Test each pipeline stage independently:

```bash
# Test topic research
sacbot research --n-topics 3

# Test content generation
sacbot generate --topic "test" --type blog

# Test content review
sacbot review --content "Your content here" --type blog

# Test publishing (mock)
sacbot publish --content "Your content here" --type blog --platform twitter
```
