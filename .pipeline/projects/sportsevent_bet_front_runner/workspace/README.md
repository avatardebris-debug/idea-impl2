# Sports/Event Bet Front Runner Pipeline

A real-time sports data pipeline that detects latency gaps between raw feed timestamps and broadcast timestamps, generates actionable signals, and simulates bet placement for backtesting.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Feed Adapters│────▶│   Pipeline   │────▶│ Latency Detector│────▶│ Signal Gen   │
│  (NFL, NBA)  │     │  (Routing)   │     │  (Gap Detection)│     │ (Rules)      │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
                                                              │
                                                              ▼
                                                       ┌──────────────┐
                                                       │ Backtest     │
                                                       │ Harness      │
                                                       └──────────────┘
```

## Components

### 1. Feed Adapters (`src/pipeline/adapters/`)
- **MockNFLFeed**: Simulates NFL play-by-play data
- **MockNBAGameFeed**: Simulates NBA game data
- **FeedAdapter**: Base class for creating custom feed adapters

### 2. Pipeline (`src/pipeline/pipeline.py`)
- Core pipeline that manages feed connections and message routing
- Tracks processing latency per event
- Routes events to registered handlers
- Generates signals based on latency gaps

### 3. Latency Detector (`src/pipeline/latency_detector.py`)
- Detects gaps between raw feed timestamps and broadcast timestamps
- Computes confidence scores based on gap size
- Determines severity levels (low, medium, high, critical)
- Generates rule-based signals

### 4. Backtest Harness (`src/backtest/backtest_harness.py`)
- Simulates bet placement during latency gaps
- Calculates ROI, win rate, and other performance metrics
- Supports configurable bet amounts, odds, and commission rates

### 5. Configuration (`src/pipeline/config.py`)
- Manages feed URLs, polling intervals, sport mappings
- Configures latency thresholds and signal rules
- Configures backtest parameters

## Setup

```bash
cd workspace
pip install -r requirements.txt
```

## Running

### Run the pipeline:
```bash
python -m src.main
```

### Run with backtest:
```bash
python -m src.main --run-backtest
```

### Run tests:
```bash
pytest tests/ -v
```

## Configuration

Edit `src/pipeline/config.py` to customize:

- **Feed settings**: poll intervals, seed values, enabled feeds
- **Latency thresholds**: gap detection thresholds, confidence scoring
- **Signal rules**: thresholds for different signal types
- **Backtest parameters**: bet amounts, odds, commission rates

## Signal Types

| Signal Type | Description |
|-------------|-------------|
| SCORE_DELAYED | Score event delayed beyond threshold |
| PLAY_DELAYED | Play event delayed beyond threshold |
| QUARTER_END_DELAYED | Quarter end event delayed beyond threshold |
| ANOMALY_DETECTED | Anomalous latency gap detected |

## Severity Levels

| Severity | Gap Size |
|----------|----------|
| LOW | 1.0s - 2.0s |
| MEDIUM | 2.0s - 5.0s |
| HIGH | 5.0s - 10.0s |
| CRITICAL | > 10.0s |

## Project Structure

```
workspace/
├── src/
│   ├── main.py                    # Entry point
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration
│   │   ├── feed_adapter.py        # Base feed adapter
│   │   ├── latency_detector.py    # Latency gap detection
│   │   ├── models.py              # Data models
│   │   ├── pipeline.py            # Core pipeline
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── mock_nfl_feed.py   # Mock NFL feed
│   │       └── mock_nba_feed.py   # Mock NBA feed
│   └── backtest/
│       ├── __init__.py
│       └── backtest_harness.py    # Backtest simulation
├── tests/
│   └── test_pipeline.py           # Unit and integration tests
├── requirements.txt
└── README.md
```

## Design Decisions

1. **Async-first**: All I/O operations are async for high throughput
2. **Configurable thresholds**: All detection thresholds are configurable
3. **Modular design**: Each component is independently testable
4. **Mock feeds**: No external dependencies for testing
5. **Rule-based signals**: Simple, interpretable signal generation

## Future Work

- [ ] Add real feed adapters (ESPN, SportsDataIO, etc.)
- [ ] Add WebSocket support for real-time feeds
- [ ] Add database persistence for historical data
- [ ] Add ML-based signal generation
- [ ] Add live trading integration
- [ ] Add dashboard for monitoring
- [ ] Add more sports coverage
