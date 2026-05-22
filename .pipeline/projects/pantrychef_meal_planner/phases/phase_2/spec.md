## Phase 2 — Shopping Lists + Nutritional Tracking

**Goal:** Extend the MVP so users can see what they're missing (shopping list) and understand the nutritional impact of their meal plans.

### Description

Add two critical real-world features:
1. **Shopping List Generator** — Given a meal plan, compute the delta between pantry inventory and recipe ingredient requirements. Output a deduplicated, grouped shopping list.
2. **Nutrition Tracker** — For each recipe and meal plan, aggregate nutritional macros (calories, protein, carbs, fat, fiber). Allow the user to query daily/weekly macro totals.

### Deliverable

- **`ShoppingListGenerator`** service:
  - Computes ingredient deltas per recipe.
  - Deduplicates across recipes (e.g., "2 eggs" + "3 eggs" → "5 eggs").
  - Groups items by store aisle category (produce, dairy, pantry, etc.).
  - CLI: `pantrychef shopping-list --date 2025-01-15`
- **`NutritionTracker`** service:
  - Stores nutrition data per recipe ingredient.
  - Aggregates per-meal and per-day totals.
  - CLI: `pantrychef nutrition --date 2025-01-15`
- Updated `RecipeStore` to accept nutrition metadata.
- Integration tests for shopping list deduplication and nutrition aggregation.

### Dependencies

- Phase 1 (`PantryManager`, `RecipeStore`, `RecipeMatcher`, `BasicMealPlanner`) must be stable.

### Success Criteria

| # | Criterion |
|---|---|
| 1 | Shopping list correctly identifies missing ingredients for a 3-recipe meal plan. |
| 2 | Duplicate ingredients across recipes are properly summed (e.g., 2× "1 cup flour" → "2 cups flour"). |
| 3 | Nutrition tracker reports accurate daily macro totals for a meal plan. |
| 4 | Shopping list grouped by category is readable and actionable. |

---

