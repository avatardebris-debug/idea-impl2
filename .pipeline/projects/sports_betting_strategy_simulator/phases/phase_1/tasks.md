# Phase 1 Tasks

- [ ] Task 1: Market model with odds conversion and probability representation
  - What: Implement the Market class supporting moneyline, point spread, and over/under bet types. Include decimal, American, and fractional odds formats with bidirectional conversion. Represent implied probability and allow a configurable "true probability" for edge calculation.
  - Files: engine/market.py
  - Done when: Market class can create a market with any odds format, convert between all three formats, compute implied probability, and store true probability. Unit tests verify odds conversions are lossless (e.g., decimal 2.50 ↔ American +150 ↔ fractional 3/2) and implied probability is correct.

- [ ] Task 2: Core Monte Carlo simulation engine
  - What: Implement the Monte Carlo engine that generates N simulated outcomes for a single market. Use NumPy vectorized operations (np.random.binomial or np.random.choice) to sample outcomes efficiently. Support configurable seed for reproducibility. Return an array of boolean wins and per-bet P&L.
  - Files: engine/monte_carlo.py
  - Done when: Engine can simulate 100,000 outcomes for a single market in under 5 seconds. Results converge to the theoretical expected value as N increases (verified: simulated win rate approaches true probability within 1% at N=10,000). Unit tests verify vectorized sampling and convergence behavior.

- [ ] Task 3: Kelly criterion strategy implementation
  - What: Implement the Kelly criterion strategy (full and fractional variants). Given true probability and odds, calculate the optimal fraction of bankroll to bet. Support configurable fractional Kelly (e.g., half-Kelly = 0.5 * full Kelly fraction). Implement the abstract strategy interface with a `stake(bankroll, market)` method.
  - Files: strategies/kelly.py
  - Done when: Full Kelly correctly computes optimal stake = (p*b - q) / b where p = true probability, b = decimal odds - 1, q = 1 - p. Fractional Kelly scales this by a configurable factor. Unit tests verify Kelly fraction against known analytical solutions (e.g., p=0.55, decimal odds=2.0 → Kelly fraction = 0.10).

- [ ] Task 4: Bankroll management and backtest runner
  - What: Implement the Bankroll class that tracks bankroll evolution across a sequence of bets. Support flat-stake and Kelly-fraction stake sizing modes. Implement the backtest runner that iterates through simulated bets, applies the strategy to determine stake, resolves the outcome, and updates the bankroll. Record per-bet state (stake, result, bankroll after bet).
  - Files: backtest/bankroll.py, backtest/runner.py
  - Done when: Bankroll correctly updates after each bet (wins add stake * (odds_decimal - 1), losses subtract stake). Runner produces a list of bet records with stake, win/loss, and running bankroll. Unit tests verify bankroll math and runner iteration logic.

- [ ] Task 5: Performance metrics computation
  - What: Implement the metrics module that computes total return, ROI, win rate, max drawdown, Sharpe ratio, and final bankroll from a sequence of bet results. Use NumPy for efficient computation. Max drawdown should be computed from the equity curve. Sharpe ratio should use per-bet returns annualized or per-session as appropriate.
  - Files: backtest/metrics.py
  - Done when: Metrics module computes all six required outputs: total return (final bankroll / initial bankroll - 1), ROI (net profit / total wagered), win rate (wins / total bets), max drawdown (largest peak-to-trough decline in bankroll), Sharpe ratio (mean per-bet return / std per-bet return), and final bankroll. Unit tests verify each metric against hand-calculated examples.

- [ ] Task 6: CLI interface and end-to-end simulation
  - What: Implement the CLI that accepts parameters (odds format, odds value, true probability, bankroll, stake fraction, number of bets, strategy type, seed) and runs a full simulation. Print a readable text report with all performance metrics. Default to the example scenario: 2% Kelly stake on +150 odds with 55% true probability over 1,000 bets.
  - Files: cli/main.py
  - Done when: CLI runs a single simulation and prints a formatted report including: strategy used, market parameters, number of bets, total return, ROI, win rate, max drawdown, Sharpe ratio, and final bankroll. Default run produces sensible output for the example scenario. Unit tests verify CLI argument parsing and output format.