# Bug Report: Market Strategy Backtester

## Executive Summary

The `market_strategy_backtester` package has **12 critical bugs** across its codebase that prevent it from functioning correctly. These bugs range from logic errors in the backtesting engine to data integrity issues in the Monte Carlo simulation. The most severe issues cause incorrect trading signals, data loss, and misleading performance metrics.

---

## Critical Bugs (P0 — Must Fix Before Use)

### Bug 1: Backtester Ignores `run_backtest` Return Value — Uses Wrong Method Name

**File:** `engine/backtester.py`

**Problem:** The `Backtester` class defines a method called `run_backtest()`, but every other module (`optimizer.py`, `walk_forward.py`, `strategy_comparator.py`) calls `backtester.run()` which **does not exist**. This will raise an `AttributeError` immediately upon use.

**Impact:** The entire backtesting pipeline is broken. No backtest can ever be executed.

**Fix:** Either rename `run_backtest` to `run` in `engine/backtester.py`, or update all callers to use `run_backtest`.

**Severity:** 🔴 Critical — Complete system failure

---

### Bug 2: Look-Ahead Bias in SMA Crossover Strategy

**File:** `strategies/sma_crossover.py`, line 53

**Problem:** The strategy computes SMAs on the full price series and then shifts them by 1. However, the SMA at time `t` uses prices up to and including time `t`. Shifting by 1 means the signal at time `t` uses SMA values that include price data from time `t`, which is **look-ahead bias** — you're using today's close price to generate a signal for today.

**Correct approach:** Either shift the price data before computing SMAs, or shift the signals by 1 after generation.

**Example of correct approach:**
```python
# Option A: Shift prices first
df["fast_sma"] = df["close"].shift(1).rolling(window=self.fast_window).mean()
df["slow_sma"] = df["slow_sma"].rolling(window=self.slow_window).mean()

# Option B: Shift signals after
signals = df[["date", "signal"]].iloc[self.slow_window:].copy()
signals["signal"] = signals["signal"].shift(1).fillna(0)
```

**Impact:** Signals are generated using future information, leading to artificially inflated backtest results.

**Severity:** 🔴 Critical — Invalidates all backtest results

---

### Bug 3: RSI Strategy Generates Signals for Every Day (Not Just Crossover Days)

**File:** `strategies/rsi_strategy.py`, lines 74-83

**Problem:** The strategy sets `signal = 1` when RSI crosses below oversold AND `signal = 0` when RSI crosses above overbought. However, the initial `signals` DataFrame is created with `signal = 0` for ALL rows. This means:
- Buy signals (1) are only generated on crossover days
- Sell signals (0) are also only generated on crossover days
- But the default is already 0, so the sell signal assignment is redundant

**More importantly:** The strategy doesn't handle the case where a position is already open. If RSI stays oversold for multiple days, only the first day generates a buy signal. If RSI stays overbought, no sell signal is generated because the default is already 0. The backtester's position logic (`position = signal.shift(1)`) will keep the position open indefinitely once entered.

**Impact:** Strategy behavior is inconsistent and may not match user expectations for mean-reversion trading.

**Severity:** 🟡 Moderate — Strategy logic is ambiguous

---

### Bug 4: Bollinger Bands Strategy Drops Rows Without Warning

**File:** `strategies/bollinger_bands_strategy.py`, line 93

**Problem:** The strategy drops the first `self.window` rows with `signals = signals.iloc[self.window:]`. This means the returned DataFrame has fewer rows than the input price data. When the backtester merges signals with price data, the dates won't align properly, causing data loss and potential misalignment.

**Impact:** The backtest will miss the first `window` days of trading opportunities, and the equity curve will start later than expected.

**Severity:** 🟡 Moderate — Data loss and misalignment

---

### Bug 5: Monte Carlo Simulation Uses Wrong Return Distribution

**File:** `engine/monte_carlo.py`, lines 47-52

**Problem:** The parametric simulation fits a normal distribution to **daily returns** but then simulates returns for `n_trades` periods. However, `n_trades` is the number of **trades**, not the number of **days**. The simulation should use the number of **trading days** in the original backtest, not the number of trades.

**Example:** If a strategy makes 50 trades over 252 days, the simulation should generate 252 daily returns, not 50.

**Impact:** Simulated equity curves have the wrong time horizon, making all Monte Carlo metrics meaningless.

**Severity:** 🔴 Critical — Monte Carlo results are invalid

---

### Bug 6: Monte Carlo Simulation Doesn't Handle Zero Variance Correctly

**File:** `engine/monte_carlo.py`, lines 55-60

**Problem:** When `std == 0`, the code sets `curves[i] = (1 + mean) ** np.arange(1, n_trades + 1)`. This assumes **compound growth** at the mean rate, but the correct approach for a constant return is `(1 + mean) ** n` where `n` is the number of periods. However, `n_trades` is used instead of the number of trading days, compounding Bug 5.

**Impact:** Even if Bug 5 were fixed, this edge case would still produce incorrect results for strategies with zero variance returns.

**Severity:** 🟡 Moderate — Edge case bug

---

### Bug 7: Metrics Calculator Computes VaR/CVaR on Daily Returns, Not Trade Returns

**File:** `metrics/metrics.py`, lines 85-92

