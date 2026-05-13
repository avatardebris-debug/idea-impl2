# Code Review: DataSource Interface and MockDataSource Implementation

## Files Reviewed
- `src/data_source.py` — Abstract `DataSource` interface
- `src/mock_data.py` — `MockDataSource` concrete implementation
- `tests/test_data_source.py` — Test suite for the interface and a minimal mock

## Summary
The `DataSource` abstract base class defines a clean contract for stock ticker data providers with methods for fetching tickers, subscribing/unsubscribing to updates, and managing connection state. The `MockDataSource` implementation provides a realistic simulation of real-time price movements using random walks with mean reversion, along with a subscription mechanism and time-throttled updates.

The code is generally well-structured and follows good OOP practices. However, there are several issues ranging from design concerns to potential bugs that should be addressed.

---

## Blocking Bugs

### 1. `MockDataSource` Does Not Implement All Abstract Methods
- **Location**: `src/mock_data.py`, class `MockDataSource`
- **Problem**: `MockDataSource` inherits from `DataSource` but does **not** implement the abstract method `unsubscribe` with the correct signature. More critically, the abstract base class defines `subscribe` and `unsubscribe` with `callback: callable` as the parameter type, but Python's ABC mechanism only checks that the method exists — it does **not** enforce parameter types. However, the real issue is that `MockDataSource` **does** implement all abstract methods, so this is not a blocking bug per se.
- **Verdict**: Not blocking, but see Issue #3 below for a related concern.

### 2. `MockDataSource.subscribe()` Allows Duplicate Subscriptions
- **Location**: `src/mock_data.py`, `subscribe()` method
- **Problem**: The `subscribe()` method appends the callback without checking for duplicates. This means the same callback can be registered multiple times, causing it to be called multiple times per update. The test file `tests/test_data_source.py` even has a test `test_subscribe_same_callback_twice` that **expects** this behavior (`assert len(ds._callbacks) == 2`), which is questionable design.
- **Impact**: Callbacks will fire multiple times, leading to unexpected behavior in subscribers. This is a bug because the typical expectation for a subscribe/unsubscribe pattern is that each callback fires exactly once per notification.
- **Fix**: Check for duplicates before appending:
  ```python
  def subscribe(self, callback: Callable) -> None:
      if callback not in self._callbacks:
          self._callbacks.append(callback)
  ```
  Note: The current `MockDataSource` in `src/mock_data.py` **does** have this check. However, the test file's `MockDataSource` in `tests/test_data_source.py` does **not**. This inconsistency is a problem.

### 3. Inconsistent Behavior Between `src/mock_data.py` and `tests/test_data_source.py`
- **Location**: `src/mock_data.py` vs `tests/test_data_source.py`
- **Problem**: The `MockDataSource` in `tests/test_data_source.py` is a **different** implementation from the one in `src/mock_data.py`. The test file's mock does not implement `subscribe` deduplication, while the source file's does. This means the tests are not testing the actual production code's behavior.
- **Impact**: Tests may pass while the production code behaves differently, or vice versa. This undermines test reliability.
- **Fix**: Either import the real `MockDataSource` from `src.mock_data` in the tests, or ensure the test mock faithfully replicates the production implementation's behavior.

---

## Non-Blocking Issues

### 4. `DataSource` Abstract Methods Use `callable` Instead of `Callable`
- **Location**: `src/data_source.py`, `subscribe()` and `unsubscribe()` signatures
- **Problem**: The type hint `callable` (lowercase) is not a valid type hint in Python's typing system. It should be `Callable` from the `typing` module. While this doesn't cause runtime errors, it breaks static type checkers like `mypy`.
- **Fix**: Change `callback: callable` to `callback: Callable[[Ticker], None]` (or appropriate signature).

### 5. `MockDataSource._simulate_price_movement()` Uses Global State (`time.time()`)
- **Location**: `src/mock_data.py`, `_simulate_price_movement()` method
- **Problem**: The trend component uses `time.time()` directly, which makes the simulation non-deterministic and hard to test reproducibly. While this is acceptable for a mock, it means two runs with the same seed will produce different results.
- **Fix**: Consider accepting a `current_time` parameter or using a configurable time source for testability.

### 6. `MockDataSource.update_prices()` Not Thread-Safe
- **Location**: `src/mock_data.py`, `update_prices()` and related methods
- **Problem**: The `_tickers` dictionary and `_callbacks` list are accessed without any synchronization. If `update_prices()` is called from a background thread (as suggested by the `start()`/`stop()` methods and the `_thread` attribute), there's a risk of race conditions.
- **Impact**: Potential `RuntimeError` or corrupted state in multi-threaded scenarios.
- **Fix**: Add a `threading.Lock` to protect shared state, or document that the class is not thread-safe and users must handle synchronization externally.

