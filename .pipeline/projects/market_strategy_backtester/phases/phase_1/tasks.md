# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and configuration
  - What: Create the Python package layout, pyproject.toml, and default YAML config
  - Files: pyproject.toml, README.md, config/default.yaml, src/__init__.py, src/cli.py
  - Done when: Package is installable via `pip install -e .`, CLI accepts `--help` flag, default config defines data path, strategy (sma_crossover), MC parameters (n_simulations=1000, seed=42), and output paths

- [ ] Task 2: Data loader and strategy framework
  - What: Implement CSV data loader (OHLCV columns, date parsing, 2+ year validation) and strategy base class with one concrete strategy
  - Files: src/data/loader.py, src/strategies/__init__.py, src/strategies/base.py, src/strategies/sma_crossover.py
  - Done when: loader loads a CSV with columns [date, open, high, low, close, volume], validates ≥ 252 trading days, returns a pandas DataFrame; Strategy base class has abstract `generate_signals(price_data)` returning a DataFrame with [date, signal] (1=buy, 0=sell); SMACrossoverStrategy generates signals from configurable fast/slow SMA windows with no look-ahead bias (uses only `.shift()` data)

- [ ] Task 3: Backtester, Monte Carlo engine, and metrics calculator
  - What: Implement the core backtester (apply strategy → compute equity curve), bootstrap Monte Carlo simulator, and risk metrics
  - Files: src/engine/backtester.py, src/engine/monte_carlo.py, src/metrics/risk.py
  - Done when: backtester takes price data + strategy, produces per-trade returns and an equity curve; Monte Carlo engine resamples returns with replacement, re-aggregates into equity curves, runs ≥ 1,000 simulations with seed control in < 30s; metrics calculator computes annualized return, Sharpe ratio, max drawdown, 95% VaR, and equity curve percentiles (5th/50th/95th) across all simulations

- [ ] Task 4: Result formatting and CLI entry point
  - What: Implement result formatter (CSV export + text summary) and CLI with YAML config support
  - Files: src/reporting/text_report.py, src/reporting/csv_export.py, src/cli.py (update)
  - Done when: `python -m market_strategy_backtester run --config config.yaml` executes end-to-end; output CSV contains per-simulation equity curves and summary statistics; text summary prints mean annualized return, Sharpe ratio, max drawdown, 95% VaR, and percentile bands to stdout and writes to results/ directory

- [ ] Task 5: Integration test with sample data and documentation
  - What: Create sample OHLCV CSV data, write integration test, and document usage + config schema
  - Files: examples/sample_data/sample_ohlcv.csv, tests/integration/test_full_pipeline.py, README.md (update)
  - Done when: sample CSV has ≥ 500 trading days of synthetic OHLCV data; integration test runs the full pipeline (load → strategy → backtest → MC → metrics → export) and asserts non-empty results with deterministic output; README documents installation, config schema, CLI usage, and interpretation of output metrics