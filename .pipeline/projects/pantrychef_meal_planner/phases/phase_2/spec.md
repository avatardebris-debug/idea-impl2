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
