# Fix Report — Phase 2

## Current Issues
# Validation Report — Phase 2
## Summary
- Tests: 53 passed, 31 failed
## Verdict: FAIL

## Details

### Test Results
- **Total tests:** 84
- **Passed:** 53
- **Failed:** 31

### Failure Categories
1. **`MarketType.SPREAD` missing** — Multiple tests in `test_odds.py` fail with `AttributeError: type object 'MarketType' has no attribute 'SPREAD'`. The `MarketType` enum in `dfs_arb/core/models.py` does not include a `SPREAD` member.

2. **Return type mismatches in arbitrage** — Tests in `test_arbitrage.py` fail with errors like `assert [] is None` and `AttributeError: 'list' object has no attribute 'profit_pct'`. The `find_arbitrage` function appears to return a list where tests expect a single object or `None`.

3. **Engine attribute errors** — Tests in `test_engine.py` fail with `AttributeError: 'float' object has no attribute 'odds_format'`. The engine's `odds_format` parameter is being stored as a float instead of a string/enum.

4. **Value assertion errors** — `test_odds.py::TestAmericanToDecimal::test_negative_american` fails with a floating-point precision mismatch (`1.6666666666666665` vs `1.6666666666666667`).

5. **Missing ValueError** — `test_odds.py::TestImpliedProbability::test_invalid_format` fails because the code does not raise `ValueError` for invalid input formats.

### Core Files Present
All core Phase 2 files are present:
- `dfs_arb/core/arbitrage.py`
- `dfs_arb/core/engine.py`
- `dfs_arb/core/models.py`
- `dfs_arb/core/odds.py`
- `dfs_arb/core/promos.py`
- `dfs_arb/__init__.py`
- `dfs_arb/cli.py`
- `tests/test_arbitrage.py`
- `tests/test_engine.py`
- `tests/test_odds.py`
- `tests/test_promos.py`

### Root Causes
The failures indicate the implementation does not match the test expectations. Key issues:
- `MarketType` enum needs a `SPREAD` member
- `find_arbitrage` should return a single `ArbitrageOpportunity` or `None`, not a list
- Engine `odds_format` should be stored as a string/enum, not a float
- Input validation should raise `ValueError` for invalid formats


## Attempt History

### Attempt 1
- **Failures**: 0 (↓ improving)
- **Previous failures**: 1

#### Test Output
```
# Validation Report — Phase 2
## Summary
- Tests: 53 passed, 31 failed
## Verdict: FAIL

## Details

### Test Results
- **Total tests:** 84
- **Passed:** 53
- **Failed:** 31

### Failure Categories
1. **`MarketType.SPREAD` missing** — Multiple tests in `test_odds.py` fail with `AttributeError: type object 'MarketType' has no attribute 'SPREAD'`. The `MarketType` enum in `dfs_arb/core/models.py` does not include a `SPREAD` member.

2. **Return type mismatches in arbitrage** — Tests in `test_arbitrage.py` fail with errors like `assert [] is None` and `AttributeError: 'list' object has no attribute 'profit_pct'`. The `find_arbitrage` function appears to return a list where tests expect a single object or `None`.

3. **Engine attribute errors** — Tests in `test_engine.py` fail with `AttributeError: 'float' object has no attribute 'odds_format'`. The engine's `odds_format` parameter is being stored as a float instead of a string/enum.

4. **Value assertion errors** — `test_odds.py::TestAmericanToDecimal::test_negative_american` fails with a floating-point precision mismatch (`1.6666666666666665` vs `1.6666666666666667`).

5. **Missing ValueError** — `test_odds.py::TestImpliedProbability::test_invalid_format` fails because the code does not raise `ValueError` for invalid input formats.

### Core Files Present
All core Phase 2 files are present:
- `dfs_arb/core/arbitrage.py`
- `dfs_arb/core/engine.py`
- `dfs_arb/core/models.py`
- `dfs_arb/core/odds.py`
- `dfs_arb/core/promos.py`
- `dfs_arb/__init__.py`
- `dfs_arb/cli.py`
- `tests/test_arbitrage.py`
- `tests/test_engine.py`
- `tests/test_odds.py`
- `tests/test_promos.py`

### Root Causes
The failures indicate the implementation does not match the test expectations. Key issues:
- `MarketType` enum needs a `SPREAD` member
- `find_arbitrage` should return a single `ArbitrageOpportunity` or `None`, not a list
- Engine `odds_format` should be stored as a string/enum, not a float
- Input validation should raise `ValueError` for invalid formats

```


