# Phase 1 Review — Dynamic Pricing Integrator

## What's Good
- Package structure is clean and well-organized: `constants.py`, `config.py`, `models.py`, `mock_sources.py`, `price_tracker.py` all serve distinct responsibilities.
- `PricingConfig` dataclass correctly uses `field(default_factory=list)` for the mutable `competitor_sources` default — avoids the common mutable-default pitfall.
- `Product` dataclass defaults `currency` to `DEFAULT_CURRENCY` from constants, keeping defaults centralized.
- `CompetitorPrice` dataclass defaults `last_updated` to `datetime.now()` via `field(default_factory=datetime.now)`, which is correct.
- `PriceSnapshot` dataclass has all required fields (`product_id`, `competitor`, `price`, `timestamp`, `source`) with correct types.
- `MockAPISource` and `MockCSVSource` both return 2 `CompetitorPrice` entries with different competitor names and prices, satisfying the spec.
- `MockCSVSource` handles CSV parsing with header skip, whitespace stripping, and `ValueError` protection for bad price values.
- `PriceTracker.add_source` correctly guards against duplicate entries.
- `PriceTracker.remove_source` safely handles removal of non-existent sources (no exception).
- `poll_all()` uses a single `datetime.now()` call for consistency across all snapshots from the same poll cycle.
- `get_current_price()` correctly filters by `product_id` and returns `None` when no data exists.
- `__init__.py` exports all public classes and constants via `__all__`, enabling clean public API.
- `conftest.py` correctly injects the workspace into `sys.path` for local imports.
- 32 tests all pass, covering all 17 required scenarios plus extras (duplicate add, empty poll, nonexistent remove, etc.).

## Blocking Bugs
None

## Non-Blocking Notes
- `price_tracker.py`: `poll_all()` passes an empty string `""` as `product_id` to `source.fetch_prices("")` (line 56). This means snapshots from `poll_all()` will have `product_id=""` rather than a meaningful product ID. The `get_current_price()` method works around this by re-polling with the actual `product_id`, but `poll_all()`'s behavior is inconsistent with its purpose of returning snapshots for a specific product. Consider adding a `product_id` parameter to `poll_all()` or documenting that it returns all snapshots regardless of product.
- `price_tracker.py`: `get_current_price()` re-polls all sources on every call (line 73-87). This is fine for Phase 1 but will be inefficient at scale — caching or incremental updates would be needed for production.
- `models.py`: `CompetitorPrice.last_updated` uses `field(default_factory=datetime.now)` which captures the time at object construction. This is correct but worth noting that the timestamp is set at creation, not at fetch time.
- `mock_sources.py`: `MockCSVSource` mutates `self.csv_data` when no data is provided (line 68-69), which is a side effect. Consider using a separate internal default instead.
- `test_models.py`: Test (16) `test_get_current_price_returns_latest_snapshot` contains verbose inline comments explaining the workaround for `poll_all()`'s empty `product_id`. These comments could be removed or moved to docstrings.
- Type hints: `price_tracker.py` uses `list` (lowercase) in `__init__` but `List` (uppercase) in method signatures. Consider using `list` consistently (Python 3.9+ supports lowercase generics).
- No docstring on `PriceTracker.__init__` — minor, since the class docstring covers it.

## Reusable Components
- **PricingConfig** (`dynamic_pricing/config.py`): A clean, general-purpose dataclass configuration pattern with `field(default_factory=list)` for mutable defaults and constant-based defaults. Useful for any Python project needing typed configuration with sensible defaults.
- **MockCSVSource** (`dynamic_pricing/mock_sources.py`): The CSV parsing logic in `MockCSVSource.fetch_prices()` is a self-contained, general-purpose CSV-to-objects parser with header detection, whitespace handling, and error recovery. Could be extracted as a utility for any project needing lightweight CSV parsing.

## Verdict
PASS — All 32 tests pass, no blocking bugs found. Code meets all Phase 1 spec requirements.
