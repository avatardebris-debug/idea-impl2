# Market Strategy Backtester

A Monte Carlo-based backtesting engine for trading strategies with comprehensive metrics and risk analysis.

## Features

- **Multiple Strategies**: SMA Crossover, RSI, MACD, and Bollinger Bands strategies
- **Monte Carlo Simulation**: Parametric and historical simulation for risk analysis
- **Comprehensive Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio, VaR, CVaR, Kelly fraction
- **Strategy Comparison**: Compare multiple strategies side-by-side
- **Walk-Forward Analysis**: Validate strategies on out-of-sample data

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from market_strategy_backtester.strategies.sma_crossover import SMACrossoverStrategy
from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.metrics.metrics import MetricsCalculator
from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator
import pandas as pd

# Load price data
price_data = pd.read_csv("data.csv")  # Must have 'date' and 'close' columns

# Create strategy
strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)

# Generate signals
signals = strategy.generate_signals(price_data)

# Run backtest
backtester = Backtester(initial_capital=100000)
result = backtester.run(signals.merge(price_data, on="date", how="left"))

# Compute metrics
calculator = MetricsCalculator()
metrics = calculator.compute_metrics(result["equity"])
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

# Run Monte Carlo simulation
monte_carlo = MonteCarloSimulator(n_days=len(price_data))
curves = monte_carlo.simulate(n_simulations=1000)
print(f"95% VaR: {curves['equity'].iloc[-1].quantile(0.05):.2f}")
```

## Strategies

### SMA Crossover

- **Parameters**: `fast_window`, `slow_window`
- **Logic**: Buy when fast SMA crosses above slow SMA, sell when it crosses below

### RSI

- **Parameters**: `period`, `oversold`, `overbought`
- **Logic**: Buy when RSI crosses above oversold level, sell when it crosses below overbought level

### MACD

- **Parameters**: `fast_period`, `slow_period`, `signal_period`
- **Logic**: Buy when MACD line crosses above signal line, sell when it crosses below

### Bollinger Bands

- **Parameters**: `window`, `std_dev`
- **Logic**: Buy when price crosses below lower band, sell when it crosses above upper band

## Metrics

- **Total Return**: Total percentage return of the strategy
- **Annualized Return**: Annualized percentage return
- **Sharpe Ratio**: Risk-adjusted return using standard deviation
- **Sortino Ratio**: Risk-adjusted return using downside deviation
- **Calmar Ratio**: Return to max drawdown ratio
- **Max Drawdown**: Maximum peak-to-trough decline
- **VaR (95%)**: Value at Risk at 95% confidence level
- **CVaR (95%)**: Conditional Value at Risk at 95% confidence level
- **Kelly Fraction**: Optimal fraction of capital to bet

## Monte Carlo Simulation

### Parametric Simulation

Assumes returns are normally distributed. Uses mean and standard deviation of returns to simulate future equity curves.

### Historical Simulation

Resamples actual returns with replacement to simulate future equity curves.

## Risk Analysis

- **VaR**: Estimates the maximum loss at a given confidence level
- **CVaR**: Estimates the expected loss beyond VaR
- **Kelly Fraction**: Calculates the optimal bet size to maximize long-term growth

## Strategy Comparison

Compare multiple strategies using:

- Total Return
- Sharpe Ratio
- Max Drawdown
- VaR
- CVaR

## Walk-Forward Analysis

Validate strategies on out-of-sample data:

1. Split data into in-sample and out-of-sample periods
2. Optimize strategy parameters on in-sample data
3. Test optimized parameters on out-of-sample data
4. Repeat with rolling windows

## Testing

```bash
pytest test_market_strategy_backtester.py -v
```

## Bug Fixes

This version includes fixes for 12 identified bugs:

1. **Bug 1**: Renamed `run_backtest` to `run` in Backtester
2. **Bug 2**: Corrected look-ahead bias in SMA Crossover Strategy
3. **Bug 3**: Clarified RSI Strategy signal logic
4. **Bug 4**: Fixed Bollinger Bands signal alignment
5. **Bug 5**: Fixed Monte Carlo simulation to use `n_days` instead of `n_trades`
6. **Bug 6**: Added zero variance handling in Monte Carlo
7. **Bug 7**: Fixed VaR/CVaR calculation on trade returns
8. **Bug 8**: Fixed Kelly fraction for no-loss strategies
9. **Bug 9**: Fixed signal length mismatch in comparator
10. **Bug 10**: Added missing price data handling
11. **Bug 11**: Added input validation
12. **Bug 12**: Added RNG type validation

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Submit a pull request

## Acknowledgments

- Inspired by [Backtrader](https://www.backtrader.com/)
- Monte Carlo simulation based on [QuantLib](https://www.quantlib.org/)
- Metrics calculation based on [Pyfolio](https://github.com/quantopian/pyfolio)
