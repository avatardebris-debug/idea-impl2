# Code Review — Phase 1

## Scope
Review of all Phase 1 deliverables:
- `src/dashboard/models.py` — Four metric dataclasses with serialization
- `src/dashboard/tickers.py` — `DashboardTicker` extending `Ticker`
- `src/dashboard/data_source.py` — `DashboardDataSource` extending `MockDataSource`
- `src/dashboard/demo_cli.py` — CLI demo script
- `tests/test_dashboard_models.py` — Model unit tests
- `tests/test_dashboard_data_source.py` — Data source and ticker unit tests

---

## Blocking Bugs

### 1. `DashboardDataSource` inherits from `MockDataSource` but does not call `super().__init__`

**File:** `src/dashboard/data_source.py`

`DashboardDataSource.__init__` sets `self.interval`, `self.running`, `self.callbacks`, `self._thread`, `self._lock`, and `self._stop_event` manually. However, `MockDataSource.__init__` also sets these same attributes. The subclass does not call `super().__init__()`, so the parent's `__init__` is never executed.

This is not a crash on its own because the subclass overwrites all the same attributes. However, it is a **design smell** and a **maintenance hazard**: if `MockDataSource.__init__` ever adds a new attribute (e.g., `self._config = {}`), the subclass will silently miss it.

**Recommendation:** Call `super().__init__(interval=interval)` at the top of `DashboardDataSource.__init__` and remove the redundant attribute assignments.

```python
def __init__(
    self,
    initial_bankroll: float = 1000.0,
    seed: int = 42,
    interval: float = 1.0,
):
    super().__init__(interval=interval)  # <-- ADD THIS
    self.initial_bankroll = initial_bankroll
    self.seed = seed
    self._bankroll = initial_bankroll
    self._peak_bankroll = initial_bankroll
    self._total_games = 0
    self._wins = 0
    self._step = 0
    self._ticker = DashboardTicker()
```

### 2. `DashboardDataSource._generate_update` does not use `self.interval`

**File:** `src/dashboard/data_source.py`

The `_generate_update` method is called by `MockDataSource._run_loop` every `self.interval` seconds. However, `_generate_update` itself does not reference `self.interval` — it only uses `self._step`, `self._bankroll`, etc. This is fine functionally, but the method signature and docstring in `MockDataSource` say:

> "Override in subclasses to return the actual data dict."

The subclass correctly overrides `_generate_update`. No bug here, but worth noting that the `interval` parameter is only used by the parent's `_run_loop`, not by the subclass's update logic. This is by design and is acceptable.

### 3. `DashboardDataSource.force_update` calls `_notify` but `_notify` is not thread-safe for the `callbacks` list

**File:** `src/dashboard/data_source.py`

`MockDataSource._notify` acquires `self._lock` before iterating over `self.callbacks`. This is correct. However, `DashboardDataSource.force_update` calls `self._notify(payload)` directly. If a callback is registered from another thread while `force_update` is executing, the lock protects the iteration. This is fine.

No bug here.

### 4. `DashboardDataSource.start` can be called multiple times without error, but the thread is not duplicated

**File:** `src/dashboard/data_source.py`

The `start` method checks `if self.running: return`, which prevents duplicate threads. The test `test_start_does_not_duplicate_thread` confirms this. No bug.

### 5. `DashboardDataSource.stop` calls `self._thread.join(timeout=...)` but `self._thread` may be `None` if `start` was never called

**File:** `src/dashboard/data_source.py`

The `stop` method checks `if self._thread is not None` before calling `join`. The test `test_stop_without_start_is_safe` confirms this. No bug.

### 6. `DashboardTicker.price_color` logic differs from `Ticker.price_color` logic

**File:** `src/dashboard/tickers.py`

`Ticker.price_color` (base class) uses `previous_price` to determine color:
- green if `price > previous_price`
- red if `price < previous_price`
- white otherwise

`DashboardTicker.price_color` (override) uses `current_win_rate.value` to determine color:
- green if `value > 0.5`
- red if `value < 0.5`
- white if `value == 0.5`

This is an **intentional override** and is correct for the domain (win rate, not price direction). However, the docstring of `Ticker.price_color` says "Return a color hint based on price direction" which is misleading for `DashboardTicker`. The override is correct but the base class docstring should be clarified or the override should have its own docstring.

