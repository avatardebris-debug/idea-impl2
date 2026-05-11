# Tableau Integration Module

A card-game simulation dashboard that generates real-time metrics including win rate, bankroll curves, and Nash equilibrium shifts. Designed for integration with Tableau for visualization.

## Architecture

```
src/
├── __init__.py              # Package root
├── data_source.py           # MockDataSource base class (threading, callbacks)
├── ticker.py                # Base Ticker class (price/color logic)
└── dashboard/
    ├── __init__.py
    ├── models.py            # DashboardState, WinRateMetric, BankrollCurvePoint, NashEquilibriumShift
    ├── tickers.py           # DashboardTicker (aggregates metrics with color logic)
    ├── data_source.py       # DashboardDataSource (generates simulated updates)
    └── demo_cli.py          # CLI demo script
tests/
├── test_dashboard_models.py
└── test_dashboard_data_source.py
```

## Key Components

### Ticker (`src/ticker.py`)
- Base class for real-time metric streams
- Color-coded visual hints (green/red/white) based on price direction
- Serialization/deserialization support

### MockDataSource (`src/data_source.py`)
- Threading-based periodic update generator
- Callback registration for reactive updates
- Background thread management

### Dashboard Module (`src/dashboard/`)
- **Models**: Dataclasses for win rate, bankroll, and Nash equilibrium metrics
- **Tickers**: Aggregated ticker with color logic based on win rate thresholds
- **DataSource**: Simulated data source with configurable seed for reproducibility

## Usage

```python
from src.dashboard.data_source import DashboardDataSource

ds = DashboardDataSource(seed=42)
ds.start()

# Get latest state
state = ds.get_latest_state()
print(f"Win Rate: {state.win_rate.value:.2%}")
print(f"Bankroll: {state.bankroll.bankroll}")

ds.stop()
```

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT
