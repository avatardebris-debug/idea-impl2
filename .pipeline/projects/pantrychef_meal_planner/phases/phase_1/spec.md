## Phase 1 — MVP: Pantry Ingestion + Recipe Matching + Basic Meal Plan

**Goal:** A user can add pantry items, define or load recipes, and get a simple meal plan showing which recipes can be made from what's on hand.

### Description

Build the foundational data layer and the core matching engine. The user can:
1. Add/remove pantry items (name, quantity, unit, category).
2. Add recipes with ingredients and basic metadata.
3. Query the system: *"What can I cook right now?"* — returns recipes where all (or most) ingredients are in the pantry.
4. Generate a basic 1-day meal plan from matched recipes.

### Deliverable

- **`pantrychef-core`** Python package (or equivalent) with:
  - `PantryManager` — CRUD for pantry items, persisted to SQLite.
  - `RecipeStore` — CRUD for recipes, persisted to SQLite.
  - `RecipeMatcher` — Scored ingredient overlap algorithm; returns ranked list of cookable recipes.
  - `BasicMealPlanner` — Picks top-scoring recipes into a single-day plan.
  - CLI entry point: `pantrychef add-pantry-item`, `pantrychef add-recipe`, `pantrychef plan`
- SQLite database schema (migrations or schema-on-first-write).
- Unit tests for `RecipeMatcher` (≥ 80% branch coverage).

### Dependencies

- None (this is the foundation).

### Success Criteria

| # | Criterion |
|---|---|
| 1 | User can add ≥ 20 pantry items and ≥ 5 recipes via CLI. |
| 2 | `RecipeMatcher` correctly identifies recipes where ≥ 80% of ingredients are in the pantry. |
| 3 | `pantrychef plan` outputs a valid 1-day meal plan (breakfast, lunch, dinner) from available recipes. |
| 4 | All core classes have unit tests; CI passes. |

---