**Recommendation:** Add a docstring to `DashboardTicker.price_color` explaining the win-rate-based logic.

### 7. `DashboardTicker.from_dict` raises on `None` values but the test `test_from_dict_with_none_values_raises` expects this

**File:** `src/dashboard/tickers.py`

The `from_dict` method does not explicitly handle `None` values. If `data["current_win_rate"]` is `None`, then `WinRateMetric.from_dict(None)` will be called, which will raise an `AttributeError` (since `None` has no `.get()` method). The test expects `(TypeError, ValueError)` to be raised, but the actual exception is `AttributeError`.

**Bug:** The test assertion is incorrect. It should expect `AttributeError` or the `from_dict` method should validate inputs and raise `ValueError`.

**Recommendation:** Either:
- Update the test to expect `AttributeError`, or
- Add input validation in `DashboardTicker.from_dict` to raise `ValueError` with a clear message.

### 8. `DashboardDataSource._generate_update` uses `random.Random(self.seed)` but does not re-seed per update

**File:** `src/dashboard/data_source.py`

The `random.Random(self.seed)` instance is created once in `__init__` and reused. This means the sequence of random numbers is deterministic and reproducible, which is good for testing. However, if the seed is not set (default `42`), all instances will produce the same sequence. This is acceptable for a demo but should be documented.

No bug.

---

## Warnings

### 9. `DashboardDataSource._generate_update` does not handle division by zero in win rate calculation

**File:** `src/dashboard/data_source.py`

```python
win_rate = self._wins / self._total_games if self._total_games > 0 else 0.0
```

This is correctly guarded. No bug.

### 10. `DashboardDataSource._generate_update` does not handle negative bankroll

**File:** `src/dashboard/data_source.py`

The bankroll can go negative if losses exceed the current bankroll. The test `test_force_update_bankroll_non_negative` asserts `state.bankroll.bankroll >= 0.0`, which means the implementation must prevent negative bankrolls. Looking at the code:

```python
# Simulate a game result
result = self._rng.choice(["win", "loss"])
if result == "win":
    self._bankroll += self._bankroll * 0.01  # 1% gain
else:
    self._bankroll -= self._bankroll * 0.01  # 1% loss
```

With a 1% loss, the bankroll decreases but never goes negative (it approaches zero asymptotically). With a 1% gain, it increases. So the bankroll is always non-negative. The test is correct.

No bug.

### 11. `DashboardDataSource._generate_update` does not handle the case where `self._bankroll` becomes very small

**File:** `src/dashboard/data_source.py`

As the bankroll approaches zero, the 1% gain/loss becomes very small. This is mathematically correct but may cause floating-point precision issues over many iterations. For a demo, this is acceptable.

No bug.

### 12. `DashboardDataSource._generate_update` does not handle the case where `self._total_games` overflows

**File:** `src/dashboard/data_source.py`

Python integers have arbitrary precision, so overflow is not an issue. No bug.

### 13. `DashboardDataSource._generate_update` does not handle the case where `self._wins` exceeds `self._total_games`

**File:** `src/dashboard/data_source.py`

The code increments `self._wins` only when `result == "win"`, and `self._total_games` is incremented every update. So `self._wins <= self._total_games` is always true. No bug.

### 14. `DashboardDataSource._generate_update` does not handle the case where `self._peak_bankroll` is not updated correctly

**File:** `src/dashboard/data_source.py`

```python
if self._bankroll > self._peak_bankroll:
    self._peak_bankroll = self._bankroll
```

This is correct. No bug.

### 15. `DashboardDataSource._generate_update` does not handle the case where `self._drawdown` is calculated incorrectly

**File:** `src/dashboard/data_source.py`

```python
drawdown = (self._bankroll - self._peak_bankroll) / self._peak_bankroll if self._peak_bankroll > 0 else 0.0
```

This is correct. No bug.

### 16. `DashboardDataSource._generate_update` does not handle the case where `self._nash_distance` is calculated incorrectly

**File:** `src/dashboard/data_source.py`

```python
nash_distance = self._rng.uniform(0.0, 0.15) + self._rng.uniform(0.0, 0.05) * self._step / 100
```

This produces a value in `[0.0, 0.35]` approximately. The test `test_force_update_nash_distance_range` asserts `0.0 <= state.nash_shift.distance <= 0.35`. This is correct.

No bug.

### 17. `DashboardDataSource._generate_update` does not handle the case where `self._timestamp` is not updated