### Attempt 2
- **Failures**: 0 (→ stalled)
- **Previous failures**: 0

#### Test Output
```
# Validation Report — Phase 2
## Summary
- Tests: 78 passed, 6 failed
## Verdict: FAIL

## Failed Tests Detail
1. `tests/test_arbitrage.py::TestFindArbitrage::test_three_way_arbitrage` — AttributeError: type object 'MarketType' has no attribute 'MLR'
2. `tests/test_arbitrage.py::TestFindArbitrage::test_three_way_arbitrage_exists` — AttributeError: type object 'MarketType' has no attribute 'MLR'
3. `tests/test_arbitrage.py::TestFindArbitrageWithBankroll::test_arbitrage_with_bankroll` — assert 952.38 == 1000.0 ± 0.001
4. `tests/test_arbitrage.py::TestFindArbitrageWithBankroll::test_max_stake_constraint` — assert 800.0 == 500.0 ± 5.0e-04
5. `tests/test_engine.py::TestArbEngine::test_run_analysis` — AttributeError: 'PromoOffer' object has no attribute 'evaluate'
6. `tests/test_odds.py::TestOddsEntryToDecimal::test_invalid_format_entry` — pydantic ValidationError: odds_format should be 'american', 'decimal' or 'fractional'

## Core Files Present
All core Phase 2 files are present:
- dfs_arb/core/arbitrage.py
- dfs_arb/core/engine.py
- dfs_arb/core/models.py
- dfs_arb/core/odds.py
- dfs_arb/core/promos.py
- tests/test_arbitrage.py
- tests/test_engine.py
- tests/test_odds.py
- tests/test_promos.py

```


### Attempt 3
- **Failures**: 0 (→ stalled)
- **Previous failures**: 0

#### Test Output
```
# Validation Report — Phase 2
## Summary
- Tests: 78 passed, 6 failed
## Verdict: FAIL

## Failed Tests Detail
1. `tests/test_arbitrage.py::TestFindArbitrage::test_three_way_arbitrage` — AttributeError: type object 'MarketType' has no attribute 'MLR'
2. `tests/test_arbitrage.py::TestFindArbitrage::test_three_way_arbitrage_exists` — AttributeError: type object 'MarketType' has no attribute 'MLR'
3. `tests/test_arbitrage.py::TestFindArbitrageWithBankroll::test_arbitrage_with_bankroll` — assert 952.38 == 1000.0 ± 0.001
4. `tests/test_arbitrage.py::TestFindArbitrageWithBankroll::test_max_stake_constraint` — assert 800.0 == 500.0 ± 5.0e-04
5. `tests/test_engine.py::TestArbEngine::test_run_analysis` — AttributeError: 'PromoOffer' object has no attribute 'evaluate'
6. `tests/test_odds.py::TestOddsEntryToDecimal::test_invalid_format_entry` — pydantic ValidationError: odds_format should be 'american', 'decimal' or 'fractional'

## Core Files Present
All core Phase 2 files are present:
- dfs_arb/core/arbitrage.py
- dfs_arb/core/engine.py
- dfs_arb/core/models.py
- dfs_arb/core/odds.py
- dfs_arb/core/promos.py
- tests/test_arbitrage.py
- tests/test_engine.py
- tests/test_odds.py
- tests/test_promos.py

```

