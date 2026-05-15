# Phase 2 Tasks

- [x] Task 1: Extend models.py with new dataclasses
  - What: Add `DiscountRule`, `DiscountResult`, `RecommendedPrice`, and `MarginStatus` dataclasses to `dynamic_pricing/models.py`. `DiscountRule` holds rule type, parameters (e.g., gap_threshold, discount_pct, inventory_days), and strategy. `DiscountResult` holds discount_pct, effective_price, and reason. `RecommendedPrice` holds product_id, recommended_price, target_margin, and floor/ceiling bounds. `MarginStatus` holds current_margin, target_margin, and status enum (below/within/above).
  - Files: `dynamic_pricing/models.py` (append), `dynamic_pricing/constants.py` (add pricing strategy constants)
  - Done when: All four new dataclasses are importable from `dynamic_pricing.models`, fields match spec, and `DiscountRule` supports at least the four rule types (PriceGap, InventoryAge, MarginFloor, CompetitorMatch) via a type field or subclass pattern.

- [x] Task 2: Implement DiscountEngine with four rule types
  - What: Create `dynamic_pricing/discount_engine.py` with `DiscountEngine` class. It must support `add_rule(rule)` to register rules, `evaluate(product_id) -> DiscountResult` that applies registered rules in order, and two combination strategies: `last_rule_wins` (default) and `weighted_average`. Implement four built-in rule classes: `PriceGapRule` (triggers when competitor price is below base by a threshold), `InventoryAgeRule` (triggers when product has been in inventory longer than a threshold), `MarginFloorRule` (triggers when current margin drops below floor), and `CompetitorMatchRule` (triggers to match the lowest competitor price). Each rule's `apply(product, snapshots) -> DiscountResult` returns a discount percentage, effective price, and human-readable reason.
  - Files: `dynamic_pricing/discount_engine.py` (new), `dynamic_pricing/models.py` (import new dataclasses)
  - Done when: `DiscountEngine` can add and evaluate all four rule types, `evaluate()` returns a `DiscountResult` with discount_pct, effective_price, and reason, and both `last_rule_wins` and `weighted_average` strategies produce correct results when multiple rules are registered.

- [x] Task 3: Implement MarginOptimizer
  - What: Create `dynamic_pricing/margin_optimizer.py` with `MarginOptimizer` class. It must have `calculate_optimal_price(product_id) -> RecommendedPrice` that computes the price needed to hit the target margin given cost and competitor data, and `check_margin(product_id) -> MarginStatus` that returns current margin vs target. The optimizer should use `PricingConfig.margin_floor` as the default floor and support configurable ceiling bounds. It should integrate with `PriceTracker` to fetch competitor snapshots for margin-aware recommendations.
  - Files: `dynamic_pricing/margin_optimizer.py` (new), `dynamic_pricing/config.py` (ensure margin_floor is accessible)
  - Done when: `MarginOptimizer.calculate_optimal_price()` returns a `RecommendedPrice` within floor/ceiling bounds, `check_margin()` returns accurate `MarginStatus` with correct margin percentage, and the optimizer correctly uses `PriceTracker` data when available.

- [x] Task 4: Update package exports and write unit tests
  - What: Update `dynamic_pricing/__init__.py` to export all new classes (`DiscountEngine`, `PriceGapRule`, `InventoryAgeRule`, `MarginFloorRule`, `CompetitorMatchRule`, `MarginOptimizer`, and the new dataclasses). Create `tests/test_discount_engine.py` and `tests/test_margin_optimizer.py` with comprehensive test coverage. Tests must cover: each of the 4 rule types individually, rule combination with both strategies, edge cases (no rules registered, no competitor data, zero margin), MarginOptimizer floor/ceiling enforcement, and integration between DiscountEngine and MarginOptimizer.
  - Files: `dynamic_pricing/__init__.py` (update exports), `tests/test_discount_engine.py` (new), `tests/test_margin_optimizer.py` (new)
  - Done when: All new classes are importable from `dynamic_pricing`, ≥ 25 new test cases exist across the two test files, and total test count across all test files is ≥ 40.

- [x] Task 5: Validate tests pass and verify no breaking changes
  - What: Run the full pytest suite to confirm all tests pass. Verify that existing `youtube_studio` package (if present) is unaffected. Check that all new imports work correctly and that the existing Phase 1 tests still pass.
  - Files: Run `pytest` on the workspace
  - Done when: All tests (≥ 40 total) pass with zero failures, no import errors, and no changes to existing `youtube_studio` package files.