**File:** `src/dashboard/data_source.py`

```python
timestamp = time.time()
```

This is correct. No bug.

### 18. `DashboardDataSource._generate_update` does not handle the case where `self._ticker` is not updated

**File:** `src/dashboard/data_source.py`

```python
self._ticker.update_from_state(state)
```

This is correct. No bug.

### 19. `DashboardDataSource._generate_update` does not handle the case where `self._ticker` is `None`

**File:** `src/dashboard/data_source.py`

`self._ticker` is initialized in `__init__` as `DashboardTicker()`. It is never set to `None`. No bug.

### 20. `DashboardDataSource._generate_update` does not handle the case where `self._ticker.update_from_state` raises

**File:** `src/dashboard/data_source.py`

If `update_from_state` raises an exception, it will propagate up to `_run_loop` or `force_update`. The `_run_loop` does not catch exceptions, so the thread will die. The `force_update` method does not catch exceptions either.

**Recommendation:** Consider wrapping the update logic in a try/except to prevent the background thread from dying on unexpected errors.

---

## Suggestions

### 21. Consider using `dataclasses.field(default_factory=time.time)` for timestamp fields

**File:** `src/dashboard/models.py`

The `timestamp` field in all four dataclasses uses `field(default_factory=time.time)`. This is correct and consistent. No change needed.

### 22. Consider adding `__repr__` methods to dataclasses for debugging

**File:** `src/dashboard/models.py`

The dataclasses use `@dataclass` which generates a default `__repr__`. This is sufficient for debugging. No change needed.

### 23. Consider adding type hints to `DashboardDataSource._generate_update`

**File:** `src/dashboard/data_source.py`

The method signature is:

```python
def _generate_update(self) -> Dict[str, Any]:
```

This is correct. No change needed.

### 24. Consider adding docstrings to `DashboardDataSource` methods

**File:** `src/dashboard/data_source.py`

The `__init__`, `force_update`, and `_generate_update` methods have docstrings. The `start` and `stop` methods inherit docstrings from `MockDataSource`. No change needed.

### 25. Consider adding a `__main__` block to `demo_cli.py`

**File:** `src/dashboard/demo_cli.py`

The script has a `if __name__ == "__main__":` block. No change needed.

### 26. Consider adding a `--help` flag to `demo_cli.py`

**File:** `src/dashboard/demo_cli.py`

The script uses `argparse` but does not add a `--help` flag. By default, `argparse` adds `--help`. No change needed.

### 27. Consider adding a `--interval` flag to `demo_cli.py`

**File:** `src/dashboard/demo_cli.py`

The script does not expose the `interval` parameter. This is acceptable for a demo. No change needed.

### 28. Consider adding a `--seed` flag to `demo_cli.py`

**File:** `src/dashboard/demo_cli.py`

The script does not expose the `seed` parameter. This is acceptable for a demo. No change needed.

### 29. Consider adding a `--initial-bankroll` flag to `demo_cli.py`

**File:** `src/dashboard/demo_cli.py`

The script does not expose the `initial_bankroll` parameter. This is acceptable for a demo. No change needed.

### 30. Consider adding a `--duration` flag to `demo_cli.py`

**File:** `src/dashboard/demo_cli.py`

The script does not expose a duration parameter. The script runs indefinitely until interrupted. This is acceptable for a demo. No change needed.

---

## Summary

### Blocking Bugs (must fix before merge)
1. **`DashboardDataSource` does not call `super().__init__()`** — This is a design smell and maintenance hazard. Fix by calling `super().__init__(interval=interval)`.
2. **`DashboardTicker.from_dict` test expects wrong exception type** — The test expects `(TypeError, ValueError)` but the actual exception is `AttributeError`. Fix the test or add input validation.

### Warnings (should fix before merge)
3. **`DashboardDataSource._generate_update` does not handle exceptions from `update_from_state`** — Consider wrapping in try/except to prevent thread death.

### Suggestions (nice-to-have)
4. **Add docstring to `DashboardTicker.price_color`** — Clarify the win-rate-based logic.
5. **Document the deterministic seed behavior** — Note that all instances with the default seed produce the same sequence.

### Overall Assessment
The code is well-structured and the tests are comprehensive. The main issues are the missing `super().__init__()` call and the incorrect exception type in the test. These are easy to fix and should be addressed before merging.
