# PantryChef Core

Core engine for the PantryChef Meal Planner.

## Features

- Pantry inventory management (add, remove, list items)
- Recipe storage with ingredient tracking
- Scored recipe matching against pantry inventory
- Basic meal planning (breakfast, lunch, dinner)
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

# Generate a meal plan
pantrychef plan
```
