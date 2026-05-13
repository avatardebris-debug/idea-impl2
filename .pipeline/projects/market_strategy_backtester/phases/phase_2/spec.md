## Phase 2 — Strategy Framework & Comprehensive Metrics

### Description
Extend the engine with a richer strategy library, additional data sources, comprehensive risk metrics, and improved reporting. This phase transforms the MVP into a professional-grade backtesting tool.

### Deliverable
A fully-featured backtesting package with:
1. Multiple built-in strategies (SMA Crossover, RSI Reversal, Bollinger Band Breakout, Momentum).
2. Data source abstraction (CSV, Yahoo Finance via `yfinance`, custom adapters).
3. Comprehensive risk metrics (Sortino ratio, Calmar ratio, Kelly fraction, Win Rate, Profit Factor, Beta/Alpha vs. benchmark).
4. Monte Carlo variants (parametric normal, correlated multi-asset, time-series bootstrap).
5. Detailed reporting: equity curve plots, return distribution histograms, drawdown charts, simulation convergence diagnostics.
6. Batch backtesting: run multiple strategies or parameter sets in one invocation.

### Dependencies
- Phase 1 (core engine, data loader, strategy base class, Monte Carlo engine, metrics calculator).

### Success Criteria
- [ ] ≥ 4 strategies implemented and tested.
- [ ] Yahoo Finance integration works for fetching ≥ 5 years of daily data.
- [ ] All risk metrics produce correct values (validated against known benchmarks).
- [ ] Multi-asset Monte Carlo preserves correlation structure.
- [ ] Batch mode can compare ≥ 3 strategies in a single run with tabular comparison output.
- [ ] Reports include publication-quality plots (equity curves with confidence bands, distribution plots).
- [ > 10,000 simulations run in < 60 seconds.

### Tasks
- [ ] Extend data source abstraction with `DataSource` base class
- [ ] Implement `YahooFinanceDataSource` adapter
- [ ] Implement `RSIReversalStrategy`
- [ ] Implement `BollingerBandBreakoutStrategy`
- [ ] Implement `MomentumStrategy`
- [ ] Expand metrics module (Sortino, Calmar, Kelly, Win Rate, Profit Factor, Beta/Alpha)
- [ ] Implement parametric Monte Carlo (normal distribution with empirical mean/var)
- [ ] Implement correlated multi-asset Monte Carlo
- [ ] Add time-series bootstrap (block bootstrap for return autocorrelation)
- [ ] Implement equity curve plotting (Matplotlib/Plotly)
- [ ] Implement return distribution histogram and convergence diagnostics
- [ ] Implement batch backtesting runner
- [ ] Add YAML config for multi-strategy comparison
- [ ] Write unit tests for each strategy and metric
- [ ] Write integration tests with real market data
- [ ] Update documentation with strategy library and config examples

---

