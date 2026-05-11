# PantryChef Meal Planner — Master Implementation Plan

> **Core Deliverable:** A meal planning tool that ingests pantry inventory, suggests recipes based on available ingredients, generates shopping lists for missing items, and tracks nutritional macros — all tied together in a coherent meal-planning workflow.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    PantryChef Core                       │
├──────────┬──────────┬──────────────┬───────────────────┤
│ Pantry   │ Recipe   │ MealPlan     │ ShoppingList       │
│ Engine   │ Engine   │ Engine       │ Generator          │
├──────────┴──────────┴──────────────┴───────────────────┤
│              NutritionTracker                           │
├─────────────────────────────────────────────────────────┤
│              Data Layer (SQLite / JSON)                 │
├─────────────────────────────────────────────────────────┤
│              CLI / Web UI Layer                         │
└─────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| SQLite as primary store | ACID guarantees, zero config, queryable for recipe matching |
| Recipe matching via ingredient overlap scoring | Simple, effective, extensible to weighted scoring later |
| Modular engine architecture | Each domain (pantry, recipe, nutrition, shopping) is independently testable |
| CLI-first, web-optional | Lowest barrier to entry; web can be layered on top later |

### Data Model (Core Entities)

- **PantryItem**: `id, name, quantity, unit, category, expiry_date`
- **Recipe**: `id, name, ingredients[], steps[], servings, prep_time, nutrition[]`
- **MealPlan**: `id, date, meal_type, recipe_id, servings, notes`
- **ShoppingItem**: `id, name, quantity, unit, source_recipe_ids[]`
- **NutritionalInfo**: `calories, protein, carbs, fat, fiber, per_serving`

---

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

## Phase 3 — Meal Planning Polish + Export + UI

**Goal:** Make the tool genuinely useful for ongoing meal planning with scheduling, dietary preferences, and exportable outputs.

### Description

Add the finishing layer that turns a prototype into a practical tool:
1. **Multi-Day Meal Planner** — Generate 7-day meal plans with constraints (e.g., "max 500 cal lunch," "vegetarian," "no nuts").
2. **Dietary Preference Filters** — Tag recipes with dietary labels (vegan, gluten-free, keto, etc.) and filter meal plans accordingly.
3. **Export** — Export meal plans and shopping lists to CSV/Markdown for printing or sharing.
4. **Web UI (optional but recommended)** — Simple Flask/FastAPI frontend with recipe browser, pantry dashboard, and meal plan calendar view.

### Deliverable

- **`AdvancedMealPlanner`** service:
  - Constraint-based meal plan generation (calorie caps, dietary tags).
  - Weekly rotation to avoid recipe repetition.
  - CLI: `pantrychef plan-week --days 7 --diet vegetarian --max-lunch-cal 500`
- **`PreferenceFilter`** service — tags and filters recipes by dietary category.
- **`Exporter`** — CSV and Markdown output for meal plans and shopping lists.
- **Web UI** (FastAPI + HTMX or React):
  - Pantry inventory dashboard.
  - Recipe browser with ingredient search.
  - Meal plan calendar view.
  - Shopping list export button.
- End-to-end integration tests covering the full workflow (add pantry → add recipes → plan week → export).

### Dependencies

- Phase 1 and Phase 2 services must be stable and tested.

### Success Criteria

| # | Criterion |
|---|---|
| 1 | 7-day meal plan generated with dietary constraints respected (zero violations). |
| 2 | Exported CSV/Markdown is well-formatted and opens correctly in standard tools. |
| 3 | Web UI renders pantry, recipes, and meal plan views without errors. |
| 4 | End-to-end workflow test passes: pantry → recipes → plan → export. |

---

## Architecture Notes

### Technology Stack Recommendation

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Database | SQLite (via `sqlite3` stdlib or `SQLAlchemy` ORM) |
| CLI Framework | `click` or `argparse` |
| Web UI (Phase 3) | FastAPI + Jinja2/HTMX (or React if SPA desired) |
| Testing | `pytest` + `pytest-cov` |
| Serialization | `pydantic` for data models |
| Recipe Matching | Custom scoring algorithm (Jaccard similarity on ingredient sets, weighted by quantity) |

### Recipe Matching Algorithm (Phase 1)

```
score(recipe, pantry) = Σ ingredient_overlap(recipe, pantry) / total_ingredients(recipe)

Where ingredient_overlap = 1 if pantry has ≥ required quantity, else 0

Threshold for "cookable": score ≥ 0.8
Threshold for "mostly cookable": score ≥ 0.6
```

### Database Schema (SQLite)

```sql
CREATE TABLE pantry_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    category TEXT,
    expiry_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    servings INTEGER DEFAULT 1,
    prep_time_minutes INTEGER,
    dietary_tags TEXT,  -- JSON array: ["vegan", "gluten-free"]
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recipe_ingredients (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    ingredient_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    nutrition_calories REAL,
    nutrition_protein REAL,
    nutrition_carbs REAL,
    nutrition_fat REAL,
    nutrition_fiber REAL
);

CREATE TABLE meal_plans (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    meal_type TEXT NOT NULL,  -- breakfast, lunch, dinner, snack
    recipe_id INTEGER REFERENCES recipes(id),
    servings REAL DEFAULT 1,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shopping_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    aisle_category TEXT,
    source_recipe_ids TEXT,  -- JSON array of recipe IDs
    meal_plan_id INTEGER REFERENCES meal_plans(id)
);
```

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **Recipe data is hard to populate** | High | Start with a bundled dataset of 20-50 recipes; add import from CSV/JSON in Phase 3. |
| **Ingredient matching is noisy** (e.g., "1 onion" vs "1 medium onion") | Medium | Phase 1 uses exact name matching; Phase 3 adds synonym mapping (e.g., "tomato" ↔ "tomatoes"). |
| **Nutrition data accuracy** | Medium | Use USDA FoodData Central API or a local nutrition database; flag data as approximate. |
| **SQLite concurrency limits** | Low | Single-user tool; if multi-user needed later, swap to PostgreSQL. |
| **Scope creep on web UI** | Medium | Keep web UI minimal in Phase 3; prioritize CLI correctness first. |
| **User expectations for "smart" suggestions** | Medium | Be clear in MVP that suggestions are rule-based; "AI-powered" features can be Phase 4+. |

---

## Summary

| Phase | Scope | Key Output |
|---|---|---|
| **1 — MVP** | Pantry + recipes + matching + 1-day plan | Working CLI with core matching engine |
| **2 — Shopping + Nutrition** | Shopping lists + macro tracking | Actionable shopping lists + nutrition data |
| **3 — Polish + Export + UI** | Multi-day plans + dietary filters + export + web UI | Complete, user-friendly meal planning tool |

**Total estimated complexity:** Medium. Phase 1 is the critical path — if the matching engine works well, the rest flows naturally.
