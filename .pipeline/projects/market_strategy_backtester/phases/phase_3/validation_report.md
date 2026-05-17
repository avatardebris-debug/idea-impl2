# Validation Report — Phase 3
## Summary
- Tests: 72 passed, 19 failed
- Total test files: test_all.py (market_strategy_backtester/tests/), test_backtester.py, test_strategies.py
- Core files present: Yes (strategies, engine, metrics, reporting, data, visualizer, cli all exist)

## Failed Tests (19)
### market_strategy_backtester/tests/test_all.py (12 failures)
1. TestSMACrossoverStrategy::test_no_lookahead_bias — AssertionError: np.False_ is not true
2. TestRegistry::test_create_strategy_by_name — TypeError: BollingerBandsStrategy.__init__() got unexpected keyword argument
3. TestMonteCarloSimulator::test_invalid_method_raises_error — ValueError not raised
4. TestMonteCarloSimulator::test_parametric_returns_correct_shape — ValueError: Shape mismatch (10, 101) vs (10, 10)
5. TestMetricsCalculator::test_compute_all_metrics_returns_dict — 'annualized_return' not found
6. TestMetricsCalculator::test_max_drawdown_is_negative — KeyError: 'max_drawdown'
7. TestMetricsCalculator::test_sharpe_ratio_calculation — KeyError: 'sharpe_ratio'
8. TestStrategyComparator::test_compare_returns_dataframe — KeyError: 'annualized_return'
9. TestStrategyComparator::test_get_best_strategy — KeyError: 'annualized_return'
10. TestParameterOptimizer::test_optimize_returns_dataframe — ValueError: No valid parameter combinations
11. TestParameterOptimizer::test_optimize_sorts_by_metric — ValueError: No valid parameter combinations
12. TestWalkForwardAnalyzer::test_analyze_returns_dataframe — ValueError: No valid parameter combinations

### tests/test_backtester.py (5 failures)
13. test_run_backtest_long_data — assert 1999 == 2000
14. test_run_backtest_no_trades_possible — assert 499 == 500
15. test_run_backtest_with_large_price_jumps — assert 499 == 500
16. test_run_backtest_with_negative_returns — assert 499 == 500
17. test_run_backtest_with_positive_returns — assert 499 == 500

### tests/test_strategies.py (2 failures)
18. TestMACDStrategy::test_invalid_params — DID NOT RAISE ValueError
19. TestBollingerBandsStrategy::test_bollinger_bands_computation — assert np.False_ (upper >= middle)

## Verdict: FAIL

Phase 3 code has 19 failing tests across strategies, backtester, metrics, monte_carlo, optimizer, walk_forward, and registry modules. The failures indicate bugs in:
- Strategy parameter validation (MACD, BollingerBands)
- Metrics computation (missing keys: annualized_return, max_drawdown, sharpe_ratio)
- Monte Carlo simulator (invalid method handling, shape mismatches)
- Parameter optimizer and walk-forward analyzer (no valid parameter combinations)
- Strategy comparator (missing metric keys)
- Backtester trade count off-by-one errors
- SMA crossover lookahead bias
- Registry strategy creation (BollingerBandsStrategy init signature mismatch)
