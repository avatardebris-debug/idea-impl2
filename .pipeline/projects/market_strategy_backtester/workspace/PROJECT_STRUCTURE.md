# Project Structure

```
market_strategy_backtester/
├── README.md                    # Project documentation
├── CHANGELOG.md                 # Version history
├── BUG_REPORT.md                # Detailed bug report
├── FIX_PLAN.md                  # Detailed fix plan
├── test_market_strategy_backtester.py  # Comprehensive test suite
├── market_strategy_backtester/
│   ├── __init__.py              # Package initialization
│   ├── strategies/
│   │   ├── __init__.py          # Strategies package
│   │   ├── sma_crossover.py     # SMA Crossover Strategy
│   │   ├── rsi_strategy.py      # RSI Strategy
│   │   ├── macd_strategy.py     # MACD Strategy
│   │   ├── bollinger_bands_strategy.py  # Bollinger Bands Strategy
│   │   └── registry.py          # Strategy registry
│   ├── engine/
│   │   ├── __init__.py          # Engine package
│   │   ├── backtester.py        # Backtester engine
│   │   └── monte_carlo.py       # Monte Carlo simulator
│   └── metrics/
│       ├── __init__.py          # Metrics package
│       └── metrics.py           # Metrics calculator
└── data/
    └── sample_price_data.csv    # Sample price data
```

## File Descriptions

### Root Files

- **README.md**: Project overview, installation, quick start, and usage examples
- **CHANGELOG.md**: Version history and notable changes
- **BUG_REPORT.md**: Detailed bug report with analysis and recommendations
- **FIX_PLAN.md**: Detailed fix plan with implementation details
- **test_market_strategy_backtester.py**: Comprehensive test suite

### Strategies

- **sma_crossover.py**: SMA Crossover Strategy implementation
- **rsi_strategy.py**: RSI Strategy implementation
- **macd_strategy.py**: MACD Strategy implementation
- **bollinger_bands_strategy.py**: Bollinger Bands Strategy implementation
- **registry.py**: Strategy registry for creating and managing strategies

### Engine

- **backtester.py**: Backtester engine for running strategies on price data
- **monte_carlo.py**: Monte Carlo simulator for risk analysis

### Metrics

- **metrics.py**: Metrics calculator for computing performance and risk metrics

### Data

- **sample_price_data.csv**: Sample price data for testing and demonstration

## Dependencies

- **numpy**: Numerical computing
- **pandas**: Data manipulation
- **pytest**: Testing framework

## Testing

Run tests with:

```bash
pytest test_market_strategy_backtester.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Submit a pull request
