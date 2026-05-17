# Deployment Guide

This guide covers deploying Droppain via pip, Docker, and cloud platforms.

---

## Prerequisites

- Python 3.10+ (for pip install)
- Docker 20+ (for Docker deployment)
- Shopify API credentials (for live integration)

---

## 1. Pip Install (Direct)

### Install

```bash
pip install droppain
```

### Configure

Create a `.env` file:

```bash
cp sample_env.txt .env
# Edit .env with your credentials
```

### Verify

```bash
droppain health
```

---

## 2. Docker Deployment

### Build

```bash
docker build -t droppain:latest .
```

### Run

```bash
docker run --env-file .env droppain:latest health
```

### Docker Compose

```bash
docker compose up
```

---

## 3. Cloud Deployment

### AWS ECS

1. Build and push the Docker image to ECR.
2. Create an ECS task definition with the image.
3. Set environment variables in the task definition.
4. Deploy to ECS cluster.

### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/droppain
gcloud run deploy droppain \
  --image gcr.io/PROJECT_ID/droppain \
  --platform managed \
  --env-file .env
```

### Heroku

```bash
heroku create droppain
heroku config:set SHOPIFY_API_KEY=your_key
heroku config:set SHOPIFY_PASSWORD=your_password
heroku config:set SHOPIFY_STORE_NAME=your-store
git push heroku main
```

---

## Environment Variables Reference

| Variable | Required | Description |
|------|------|------|
| `SHOPIFY_API_KEY` | Conditional | Shopify API key (required if using Shopify integration) |
| `SHOPIFY_PASSWORD` | Conditional | Shopify API password |
| `SHOPIFY_STORE_NAME` | Conditional | Shopify store name |
| `SHOPIFY_API_VERSION` | No | Shopify API version (default: 2024-01) |
| `DROPPAIN_CAMPAIGN_PREFIX` | No | Campaign name prefix (default: "Dropship Campaign") |
| `DEFAULT_CURRENCY` | No | Default currency (default: USD) |
| `DROPPAIN_DEFAULT_TIMEZONE` | No | Default timezone (default: UTC) |
| `DROPPAIN_LOG_LEVEL` | No | Log level (default: INFO) |
| `DROPPAIN_LOG_FILE` | No | Log file path (default: stderr) |

---

## Troubleshooting

### Health check fails

1. Verify all required environment variables are set.
2. Check network connectivity to Shopify API.
3. Run `droppain health --fix` to auto-resolve common issues.

### Docker build fails

1. Ensure Docker is installed and running.
2. Check that `pyproject.toml` and `droppain/` directory are in the build context.

### API errors

1. Verify Shopify credentials are correct.
2. Check that the store name matches your Shopify store URL.
3. Review logs with `--log-level DEBUG`.
