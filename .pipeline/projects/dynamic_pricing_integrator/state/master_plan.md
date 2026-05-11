# Dynamic Pricing Integrator — Master Implementation Plan

> **Idea:** Add competitive price tracking and automated discount rule engines to the e-commerce SEO tool for real-time inventory and margin optimization.
>
> **Context:** The existing codebase is a YouTube Studio SEO toolkit (`youtube_studio/`) with modular generators for titles, keywords, descriptions, thumbnails, and transcripts. This plan extends the architecture to support e-commerce product pricing, competitor price monitoring, and automated discount rule execution — all while remaining compatible with the existing SEO metadata pipeline.

---

## Architecture Notes

### Current Architecture Summary
- **`youtube_studio/`** — Core package with `YouTubeStudio` as the main orchestrator.
- **Modular generators** — `TitleGenerator`, `KeywordGenerator`, `DescriptionBuilder`, `ThumbnailGenerator`, `TranscriptBuilder`.
- **`config.py`** — Singleton-based `StudioConfig` with nested `TitleConfig`, `ThumbnailConfig`, `KeywordConfig`, `ExportConfig`.
- **`seo_optimizer.py`** — A parallel `SEOOptimizer` class that coordinates generators and exports metadata as JSON/CSV.
- **`constants.py`** — Global defaults for lengths, counts, and formats.

### Target Architecture
The Dynamic Pricing Integrator adds a new top-level package `dynamic_pricing/` alongside `youtube_studio/`, with these submodules:

```
dynamic_pricing/
├── __init__.py
├── models.py              # Product, CompetitorPrice, DiscountRule, PriceSnapshot
├── price_tracker.py       # Competitor price scraping & polling engine
├── discount_engine.py     # Rule-based discount calculation engine
├── margin_optimizer.py    # Margin-aware pricing recommendations
├── integrator.py          # Bridges pricing data into SEO metadata pipeline
├── config.py              # Pricing-specific configuration
├── constants.py           # Pricing defaults & thresholds
└── exporters/
    ├── json_exporter.py
    └── csv_exporter.py
```

### Integration Points
1. **`SEOOptimizer`** gains a `pricing_data` parameter — product price, competitor prices, and active discounts are appended to the `VideoMetadata`-equivalent `ProductMetadata` dataclass.
2. **`StudioConfig`** extends with `PricingConfig` (polling interval, margin targets, competitor sources).
3. **`YouTubeStudio`** gets a `generate_product_metadata()` method that calls both SEO generators and pricing optimizers.

