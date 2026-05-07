## Phase 1 — Core Monte Carlo Engine (MVP)

### Description
Build the foundational backtesting engine capable of running a single strategy with Monte Carlo simulation and outputting basic risk-adjusted metrics. This is the smallest useful deliverable: a working system that can take price data, apply a strategy, run Monte Carlo simulations, and produce interpretable results.

### Deliverable
A runnable Python module/package that:
1. Loads historical OHLCV price data from CSV files.
2. Implements a base `Strategy` class and one concrete strategy (e.g., SMA Crossover).
3. Runs a Monte Carlo simulation using bootstrap resampling of strategy returns.
4. Outputs summary statistics (mean return, Sharpe ratio, max drawdown, VaR) across simulations.
5. Exports results to CSV and a basic text summary.

### Dependencies
- None (Phase 1 is the foundation; subsequent phases depend on it).

### Success Criteria
- [ ] Can load a CSV with at least 2 years of daily OHLCV data.
- [ ] SMA Crossover strategy generates valid buy/sell signals (no look-ahead bias).
- [ ] Monte Carlo engine runs ≥ 1,000 simulations in < 30 seconds on a standard laptop.
- [ ] Output includes: mean annualized return, Sharpe ratio, max drawdown, 95% VaR, equity curve percentiles.
- [ ] Results are reproducible (deterministic with seed control).
- [ ] CLI entry point: `python -m market_strategy_backtester run --config config.yaml`

### Tasks
- [ ] Create project structure and package layout
- [ ] Implement data loader (CSV → DataFrame with OHLCV columns)
- [ ] Implement `Strategy` base class with abstract `generate_signals()`
- [ ] Implement `SMACrossoverStrategy` (e.g., 50/200-day SMA)
- [ ] Implement core backtester: apply strategy → compute per-trade returns → simulate
- [ ] Implement bootstrap Monte Carlo engine (resample return series, re-aggregate)
- [ ] Implement basic metrics calculator (Sharpe, max drawdown, VaR)
- [ ] Implement result formatter (CSV export + text summary)
- [ ] Implement CLI entry point with YAML config support
- [ ] Write integration test with sample data
- [ ] Document usage and config schema

---