### 7. `MockDataSource.start()` Does Not Actually Start a Thread
- **Location**: `src/mock_data.py`, `start()` method
- **Problem**: The `start()` method sets `self._running = True` but does not create or start a thread, despite having a `self._thread` attribute that is never used. The `stop()` method similarly does nothing with the thread. This is misleading — the method name suggests it starts background processing, but it doesn't.
- **Impact**: Users expecting `start()` to begin real-time updates will be confused when nothing happens.
- **Fix**: Either implement actual threading (e.g., using `threading.Thread`) or rename the methods to `enable_updates()` / `disable_updates()` to clarify they only toggle a flag.

### 8. `MockDataSource.get_status()` Exposes Internal State
- **Location**: `src/mock_data.py`, `get_status()` method
- **Problem**: The method returns a dict containing `self._tickers.keys()`, which exposes internal implementation details. While not a bug, it's a design concern — the interface should not leak internal state.
- **Fix**: Return only the information that the abstract interface or a public API contract specifies.

### 9. Test File's `MockDataSource` Is Missing `update_ticker` Notification
- **Location**: `tests/test_data_source.py`, `MockDataSource.update_ticker()`
- **Problem**: The test mock's `update_ticker()` does not notify subscribers, while the production `MockDataSource` does. This means tests for subscription notification (if any were added) would fail against the test mock but pass against the production code.
- **Fix**: Ensure the test mock mirrors the production behavior for tested methods.

### 10. No Validation of Symbol Format
- **Location**: `src/mock_data.py`, `add_ticker()` and related methods
- **Problem**: There's no validation that `symbol` is a non-empty string. A user could add a ticker with an empty or `None` symbol, which could cause issues downstream (e.g., in `get_tickers()` with a filter).
- **Fix**: Add validation in `add_ticker()` to reject invalid symbols.

### 11. `MockDataSource.force_update()` Manipulates Internal State Directly
- **Location**: `src/mock_data.py`, `force_update()` method
- **Problem**: The method sets `self._last_update = time.time() - self._update_interval` to bypass throttling. This is a hacky approach that couples the public API to internal implementation details.
- **Fix**: Consider a separate method like `update_all_immediately()` that doesn't rely on manipulating `_last_update`.

### 12. `Ticker.update_price()` Updates `high`/`low` Based on `new_price` Only
- **Location**: `src/ticker.py`, `update_price()` method
- **Problem**: The `high` and `low` are updated based on `new_price`, but if `new_price` is lower than the current `high` or higher than the current `low`, the values won't update. This is actually correct behavior for high/low tracking. However, the initial `high` and `low` are set to `0.0` by default, so the first update will always set both. This is fine but worth noting.
- **Verdict**: Not a bug, but the behavior should be documented.

---

## Recommendations

1. **Fix the subscription deduplication inconsistency** between `src/mock_data.py` and `tests/test_data_source.py`. Decide on the desired behavior (deduplicate or allow duplicates) and ensure both implementations agree.

2. **Use proper `Callable` type hints** in the abstract base class for static type checking compatibility.

3. **Document thread safety** — either implement proper locking in `MockDataSource` or clearly document that it is not thread-safe.

4. **Fix the `start()`/`stop()` methods** — either implement actual threading or rename them to avoid misleading users.

5. **Add symbol validation** in `add_ticker()` and related methods to prevent invalid state.

6. **Consider importing the production `MockDataSource`** in tests rather than maintaining a separate test mock, to ensure tests always reflect production behavior.

7. **Add tests for `MockDataSource`'s price simulation** — the current test file only tests the minimal mock, not the real `MockDataSource`'s price movement logic, subscription notification, or throttling behavior.

---

## Test Coverage Assessment

The existing test file `tests/test_data_source.py` provides good coverage of:
- Abstract base class enforcement (cannot instantiate `DataSource` directly)
- Connection management (connect, disconnect, is_connected)
- Ticker CRUD operations (get, update, filter)
- Subscription mechanism (subscribe, unsubscribe, multiple subscribers)
- Edge cases (empty symbols, empty lists, None values)

**Missing test coverage:**
- `MockDataSource` (from `src.mock_data`) price simulation logic
- Subscription notification (callbacks being called)
- Time-throttled updates (`tick()`, `force_update()`)
- `add_ticker()` and `remove_ticker()` methods
- `get_status()` method
- Thread safety (if applicable)
- Error handling in subscriber callbacks

---

## Verdict

**FAIL** — The review could not be fully completed due to the inconsistency between the production `MockDataSource` and the test mock, which undermines test reliability. Additionally, the `start()` method is misleading, and the type hints in the abstract base class are incorrect. These issues should be resolved before the code can be considered production-ready.