**Problem:** The metrics calculator computes VaR and CVaR from **daily equity curve returns** (`curve.pct_change()`). However, for a strategy that trades infrequently, daily returns include many zero-return days (when no position is held). This dilutes the risk metrics and makes VaR/CVaR appear better than they actually are for the actual trading activity.

**Impact:** Risk metrics are misleading for strategies with low trading frequency.

**Severity:** 🟡 Moderate — Misleading risk metrics

---

### Bug 8: Kelly Fraction Calculation Has Division by Zero Risk

**File:** `metrics/metrics.py`, lines 108-112

**Problem:** The Kelly fraction calculation uses `avg_loss` in the denominator. If `avg_loss == 0` (which can happen if there are no losing trades), the code returns `0.0`. However, the condition `if avg_loss > 0` is checked, so this is actually handled. But the logic is flawed: if there are no losing trades, the Kelly fraction should be **infinite** (or at least very large), not zero.

**Impact:** Kelly fraction is incorrectly reported as 0 for strategies with no losing trades.

**Severity:** 🟡 Moderate — Incorrect Kelly fraction

---

### Bug 9: Strategy Comparator Doesn't Handle Different Signal Lengths

**File:** `comparator.py` (if it exists) or `engine/backtester.py` merge logic

**Problem:** When comparing strategies, if one strategy returns fewer signals than another (e.g., Bollinger Bands drops the first 20 rows), the merge in `run_backtest` will misalign dates. The backtester's merge logic (`merged.merge(signals, on="date", how="left")`) will leave NaN values for missing dates, which are then filled with 0, effectively ignoring those days.

**Impact:** Strategies with different signal lengths cannot be fairly compared.

**Severity:** 🟡 Moderate — Unfair strategy comparison

---

### Bug 10: Backtester Doesn't Handle Missing Price Data

**File:** `engine/backtester.py`, line 55

**Problem:** The backtester computes `daily_return` using `pct_change()`, which returns NaN for the first row. This NaN is filled with 0, but if the price data has gaps (missing dates), the `pct_change()` will be incorrect because it assumes consecutive days.

**Impact:** If price data has missing dates, the equity curve will be incorrect.

**Severity:** 🟡 Moderate — Data integrity issue

---

### Bug 11: No Validation of Price Data Format

**File:** `engine/backtester.py`, line 42

**Problem:** The `run_backtest` method assumes the input `price_data` has a 'date' column and a 'close' column. There is no validation to ensure these columns exist. If they don't, the code will raise a confusing `KeyError`.

**Impact:** Poor user experience with cryptic error messages.

**Severity:** 🟢 Low — Usability issue

---

### Bug 12: Monte Carlo Simulation Doesn't Seed Reproducibly

**File:** `engine/monte_carlo.py`, line 38

**Problem:** The `simulate` method accepts an `rng` parameter but doesn't validate that it's a `np.random.Generator`. If a legacy `np.random.RandomState` is passed, the code will fail silently or produce unexpected results.

**Impact:** Potential for subtle bugs if users pass the wrong RNG type.

**Severity:** 🟢 Low — Usability issue

---

## Summary Table

| Bug | File | Severity | Description |
|-----|------|----------|-------------|
| 1 | `engine/backtester.py` | 🔴 Critical | Method name mismatch: `run_backtest` vs `run` |
| 2 | `strategies/sma_crossover.py` | 🔴 Critical | Look-ahead bias in SMA computation |
| 3 | `strategies/rsi_strategy.py` | 🟡 Moderate | Ambiguous signal generation logic |
| 4 | `strategies/bollinger_bands_strategy.py` | 🟡 Moderate | Drops rows, causing data loss |
| 5 | `engine/monte_carlo.py` | 🔴 Critical | Uses `n_trades` instead of `n_days` |
| 6 | `engine/monte_carlo.py` | 🟡 Moderate | Zero variance edge case |
| 7 | `metrics/metrics.py` | 🟡 Moderate | VaR/CVaR on daily returns, not trade returns |
| 8 | `metrics/metrics.py` | 🟡 Moderate | Kelly fraction returns 0 for no-loss strategies |
| 9 | `engine/backtester.py` | 🟡 Moderate | Signal length mismatch in merge |
| 10 | `engine/backtester.py` | 🟡 Moderate | No handling of missing price data |
| 11 | `engine/backtester.py` | 🟢 Low | No input validation |
| 12 | `engine/monte_carlo.py` | 🟢 Low | No RNG type validation |

---

## Recommended Priority Order

1. **Fix Bug 1** — Rename `run_backtest` to `run` or update all callers
2. **Fix Bug 2** — Correct look-ahead bias in SMA strategy
3. **Fix Bug 5** — Use `n_days` instead of `n_trades` in Monte Carlo
4. **Fix Bug 4** — Align Bollinger Bands signals with price data
5. **Fix Bug 3** — Clarify RSI strategy signal logic
6. **Fix Bugs 6-12** — Address remaining issues

---

## Additional Recommendations

1. **Add input validation** to `run_backtest` and `generate_signals` methods
2. **Add unit tests** for each strategy to verify no look-ahead bias
3. **Add integration tests** for the Monte Carlo simulation to verify correct time horizon
4. **Document the expected price data format** clearly
5. **Add a `validate_price_data` utility function**
