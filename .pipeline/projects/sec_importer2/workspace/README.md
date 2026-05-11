# SEC Importer 2

SEC filing data importer — fetch, parse, and store structured data from SEC filings.

## Features

- **Delta-sync**: Fetch only new filings since last sync
- **Multi-format parsing**: XBRL and HTML filing content
- **SQLite storage**: Structured storage with SQLAlchemy ORM
- **Scheduling**: APScheduler or cron-based scheduling
- **CLI**: Command-line interface for all operations

## Installation

```bash
# Install base dependencies
pip install sec-importer

# Install scheduler support (optional)
pip install "sec-importer[scheduler]"
```

## Usage

### Quick Start

```bash
# Run a one-time sync
sec-importer sync

# Run with custom tickers file
sec-importer sync --tickers-file /path/to/tickers.csv

# Run with custom limit
sec-importer sync --limit 50

# Start the scheduler (runs daily at 2:00 AM UTC)
sec-importer scheduler start

# Run a sync immediately
sec-importer scheduler run-now

# Show scheduler configuration
sec-importer scheduler show-config
```

### Configuration

All configuration can be set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHEDULER_MODE` | `apscheduler` | Scheduler mode (`apscheduler` or `cron`) |
| `SCHEDULER_SYNC_HOUR` | `2` | Hour to run sync (0-23) |
| `SCHEDULER_SYNC_MINUTE` | `0` | Minute to run sync (0-59) |
| `SCHEDULER_TIMEZONE` | `UTC` | Timezone for scheduling |
| `SCHEDULER_CRON_EXPRESSION` | `0 2 * * *` | Cron expression (cron mode) |
| `SCHEDULER_RUN_ONCE` | `false` | Run once and exit (cron mode) |
| `SCHEDULER_TICKERS_FILE` | `sec_importer/tickers.csv` | Path to tickers file |
| `SCHEDULER_LIMIT_PER_TICKER` | `100` | Max filings per ticker |
| `SCHEDULER_DB_PATH` | `sec_importer.db` | Path to SQLite database |

### Tickers File

Create a CSV file with one ticker symbol per line:

```csv
AAPL
MSFT
GOOGL
AMZN
TSLA
```

## Project Structure

```
sec_importer/
├── __init__.py
├── cli.py              # CLI entry point
├── config.py           # Configuration
├── fetcher.py          # SEC API fetcher
├── models.py           # SQLAlchemy ORM models
├── parser.py           # Filing content parser
├── storage.py          # Database storage layer
├── sync.py             # Delta-sync orchestrator
└── scheduler/
    ├── __init__.py
    ├── config.py       # Scheduler configuration
    └── run.py          # Scheduler implementation
```

## Development

```bash
# Install in development mode
pip install -e ".[scheduler]"

# Run tests
pytest

# Lint
flake8 sec_importer/
mypy sec_importer/
```

## License

MIT