### Data Flow
```
Competitor Sources (APIs / Scrapers)
        ↓
   PriceTracker (polling → PriceSnapshot)
        ↓
  DiscountEngine (rules → DiscountResult)
        ↓
MarginOptimizer (margin targets → RecommendedPrice)
        ↓
  Integrator (merges into ProductMetadata)
        ↓
  Export (JSON/CSV → downstream SEO pipeline)
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Competitor price APIs have rate limits or paywalls | Blocks Phase 1 data ingestion | Build mock data source first; use `requests` with retry/backoff; support CSV import fallback |
| Scraping legal/ToS issues | Legal exposure | Prioritize official APIs (Shopify, Amazon PA-API, PriceAPI); add `robots.txt` compliance check |
| Discount rules conflict with SEO metadata constraints | Incorrect pricing in SEO output | Add validation layer in `Integrator`; unit-test rule combinations |
| Margin optimization produces unrealistic prices | Revenue loss | Cap discounts at configurable floor price; add human-in-the-loop approval gate |
| Tight coupling to existing `youtube_studio` package | Breaks SEO functionality | Keep `dynamic_pricing/` as a separate package; bridge via `ProductMetadata` dataclass only |
| Real-time polling overhead | Server load | Default polling interval = 15 min; make configurable; add caching layer |

---

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

## Phase 2 — Discount Rule Engine

### Description
Implement a rule-based discount calculation engine that evaluates pricing conditions (competitor price gaps, inventory age, margin targets) and produces actionable discount recommendations. This phase adds the "automated discount" capability.

### Deliverable
- `dynamic_pricing/discount_engine.py` — `DiscountEngine` class with:
  - `add_rule(rule: DiscountRule)` — register rules (e.g., "if competitor is 10% lower, discount 5%").
  - `evaluate(product_id) → DiscountResult` — returns discount percentage, reason, and effective price.
  - Built-in rule types: `PriceGapRule`, `InventoryAgeRule`, `MarginFloorRule`, `CompetitorMatchRule`.
- `dynamic_pricing/margin_optimizer.py` — `MarginOptimizer` class:
  - `calculate_optimal_price(product_id) → RecommendedPrice` — suggests price to hit target margin.
  - `check_margin(product_id) → MarginStatus` — current vs. target margin.
- `dynamic_pricing/models.py` (extended) — `DiscountRule`, `DiscountResult`, `RecommendedPrice`, `MarginStatus` dataclasses.
- Unit tests for all rule types and margin calculations.

### Dependencies
- **Phase 1** must be complete (price tracker provides the input data).
- `dynamic_pricing/models.py` from Phase 1.

### Success Criteria
- [ ] `DiscountEngine` evaluates ≥ 4 rule types correctly.
- [ ] `evaluate()` returns a `DiscountResult` with discount %, effective price, and rule reason.
- [ ] `MarginOptimizer` correctly calculates margin percentages and recommends prices within configurable floor/ceiling bounds.
- [ ] Rules can be combined (e.g., PriceGap + MarginFloor) with last-rule-wins and weighted-average strategies.
- [ ] All unit tests pass (≥ 25 new test cases, total ≥ 40).
- [ ] No breaking changes to existing `youtube_studio` package.

---

## Phase 3 — Integrator & Real-Time Optimization

### Description
Bridge the pricing system into the existing SEO metadata pipeline. Create the `Integrator` that merges pricing data with SEO outputs, add real-time price refresh capability, and expose a unified `ProductMetadata` export that combines competitive pricing insights with SEO recommendations.

### Deliverable
- `dynamic_pricing/integrator.py` — `PricingIntegrator` class:
  - `merge_with_seo(seo_metadata, product_id) → ProductMetadata` — combines SEO data with pricing data.
  - `get_pricing_insights(product_id) → dict` — competitive position, recommended action, margin status.
- `dynamic_pricing/config.py` (extended) — `PricingConfig` gains `real_time_polling` (bool), `seo_integration` (bool), `approval_required` (bool).
- `dynamic_pricing/exporters/` — JSON and CSV exporters for `ProductMetadata`.
- `youtube_studio/youtube_studio.py` (extended) — `YouTubeStudio.generate_product_metadata()` method.
- `youtube_studio/seo_optimizer.py` (extended) — `SEOOptimizer` gains `pricing_data` parameter.
- Integration tests verifying end-to-end flow: price poll → discount → margin → SEO merge → export.

### Dependencies
- **Phase 1** (price tracker data).
- **Phase 2** (discount engine + margin optimizer).
- Existing `youtube_studio` package (read-only integration, no breaking changes).

### Success Criteria
- [ ] `PricingIntegrator.merge_with_seo()` produces a `ProductMetadata` with both SEO and pricing fields.
- [ ] `get_pricing_insights()` returns competitive position (e.g., "12% below market"), recommended discount, and margin status.
- [ ] `YouTubeStudio.generate_product_metadata()` works end-to-end with pricing enabled.
- [ ] Real-time polling refreshes prices within configured interval (default 15 min).
- [ ] Exporters produce valid JSON and CSV with all pricing + SEO fields.
- [ ] Approval gate (`approval_required=True`) blocks auto-discount application until confirmed.
- [ ] All integration tests pass (≥ 10 new test cases, total ≥ 50).
- [ ] Zero regressions in existing `youtube_studio` test suite.

---

## File Structure (Final)

```
dynamic_pricing/
├── __init__.py
├── models.py
├── price_tracker.py
├── discount_engine.py
├── margin_optimizer.py
├── integrator.py
├── config.py
├── constants.py
├── exporters/
│   ├── __init__.py
│   ├── json_exporter.py
│   └── csv_exporter.py
└── tests/
    ├── test_models.py
    ├── test_price_tracker.py
    ├── test_discount_engine.py
    ├── test_margin_optimizer.py
    └── test_integrator.py

youtube_studio/
├── youtube_studio.py      ← extended (generate_product_metadata)
├── seo_optimizer.py       ← extended (pricing_data parameter)
├── config.py              ← extended (PricingConfig)
└── constants.py           ← extended (pricing defaults)
```

---

## Summary

| Phase | Scope | Key Deliverable | Est. Effort |
|-------|-------|-----------------|-------------|
| **1 — MVP** | Data models + price tracker | `PriceTracker` with mock sources | Small |
| **2 — Rules** | Discount engine + margin optimizer | `DiscountEngine` + `MarginOptimizer` | Medium |
| **3 — Integration** | SEO bridge + real-time + exporters | `PricingIntegrator` + unified exports | Medium |

Total: **3 phases**, each independently testable, with Phase 1 shipping a working price tracker and Phase 3 delivering the full integrated system.
