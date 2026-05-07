# Market Strategy Backtester

A Monte Carlo backtesting engine for algorithmic trading strategies using historical price data and risk-adjusted metrics. The system simulates thousands of possible future equity curves via Monte Carlo methods, enabling robust strategy evaluation under uncertainty.

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Configuration

Edit `config/default.yaml` to set your parameters:

```yaml
data:
  path: "examples/sample_data/sample_ohlcv.csv"
  format: "ohlcv"

strategy:
  name: "sma_crossover"
  params:
    fast_window: 10
    slow_window: 30

monte_carlo:
  n_simulations: 1000
  seed: 42
  method: "bootstrap"

output:
  results_dir: "results"
  csv_export: true
  text_report: true
```

### Config Schema

| Section | Key | Type | Default | Description |
|---------|-----|------|---------|-------------|
| `data` | `path` | str | - | Path to OHLCV CSV file |
| `data` | `format` | str | "ohlcv" | Data format (currently only "ohlcv") |
| `strategy` | `name` | str | "sma_crossover" | Strategy name |
| `strategy` | `params` | dict | - | Strategy-specific parameters |
| `monte_carlo` | `n_simulations` | int | 1000 | Number of MC simulations |
| `monte_carlo` | `seed` | int | 42 | Random seed for reproducibility |
| `monte_carlo` | `method` | str | "bootstrap" | MC method ("bootstrap" or "parametric") |
| `output` | `results_dir` | str | "results" | Output directory |
| `output` | `csv_export` | bool | true | Export per-simulation CSV |
| `output` | `text_report` | bool | true | Generate text summary |

## CLI Usage

```bash
# Run with default config
python -m market_strategy_backtester run --config config/default.yaml

# Run with custom config
python -m market_strategy_backtester run --config my_config.yaml

# Show help
python -m market_strategy_backtester --help
```

## Output

Results are written to the `results/` directory:

- `equity_curves.csv` — Per-simulation equity curves (columns: step, sim_0, sim_1, ...)
- `summary_statistics.csv` — Summary metrics per simulation (columns: sim_id, annualized_return, sharpe_ratio, max_drawdown, var_95, ...)
- `text_report.txt` — Human-readable summary with mean/percentile bands

## Metrics Explained

- **Annualized Return**: Geometric mean return scaled to annual basis
- **Sharpe Ratio**: (Mean return - Risk-free rate) / Std dev of returns, annualized
- **Max Drawdown**: Largest peak-to-trough decline in equity curve
- **95% VaR**: Value at Risk at 95% confidence level (worst 5% scenario)
- **Percentile Bands**: 5th/50th/95th percentile equity curves across simulations

## Running Tests

```bash
pytest tests/ -v
```
