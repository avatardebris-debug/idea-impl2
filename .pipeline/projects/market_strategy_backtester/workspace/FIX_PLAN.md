# Fix Plan: Market Strategy Backtester

## Overview

This document provides detailed fix instructions for all 12 bugs identified in the bug report. Each fix includes the exact code changes needed.

---

## Fix 1: Rename `run_backtest` to `run` in Backtester

**File:** `engine/backtester.py`

**Change:** Rename the method `run_backtest` to `run` to match all callers.

```python
# Before:
def run_backtest(self, price_data: pd.DataFrame) -> pd.DataFrame:

# After:
def run(self, price_data: pd.DataFrame) -> pd.DataFrame:
```

---

## Fix 2: Correct Look-Ahead Bias in SMA Crossover Strategy

**File:** `strategies/sma_crossover.py`

**Change:** Shift the price data before computing SMAs to ensure signals are based on past data only.

```python
# Before (lines 48-53):
df = price_data[["date", "close"]].copy()
df["fast_sma"] = df["close"].rolling(window=self.fast_window).mean()
df["slow_sma"] = df["slow_sma"].rolling(window=self.slow_window).mean()
df["fast_sma"] = df["fast_sma"].shift(1)
df["slow_sma"] = df["slow_sma"].shift(1)

# After:
df = price_data[["date", "close"]].copy()
# Shift close price by 1 to avoid look-ahead bias
df["close_shifted"] = df["close"].shift(1)
df["fast_sma"] = df["close_shifted"].rolling(window=self.fast_window).mean()
df["slow_sma"] = df["close_shifted"].rolling(window=self.slow_window).mean()
```

---

## Fix 3: Clarify RSI Strategy Signal Logic

**File:** `strategies/rsi_strategy.py`

**Change:** Add explicit position tracking to handle multi-day oversold/overbought conditions.

```python
# After line 83 (end of generate_signals):
# Add position tracking
signals["position"] = 0
signals.loc[buy_mask, "position"] = 1
signals.loc[sell_mask, "position"] = -1
# Forward fill position to handle multi-day conditions
signals["position"] = signals["position"].ffill().fillna(0)

# Update signal column to reflect position
signals["signal"] = signals["position"].apply(lambda x: 1 if x == 1 else 0)
```

---

## Fix 4: Align Bollinger Bands Signals with Price Data

**File:** `strategies/bollinger_bands_strategy.py`

**Change:** Instead of dropping rows, fill the first `window` rows with NaN signals and let the backtester handle them.

```python
# Before (lines 90-93):
signals.loc[buy_mask, "signal"] = 1
signals.loc[sell_mask, "signal"] = 0
signals = signals.iloc[self.window:]
return signals.reset_index(drop=True)

# After:
signals.loc[buy_mask, "signal"] = 1
signals.loc[sell_mask, "signal"] = 0
# Fill first window rows with NaN (will be filled with 0 by backtester)
signals["signal"] = signals["signal"].fillna(0)
return signals[["date", "signal"]].reset_index(drop=True)
```

---

## Fix 5: Use `n_days` Instead of `n_trades` in Monte Carlo

**File:** `engine/monte_carlo.py`

**Change:** Pass the number of trading days to the simulation instead of the number of trades.

```python
# In engine/backtester.py, update the call to simulate:
# Before:
monte_carlo = MonteCarloSimulator(n_trades=len(signals))

# After:
monte_carlo = MonteCarloSimulator(n_days=len(price_data))

# In engine/monte_carlo.py, update the __init__ and simulate methods:
# Before:
def __init__(self, n_trades: int):
    self.n_trades = n_trades

def simulate(self, n_simulations: int = 1000, rng: Optional[np.random.Generator] = None) -> pd.DataFrame:
    n_trades = self.n_trades

# After:
def __init__(self, n_days: int):
    self.n_days = n_days

def simulate(self, n_simulations: int = 1000, rng: Optional[np.random.Generator] = None) -> pd.DataFrame:
    n_days = self.n_days
```

---

## Fix 6: Handle Zero Variance in Monte Carlo

**File:** `engine/monte_carlo.py`

**Change:** Add explicit handling for zero variance case.

```python
# In simulate method, after line 52:
# Before:
if std == 0:
    curves[i] = (1 + mean) ** np.arange(1, n_trades + 1)

# After:
if std == 0:
    if mean == 0:
        curves[i] = np.ones(n_days)  # No growth
    else:
        curves[i] = (1 + mean) ** np.arange(1, n_days + 1)
```

