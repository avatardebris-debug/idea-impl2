# Validation Report — Phase 2
## Summary
- Tests: 90 passed, 14 failed
## Verdict: FAIL

### Failed Tests (14)
1. `tests/test_models.py::TestKellyCriterion::test_calculate_from_probability` — TypeError: 'KellyCriterion' object is not subscriptable
2. `tests/test_models.py::TestKellyCriterion::test_calculate_from_odds` — TypeError: 'KellyCriterion' object is not subscriptable
3. `tests/test_models.py::TestKellyCriterion::test_negative_edge` — TypeError: 'KellyCriterion' object is not subscriptable
4. `tests/test_models.py::TestKellyCriterion::test_zero_edge` — TypeError: 'KellyCriterion' object is not subscriptable
5. `tests/test_models.py::TestKLDivergence::test_asymmetric` — KL divergence symmetric (should be asymmetric)
6. `tests/test_strategies.py::TestMACD::test_bullish_crossover` — histogram contains NaN values
7. `tests/test_strategies.py::TestBettingStrategy::test_generate_signal_no_bet` — returned 'BET' instead of 'NO_BET'
8. `tests/test_strategies.py::TestBettingStrategy::test_generate_signal_custom_kelly_fraction` — bet_size 200.0 vs expected 100.0
9. `tests/test_utils.py::TestFormatOdds::test_fractional_odds` — returned '1/2' instead of '3/2'
10. `tests/test_utils.py::TestExpectedValue::test_negative_ev` — returned 0.8 instead of negative value
11. `tests/test_utils.py::TestExpectedValue::test_zero_ev` — returned 1.0 instead of 0.0
12. `tests/test_utils.py::TestExpectedValue::test_invalid_odds` — did not raise ValueError
13. `tests/test_utils.py::TestImpliedProbability::test_low_odds` — precision mismatch with pytest.approx
14. `tests/test_utils.py::TestDecimalOddsFromProbability::test_high_probability` — precision mismatch with pytest.approx

### Root Causes
- **KellyCriterion**: Returns an object instead of a dict (not subscriptable)
- **KLDivergence**: Implementation produces symmetric results instead of asymmetric
- **MACD**: Histogram computation produces NaN values
- **BettingStrategy**: Signal logic and bet size calculation are incorrect
- **FormatOdds**: Fractional odds conversion formula is wrong
- **ExpectedValue**: EV calculation logic is incorrect (not producing negative/zero values as expected)
- **ImpliedProbability / DecimalOddsFromProbability**: Precision tolerance too tight for pytest.approx

### Required Files Status
All required files are present:
- `test_harness_capabilities.py` — present
- `test_all.py` — present
- `test_dependency_system.py` — present
- Core modules: `models.py`, `strategies.py`, `utils.py`, `market.py`, `simulation.py` — all present
- Test files: `test_models.py`, `test_strategies.py`, `test_utils.py`, `test_simulation.py` — all present
