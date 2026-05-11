# Phase 1 Tasks

- [x] Task 1: Create package scaffolding and constants
  - What: Create the `dynamic_pricing/` package directory structure with `__init__.py`, `constants.py` (polling interval, currency, margin floor defaults), and `config.py` (`PricingConfig` dataclass with polling_interval, margin_floor, competitor_sources).
  - Files: `dynamic_pricing/__init__.py`, `dynamic_pricing/constants.py`, `dynamic_pricing/config.py`
  - Done when: Package imports cleanly (`from dynamic_pricing import constants, config`), `PricingConfig` dataclass has `polling_interval` (int, default 900), `margin_floor` (float, default 0.15), `competitor_sources` (list, default empty), and `constants` exposes `DEFAULT_POLLING_INTERVAL=900`, `DEFAULT_CURRENCY="USD"`, `DEFAULT_MARGIN_FLOOR=0.15`.

- [x] Task 2: Implement core data models
  - What: Create `models.py` with `Product`, `CompetitorPrice`, and `PriceSnapshot` dataclasses. `Product` has id, name, base_price, currency, category. `CompetitorPrice` has product_id, competitor_name, price, last_updated. `PriceSnapshot` has product_id, competitor, price, timestamp, source.
  - Files: `dynamic_pricing/models.py`
  - Done when: All three dataclasses are importable, `PriceSnapshot` fields include product_id, competitor, price, timestamp, source; `Product` fields include id, name, base_price, currency, category; `CompetitorPrice` fields include product_id, competitor_name, price, last_updated.

- [x] Task 3: Implement mock data sources
  - What: Create a `mock_sources.py` module with two mock competitor sources (`MockAPISource` and `MockCSVSource`) that implement a `fetch_prices(product_id) -> list[CompetitorPrice]` interface. `MockAPISource` returns hardcoded prices; `MockCSVSource` parses inline CSV strings into `CompetitorPrice` objects.
  - Files: `dynamic_pricing/mock_sources.py`
  - Done when: Both mock sources return at least 2 `CompetitorPrice` entries for any given product_id, with different competitor names and prices.

- [x] Task 4: Implement the PriceTracker engine
  - What: Create `price_tracker.py` with `PriceTracker` class that manages a list of data sources, supports `add_source(source)` / `remove_source(source)`, has `poll_all() -> list[PriceSnapshot]` that iterates all sources and converts `CompetitorPrice` to `PriceSnapshot` with current timestamp, and `get_current_price(product_id) -> PriceSnapshot | None` that returns the latest snapshot for a product.
  - Files: `dynamic_pricing/price_tracker.py`
  - Done when: `add_source`/`remove_source` correctly manage the internal source list, `poll_all()` returns `PriceSnapshot` objects with correct product_id, competitor, price, timestamp, source fields, `get_current_price()` returns the most recent snapshot for a given product_id (or None if no data exists).

- [x] Task 5: Wire up public API exports
  - What: Update `__init__.py` to export all public classes: `Product`, `CompetitorPrice`, `PriceSnapshot`, `PricingConfig`, `PriceTracker`, and mock sources.
  - Files: `dynamic_pricing/__init__.py`
  - Done when: `from dynamic_pricing import Product, CompetitorPrice, PriceSnapshot, PricingConfig, PriceTracker` works without errors.

- [x] Task 6: Write unit tests (≥ 15 test cases)
  - What: Create `tests/test_models.py` and `tests/test_price_tracker.py` covering all success criteria: model field validation, mock source behavior, tracker source management, poll_all correctness, get_current_price correctness, PricingConfig defaults and overrides.
  - Files: `dynamic_pricing/tests/test_models.py`, `dynamic_pricing/tests/test_price_tracker.py`
  - Done when: ≥ 15 test cases all pass, covering: (1) Product dataclass creation, (2) Product default currency, (3) CompetitorPrice dataclass creation, (4) PriceSnapshot dataclass creation, (5) PriceSnapshot timestamp is datetime, (6) PricingConfig default polling_interval, (7) PricingConfig default margin_floor, (8) PricingConfig custom values, (9) MockAPISource returns prices, (10) MockCSVSource returns prices, (11) Mock sources return different competitors, (12) PriceTracker add_source, (13) PriceTracker remove_source, (14) poll_all returns snapshots with correct fields, (15) poll_all from 2+ sources simultaneously, (16) get_current_price returns latest snapshot, (17) get_current_price returns None for unknown product.