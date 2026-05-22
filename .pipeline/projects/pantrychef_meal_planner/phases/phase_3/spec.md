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
    i