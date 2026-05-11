## Phase 1 — MVP: Core Data Model & Price Tracker

### Description
Build the foundational data models for products and competitor prices, and implement a price tracking engine that can poll multiple sources (APIs or CSV imports) and store price snapshots. This is the smallest useful deliverable: a working price tracker that produces price data the downstream system can consume.

### Deliverable
- `dynamic_pricing/models.py` — `Product`, `CompetitorPrice`, `PriceSnapshot` dataclasses.
- `dynamic_pricing/price_tracker.py` — `PriceTracker` class with:
  - `add_source()` / `remove_source()` for competitor data sources.
  - `poll_all()` → list of `PriceSnapshot` objects.
  - `get_current_price(product_id)` → latest snapshot.
- `dynamic_pricing/config.py` — `PricingConfig` dataclass (polling interval, margin floor, competitor sources list).
- `dynamic_pricing/constants.py` — defaults for polling, currency, margin floors.
- `dynamic_pricing/__init__.py` — public API exports.
- Unit tests for models and tracker with mock data sources.

### Dependencies
- None (pure Python, no external APIs required for MVP — mock sources suffice).

### Success Criteria
- [ ] `PriceTracker` can ingest prices from at least 2 mock sources simultaneously.
- [ ] `poll_all()` returns a `PriceSnapshot` list with correct product_id, competitor, price, timestamp.
- [ ] `get_current_price()` returns the latest snapshot for a given product.
- [ ] `PricingConfig` allows configuration of polling interval and margin floor.
- [ ] All unit tests pass (≥ 15 test cases).
- [ ] No breaking changes to existing `youtube_studio` package.

---