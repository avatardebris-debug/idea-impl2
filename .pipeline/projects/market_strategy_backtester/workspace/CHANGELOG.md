# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite for all strategies and components
- Input validation for price data
- Zero variance handling in Monte Carlo simulation
- Kelly fraction fix for no-loss strategies
- Strategy comparison functionality
- Walk-forward analysis support

### Changed
- Renamed `run_backtest` to `run` in Backtester
- Corrected look-ahead bias in SMA Crossover Strategy
- Fixed RSI Strategy signal logic
- Fixed Bollinger Bands signal alignment
- Fixed Monte Carlo simulation to use `n_days` instead of `n_trades`
- Fixed VaR/CVaR calculation on trade returns
- Fixed signal length mismatch in comparator
- Added missing price data handling
- Added RNG type validation

### Fixed
- Bug 1: Method name mismatch in Backtester
- Bug 2: Look-ahead bias in SMA Crossover Strategy
- Bug 3: RSI Strategy signal logic
- Bug 4: Bollinger Bands signal alignment
- Bug 5: Monte Carlo simulation time horizon
- Bug 6: Zero variance in Monte Carlo simulation
- Bug 7: VaR/CVaR calculation
- Bug 8: Kelly fraction for no-loss strategies
- Bug 9: Signal length mismatch
- Bug 10: Missing price data handling
- Bug 11: Input validation
- Bug 12: RNG type validation

## [1.0.0] - 2023-10-01

### Added
- Initial release
- SMA Crossover Strategy
- RSI Strategy
- MACD Strategy
- Bollinger Bands Strategy
- Backtester engine
- Monte Carlo simulator
- Metrics calculator
- Strategy registry
