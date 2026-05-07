# Phase 1 Review

### What's Good
- **Project scaffolding**: `pyproject.toml` is well-structured with correct metadata, dependencies (numpy, pandas, pyyaml, scipy), dev extras, and CLI entry point.
- **Config**: `config/default.yaml` cleanly defines data path, strategy (sma_crossover), MC parameters (n_simulations=1000, seed=42), and output paths.
- **Data loader** (`data/loader.py`): Properly validates required OHLCV columns, enforces ≥252 trading days, handles type coercion, drops NaNs, and sorts by date.
- **Strategy base class** (`strategies/base.py`): Clean ABC with well-documented `generate_signals` contract returning `[date, signal]` DataFrame.
- **SMACrossoverStrategy** (`strategies/sma_crossover.py`): Correctly uses `.shift(1)` to avoid look-ahead bias; validates fast < slow window; generates signals from SMA crossovers.
- **Backtester** (`engine/backtester.py`): Properly merges signals with price data, shifts signal by 1 for next-day execution, computes daily and strategy returns, and builds equity curve starting at 1.0.
- **Monte Carlo engine** (`engine/monte_carlo.py`): Supports both bootstrap (resampling with replacement) and parametric (normal distribution) methods; uses `np.random.default_rng` for reproducible seeding; runs ≥1000 simulations.
- **Metrics calculator** (`metrics/risk.py`): Computes a comprehensive set of metrics — annualized return, Sharpe ratio, max drawdown, VaR, CVaR, win rate, profit factor, Calmar ratio, Kelly fraction — plus percentile bands across simulations.
- **CSV export** (`reporting/csv_export.py`): Exports both per-simulation equity curves and summary statistics to CSV.
- **Text report** (`reporting/text_report.py`): Clean, well-formatted text report with all key metrics and percentile bands.
- **CLI** (`cli.py`): Uses `argparse` with subcommands; `--config` flag works; full pipeline orchestration is clean and readable.
- **Integration test** (`tests/test_integration.py`): Runs full pipeline end-to-end with deterministic seed; asserts non-empty results; uses temporary directory for isolation.
- **Sample data generator** (`examples/generate_sample_data.py`): Generates synthetic OHLCV via geometric Brownian motion with proper high/low constraints; produces ≥500 trading days.
- **README.md**: Comprehensive documentation covering installation, config schema table, CLI usage, output format, metrics explanation, and test commands.

## Blocking Bugs
- **None**

## Non-Blocking Notes
- **`monte_carlo.py` — `_bootstrap_simulate` column naming**: The column names use `[f"sim_{i}" for i in range(self.n_simulations)]` but `i` is the loop variable from the outer scope — this works in Python 3 but is technically a closure bug. If `n_simulations` changes between iterations, it would capture the final value. However, since `i` is used directly in the list comprehension (not a lambda), it captures the current value correctly. This is fine as written.
- **`metrics/risk.py` — `kelly_fraction` formula**: The Kelly fraction formula divides by `avg_loss` which is the absolute mean loss. The standard Kelly formula is `(bp - q) / b` where `b` is the average win/loss ratio. The current implementation approximates this but could be clarified with a comment.
- **`metrics/risk.py` — `profit_factor` with zero losses**: When `losses == 0` and `gains > 0`, it returns `float("inf")`. This could cause issues downstream in CSV export or report formatting. Consider capping at a large finite number or documenting the behavior.
- **`cli.py` — no `--help` on the top-level parser when no subcommand is given**: The `else` branch prints help and exits with code 0, which is fine, but `parser.print_help()` on the top-level parser (not the subparser) may be confusing. Consider adding a default subparser or explicit message.
- **`data/loader.py` — `inplace` operations**: Uses `df.dropna(inplace=True)` and `df.sort_values(..., inplace=True)`. These are deprecated in newer pandas versions. Consider using `df = df.dropna()` and `df = df.sort_values(...)` for forward compatibility.
- **`engine/backtester.py` — equity curve starting at 1.0**: The equity curve starts at 1.0 and compounds from there. This is fine for relative performance, but the initial value is implicit. Consider documenting or making it a parameter.
- **`examples/sample_data/` directory is empty**: The sample CSV is generated on-the-fly by the test and the `generate_sample_data.py` script. Consider committing a pre-generated sample CSV for users who don't want to run the generator.
- **`pyproject.toml` — scipy listed as dependency but not imported**: `scipy` is in the dependencies but no file imports it. Consider removing it if not needed, or adding a comment explaining its intended use.
- **`conftest.py` — path injection**: The `conftest.py` injects the workspace path into `sys.path`. This is a pipeline-specific hack and may not be needed in a standard pytest setup. Consider using `PYTHONPATH` or pytest's `--rootdir` instead.

## Reusable Components
- **`market_strategy_backtester/data/loader.py`** — Generic CSV data loader with column validation, type coercion, NaN handling, and minimum-row validation. Could be reused for any tabular data ingestion pipeline.
- **`market_strategy_backtester/strategies/base.py`** — Abstract Strategy base class defining a clean signal-generation contract. Useful as a template for any event-driven strategy framework.
- **`market_strategy_backtester/metrics/risk.py`** — `MetricsCalculator` class computes comprehensive financial metrics (Sharpe, max drawdown, VaR, CVaR, Kelly fraction, etc.) from equity curves. Self-contained and general-purpose.
- **`market_strategy_backtester/engine/monte_carlo.py`** — `MonteCarloSimulator` class supports bootstrap and parametric simulation methods with seed control. General-purpose Monte Carlo engine for any resampling task.
- **`examples/generate_sample_data.py`** — `generate_sample_ohlcv` function generates synthetic OHLCV data via geometric Brownian motion with proper high/low constraints. Useful for testing any financial data pipeline.

## Verdict
PASS — All tasks are implemented correctly, the integration test passes, and there are no blocking bugs.
