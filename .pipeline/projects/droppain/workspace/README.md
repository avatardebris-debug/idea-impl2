# Droppain

**Dropship marketing campaign planner and execution engine.**

Automate your dropshipping marketing campaigns: plan, generate content, and publish across multiple channels — all from the command line.

---

## Installation

### pip

```bash
pip install droppain
```

### From source

```bash
git clone https://github.com/your-org/droppain.git
cd droppain
pip install -e .
```

### Development dependencies

```bash
pip install -e ".[dev]"
```

---

## Quick Start

```bash
# Set up environment variables
export SHOPIFY_API_KEY="your_api_key"
export SHOPIFY_PASSWORD="your_password"
export SHOPIFY_STORE_NAME="your-store"

# Run a health check
droppain health

# Create a campaign plan from products
droppain plan --products products.json --name "Summer Sale" --budget 500.0

# Execute the campaign
droppain execute --plan plan.json
```

---

## CLI Reference

### `droppain health`

Run system health checks to verify configuration and dependencies.

```bash
droppain health                          # report only
droppain health --fix                    # auto-fix fixable issues
droppain health --json                   # machine-readable output
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--fix` | Auto-fix fixable issues |
| `--json` | Output results as JSON |
| `--log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### `droppain plan`

Generate a campaign plan from a products JSON file.

```bash
droppain plan --products products.json --name "Spring Campaign" --budget 1000.0
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--products` (required) | Path to products JSON file |
| `--name` | Campaign name |
| `--budget` | Total campaign budget |
| `--json` | Output plan as JSON |

**Products JSON format:**

```json
[
  {
    "id": "prod_1",
    "title": "Wireless Earbuds",
    "description": "High-quality wireless earbuds",
    "price": 49.99,
    "variants": [
      {"id": "var_1", "title": "Black", "price": 49.99}
    ],
    "tags": ["electronics", "audio"]
  }
]
```

### `droppain execute`

Execute a previously created campaign plan.

```bash
droppain execute --plan plan.json
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--plan` (required) | Path to plan JSON file |
| `--json` | Output results as JSON |

---

## Configuration

All configuration is via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SHOPIFY_API_KEY` | Shopify API key | (empty) |
| `SHOPIFY_PASSWORD` | Shopify API password | (empty) |
| `SHOPIFY_STORE_NAME` | Shopify store name | (empty) |
| `SHOPIFY_API_VERSION` | Shopify API version | `2024-01` |
| `DROPPAIN_CAMPAIGN_PREFIX` | Campaign name prefix | `Dropship Campaign` |
| `DEFAULT_CURRENCY` | Default currency code | `USD` |
| `DROPPAIN_DEFAULT_TIMEZONE` | Default timezone | `UTC` |
| `DROPPAIN_LOG_LEVEL` | Logging level | `INFO` |
| `DROPPAIN_LOG_FILE` | Optional log file path | (none) |

### Sample environment file

See `sample_env.txt` in the repository root for a commented template.

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Products   │────▶│  Campaign    │────▶│  Content     │
│  (JSON/API) │     │  Planner     │     │  Generator   │
└─────────────┘     └──────────────┘     └──────────────┘
                                       │
                                       ▼
                               ┌──────────────┐
                               │  Executor    │
                               │  (Channels)  │
                               └──────────────┘
```

1. **Planner** — Takes products and creates a campaign plan with content briefs.
2. **Content Generator** — Generates platform-specific content from briefs.
3. **Executor** — Publishes content to configured channels (Shopify, social media, etc.).

---

## Deployment

See [docs/deployment.md](docs/deployment.md) for step-by-step deployment instructions.

### Docker

```bash
docker build -t droppain .
docker run --env-file .env droppain health
```

### Cloud deployment

1. Set environment variables in your hosting platform.
2. Deploy the Docker image or install via pip.
3. Run `droppain health` to verify.

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run mypy
mypy droppain

# Run linting
ruff check droppain
```

---

## License

MIT
