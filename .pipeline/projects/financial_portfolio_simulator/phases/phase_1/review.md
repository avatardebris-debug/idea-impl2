# Phase 1 Review — Financial Portfolio Simulator

## What's Good

- **Clean package structure**: All `__init__.py` files properly expose public APIs. The `run_simulation` convenience function is a nice touch for usability.
- **Correct GBM implementation**: The geometric Brownian motion math is sound — drift adjustment (`mu - 0.5*sigma^2`) is properly applied, and prices are guaranteed positive via the exponential.
- **Correlated simulation via Cholesky**: The `MarketSimulator.simulate_correlated` method correctly builds a correlation matrix, performs Cholesky decomposition, and applies it to independent normals. This is the standard approach.
- **Deterministic seeding**: Both `GBM` and `MarketSimulator` support seeding, and `PortfolioSimulator` uses per-iteration seeds for correlated simulations while keeping independent GBMs deterministic. This makes tests reproducible.
- **Good test coverage**: All major code paths are tested — GBM paths, correlated simulation, portfolio simulation with/without strategies, empty portfolios, deterministic behavior, and risk metrics (VaR, percentiles).
- **SimulationResult is well-designed**: The dataclass captures all key metrics (mean, median, std, VaR, percentiles, expected return) and provides a `summary()` method for reporting.
- **Strategy pattern is clean**: The abstract `Strategy` base class with `BuyAndHold` as a concrete implementation follows good OOP design. Easy to extend with new strategies.

## Issues Found

### 1. `PortfolioSimulator.simulate` — GBM seed reuse bug (Medium)

In `PortfolioSimulator.simulate`, when `use_correlated=False`, the code creates `gbm_per_asset` with a fixed seed and then calls `gbm_per_asset[j].simulate_single(...)` for *every* iteration. Since `GBM` uses `np.random.default_rng(seed)`, calling `simulate_single` multiple times on the same GBM instance will produce the *same* random path every iteration — not independent Monte Carlo samples.

**Impact**: The simulation is not truly Monte Carlo for the independent case; all iterations produce identical final values.

**Fix**: Either create a new GBM per iteration, or pass a fresh seed to each `simulate_single` call.

### 2. `PortfolioSimulator.simulate` — `price_paths` variable scope (Low)

The variable `price_paths` is assigned inside the loop but only the *last* iteration's paths are retained after the loop. The docstring says `price_paths` should map ticker → `(n_paths, time_steps+1)`, but the current implementation only stores the last iteration's single path. If the intent is to return all paths, the data structure needs to change.

**Impact**: Misleading API contract. Users expecting all simulated paths will only get the last one.

**Fix**: Either document that only the last iteration's paths are returned, or accumulate all paths into a 3D array.

### 3. `SimulationResult` — VaR naming convention (Low)

`var_95` is set to `np.percentile(final_values, 5)` and `var_99` to `np.percentile(final_values, 1)`. In finance, VaR at 95% confidence typically means the 5th percentile (loss threshold), so the math is correct. However, the naming `var_95` could be misread as "95th percentile" by someone unfamiliar with VaR conventions. The `worst_case_95` property clarifies this, but the attribute name is slightly ambiguous.

**Impact**: Minor readability concern for finance newcomers.

**Fix**: Consider renaming to `var_95_confidence` or adding a clarifying docstring.

### 4. `MarketSimulator.simulate_correlated` — Correlation matrix symmetry not enforced (Low)

If the user passes an asymmetric `correlation_matrix`, Cholesky decomposition will fail silently or produce incorrect results. There's no validation that the matrix is symmetric and positive semi-definite.

**Impact**: Hard-to-debug errors when users pass malformed correlation matrices.

**Fix**: Add validation: check symmetry and positive definiteness, or enforce symmetry via `(corr + corr.T) / 2`.

### 5. `PortfolioSimulator.simulate` — Strategy receives full price paths but only uses final prices (Low)

The `strategy.apply` method receives `price_paths` (full time series) but the `BuyAndHold` strategy ignores it entirely. This is fine for `BuyAndHold`, but the interface doesn't prevent strategies from misusing the data. Also, the strategy is applied *after* computing the final value in each iteration, which means the strategy's rebalancing doesn't affect the current iteration's final value — it only affects the *next* iteration's starting prices.

**Impact**: The strategy's effect is off-by-one iteration. Rebalancing at step t affects prices starting at step t+1, which may be counterintuitive.

**Fix**: Clarify in docs that strategy rebalancing takes effect from the next iteration onward, or apply the strategy before computing the final value.

### 6. `GBM.simulate` — `n_paths` default is `None` but used in `np.zeros((n_paths, ...))` (Medium)

In `GBM.simulate`, if `n_paths` is `None`, `np.zeros((None, ...))` will raise a `TypeError`. The default should be a concrete integer.

**Impact**: Crash if `n_paths` is not provided.

**Fix**: Set a sensible default like `n_paths=1000` or raise a clear error.

### 7. `PortfolioSimulator` — No way to pass custom drift/volatility per asset via `run_simulation` (Low)

The `run_simulation` function accepts `drift` and `volatility` as global parameters, but if a user wants different drift/volatility per asset, they must construct `Asset` objects with `metadata` directly. This is inconsistent with the API design.

**Impact**: Inconsistent API — some parameters are global, others require low-level object construction.

**Fix**: Allow `drift` and `volatility` in the asset dicts passed to `run_simulation`, or document that metadata is the way to set per-asset parameters.

### 8. `PortfolioSimulator.simulate` — `original_prices` restoration is fragile (Medium)

The code saves `original_prices` before the loop and restores them after each iteration by calling `asset.update_price()`. However, if an exception occurs during an iteration, the prices may not be restored, corrupting subsequent iterations.

**Impact**: Non-deterministic behavior if an iteration fails.

**Fix**: Use a `try/finally` block to ensure restoration.

### 9. `SimulationResult` — `confidence_intervals` uses non-standard keys (Low)

The keys `"5_95"` and `"1_99"` are unconventional. Standard notation would be `(5, 95)` and `(1, 99)` as tuples, or `"5th_to_95th"` for clarity.

**Impact**: Minor readability concern.

**Fix**: Use tuple keys or more descriptive string keys.

### 10. `PortfolioSimulator` — `use_correlated` flag behavior is inconsistent (Medium)

When `use_correlated=False` and `n_assets > 1`, the code still builds `asset_specs` with correlation metadata but ignores it. When `use_correlated=True`, it requires `n_assets > 1` to enter the correlated branch. If `n_assets == 1` and `use_correlated=True`, it falls through to the independent GBM branch, which is fine but the flag is misleading.

**Impact**: The `use_correlated` flag doesn't behave as expected for single-asset portfolios.

**Fix**: Either allow correlated simulation for single assets (trivially identity matrix) or document the behavior clearly.
