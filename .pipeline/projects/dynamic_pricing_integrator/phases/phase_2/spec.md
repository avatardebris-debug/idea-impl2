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