---

## Fix 7: Compute VaR/CVaR on Trade Returns, Not Daily Returns

**File:** `metrics/metrics.py`

**Change:** Filter to only include days with non-zero positions when computing VaR/CVaR.

```python
# After line 84:
# Before:
daily_returns = curve.pct_change().dropna()

# After:
# Filter to days with non-zero positions (if position column exists)
if "position" in curve.columns:
    trading_days = curve[curve["position"] != 0]
    daily_returns = trading_days["equity"].pct_change().dropna()
else:
    daily_returns = curve["equity"].pct_change().dropna()
```

---

## Fix 8: Fix Kelly Fraction for No-Loss Strategies

**File:** `metrics/metrics.py`

**Change:** Return a large value (e.g., 1.0) for strategies with no losing trades.

```python
# After line 112:
# Before:
if avg_loss > 0:
    kelly = (avg_win * win_rate - avg_loss * (1 - win_rate)) / avg_win
else:
    kelly = 0.0

# After:
if avg_loss > 0:
    kelly = (avg_win * win_rate - avg_loss * (1 - win_rate)) / avg_win
elif win_rate == 1.0:
    kelly = 1.0  # All wins, use full Kelly
else:
    kelly = 0.0  # No trades
```

---

## Fix 9: Handle Different Signal Lengths in Comparator

**File:** `engine/backtester.py`

**Change:** Align signals by date before merging.

```python
# After line 54:
# Before:
merged = price_data.merge(signals, on="date", how="left")

# After:
# Ensure signals have the same date range as price_data
signals = signals.set_index("date")
price_data = price_data.set_index("date")
merged = price_data.join(signals, how="left").reset_index()
merged["signal"] = merged["signal"].fillna(0)
```

---

## Fix 10: Handle Missing Price Data

**File:** `engine/backtester.py`

**Change:** Add validation for consecutive dates.

```python
# After line 42:
# Before:
def run(self, price_data: pd.DataFrame) -> pd.DataFrame:

# After:
def run(self, price_data: pd.DataFrame) -> pd.DataFrame:
    # Validate input
    if "date" not in price_data.columns:
        raise ValueError("price_data must have a 'date' column")
    if "close" not in price_data.columns:
        raise ValueError("price_data must have a 'close' column")
    
    # Check for missing dates
    price_data = price_data.sort_values("date").reset_index(drop=True)
    date_range = pd.date_range(start=price_data["date"].min(), end=price_data["date"].max(), freq="D")
    if len(date_range) != len(price_data):
        warnings.warn("Price data has missing dates. Filling with forward fill.")
        price_data = price_data.set_index("date").reindex(date_range).ffill().reset_index()
        price_data.columns = ["date", "close"]
```

---

## Fix 11: Add Input Validation

**File:** `engine/backtester.py`

**Change:** Already included in Fix 10.

---

## Fix 12: Validate RNG Type in Monte Carlo

**File:** `engine/monte_carlo.py`

**Change:** Add type checking for RNG parameter.

```python
# After line 38:
# Before:
def simulate(self, n_simulations: int = 1000, rng: Optional[np.random.Generator] = None) -> pd.DataFrame:

# After:
def simulate(self, n_simulations: int = 1000, rng: Optional[np.random.Generator] = None) -> pd.DataFrame:
    if rng is None:
        rng = np.random.default_rng()
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a np.random.Generator instance")
```

---

## Testing Plan

1. **Unit Tests:**
   - Test each strategy with known inputs to verify no look-ahead bias
   - Test Monte Carlo simulation with known distributions
   - Test metrics calculation with known equity curves

2. **Integration Tests:**
   - Test full backtesting pipeline with sample data
   - Test Monte Carlo simulation with sample backtest results
   - Test strategy comparison with multiple strategies

3. **Regression Tests:**
   - Compare results before and after fixes to ensure no regression

---

## Estimated Effort

| Fix | Estimated Effort |
|-----|-----------------|
| 1 | 5 minutes |
| 2 | 15 minutes |
| 3 | 30 minutes |
| 4 | 15 minutes |
| 5 | 30 minutes |
| 6 | 10 minutes |
| 7 | 20 minutes |
| 8 | 10 minutes |
| 9 | 20 minutes |
| 10 | 20 minutes |
| 11 | Included in Fix 10 |
| 12 | 5 minutes |

**Total Estimated Effort:** ~3 hours
