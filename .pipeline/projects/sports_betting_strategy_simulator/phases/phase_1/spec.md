## Phase 1: Core Monte Carlo Engine & Single-Strategy MVP

### Description
Build the foundational simulation engine with a single betting market type, one strategy implementation, and basic performance metrics. This is the smallest useful deliverable — a working simulator that can answer: "If I bet $X on outcome Y with probability Z using strategy S, what is my expected return over N bets?"

### Deliverable
- `engine/monte_carlo.py` — Core Monte Carlo engine that generates N simulated outcomes given market probabilities and odds
- `engine/market.py` — Market model supporting single-market bets (moneyline, point spread, over/under) with decimal, American, and fractional odds
- `strategies/kelly.py` — Kelly criterion strategy (full and fractional)
- `backtest/metrics.py` — Basic performance metrics: total return, ROI, win rate, max drawdown, Sharpe ratio
- `backtest/bankroll.py` — Simple bankroll management (flat stake or Kelly fraction)
- `cli/main.py` — CLI that runs a single simulation and prints results
- A single-market simulation that can answer: "What is the expected P&L of betting 2% of bankroll on +150 odds with 55% true probability over 1,000 bets?"

### Dependencies
- None (foundation phase)

### Success Criteria
1. Engine can simulate 100,000 outcomes for a single market in under 5 seconds
2. Kelly strategy correctly calculates optimal stake given true probability and odds
3. Metrics output includes: total return, ROI, win rate, max drawdown, Sharpe ratio, and final bankroll
4. CLI produces a readable text report of simulation results
5. Simulated results converge to theoretical expected value as N → ∞ (verified with unit tests)
6. All code passes linting and has ≥80% test coverage

---