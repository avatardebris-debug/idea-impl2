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
