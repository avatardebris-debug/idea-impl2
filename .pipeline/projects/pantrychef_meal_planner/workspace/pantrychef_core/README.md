# PantryChef Core

Core engine for the PantryChef Meal Planner.

## Features

- Pantry inventory management (add, remove, list items)
- Recipe storage with ingredient tracking
- Scored recipe matching against pantry inventory
- Basic meal planning (breakfast, lunch, dinner)
- **Multi-day meal planning** (7-day plans with dietary constraints)
- **Dietary preference filters** (vegan, vegetarian, keto, gluten-free, etc.)
- **Export** meal plans to CSV or Markdown
- **Web UI** (FastAPI backend)
- **Shopping list generation** for missing ingredients
- **Nutrition tracking** with macro summaries
- CLI interface

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Add a pantry item
pantrychef add-pantry-item --name "Eggs" --quantity 12 --unit "pieces" --category "dairy"

# Add a recipe
pantrychef add-recipe --name "Scrambled Eggs" --servings 2 --prep-time 10 \
  --ingredients "eggs:3:pieces,butter:1:tbsp,milk:2:tbsp"

# Generate a basic meal plan
pantrychef plan

# Generate a 7-day advanced meal plan with dietary constraints
pantrychef advanced-plan --days 7 --dietary-tag vegetarian

# Filter recipes by dietary preference
pantrychef dietary-filter --tag vegan

# Export meal plan to CSV
pantrychef export --format csv

# Export meal plan to Markdown
pantrychef export --format markdown --output meal_plan.md
```
