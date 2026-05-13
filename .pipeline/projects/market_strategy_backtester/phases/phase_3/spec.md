## Phase 3 — Optimization, Walk-Forward Analysis & Visualization Dashboard

### Description
Add advanced analytical capabilities: parameter optimization, walk-forward analysis for robustness testing, and an interactive visualization dashboard. This phase makes the tool suitable for production strategy development and validation.

### Deliverable
A production-ready backtesting platform with:
1. Grid search and random search parameter optimization with Monte Carlo-aware scoring.
2. Walk-forward analysis engine (rolling window optimization + out-of-sample validation).
3. Interactive Plotly-based dashboard for exploring simulation results.
4. Performance benchmarking against buy-and-hold and random strategies.
5. Parallel execution for large optimization runs.
6. Strategy performance attribution (sector, regime, time-of-day analysis).
7. Export to JSON/HTML for sharing and archival.

### Dependencies
- Phase 2 (all strategies, metrics, data sources, Monte Carlo variants, reporting).

### Success Criteria
- [ ] Parameter optimization finds Pareto-optimal strategy configurations (Sharpe vs. Drawdown).
- [ ] Walk-forward analysis correctly splits data into in-sample (optimization) and out-of-sample (validation) windows.
- [ ] Out-of-sample performance degradation is quantified and reported.
- [ ] Interactive dashboard allows filtering by strategy, date range, metric, and simulation percentile.
- [ ] Benchmark comparisons (buy-and-hold, random walk) included by default.
- [ ] Parallel execution achieves ≥ 3x speedup on 4-core machines.
- [ ] HTML export produces a self-contained, shareable report.
- [ ] Full test coverage ≥ 80%.

### Tasks
- [ ] Implement `ParameterOptimizer` with grid search and random search
- [ ] Implement Monte Carlo-aware scoring (optimize mean Sharpe with penalty for drawdown variance)
- [ ] Implement `WalkForwardAnalyzer` with configurable window sizes
- [ ] Add out-of-sample performance degradation metric
- [ ] Implement Plotly dashboard with interactive filtering
- [ ] Implement benchmark engine (buy-and-hold, random walk, index comparison)
- [ ] Add parallel execution via `concurrent.futures` or `multiprocessing`
- [ ] Implement performance attribution (regime analysis, sector breakdown)
- [ ] Implement HTML report exporter
- [ ] Implement JSON export for archival
- [ ] Write comprehensive test suite (target ≥ 80% coverage)
- [ ] Performance benchmarking of the engine itself
- [ ] Final documentation, API reference, and example notebooks
- [ ] Release packaging (setup.py / pyproject.toml)

---

## File Structure (Target)

```
market_strategy_backtester/
├── pyproject.toml
├── README.md
├── config/
│   ├── default.yaml
│   └── strategies/
│       ├── sma_crossover.yaml
│       ├── rsi_reversal.yaml
│       ├── bollinger_breakout.yaml
│       └── momentum.yaml
├── src/
│   ├── __init__.py
│   ├── cli.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── csv