# Phase 1 Tasks

- [ ] Task 1: Create package structure and entry point
  - What: Set up the Python package layout with pyproject.toml, __init__.py, and top-level exports so the project is importable as `dropgentic`
  - Files: pyproject.toml, src/dropgentic/__init__.py, src/dropgentic/cli.py
  - Done when: `pip install -e .` succeeds and `import dropgentic` works without errors

- [ ] Task 2: Build core data models
  - What: Implement the domain models — Product, Supplier, Order, and MarginCalculator — with basic validation and serialization
  - Files: src/dropgentic/models/product.py, src/dropgentic/models/supplier.py, src/dropgentic/models/order.py, src/dropgentic/models/margin.py, src/dropgentic/models/__init__.py
  - Done when: All models can be instantiated, validated, and serialized to/from dicts; margin calculations produce correct results

- [ ] Task 3: Implement the agent planner engine
  - What: Build the core decision-making logic — product sourcing agent that evaluates products against suppliers, ranks by profit margin, and generates a recommended action plan
  - Files: src/dropgentic/planner/engine.py, src/dropgentic/planner/__init__.py
  - Done when: Given a list of products and suppliers, the planner returns a ranked recommendation list with margin scores and actionable output

- [ ] Task 4: Add configuration and settings module
  - What: Create a config system for project settings (default margins, supplier filters, currency, etc.) with file-based loading (YAML or JSON)
  - Files: src/dropgentic/config/settings.py, src/dropgentic/config/__init__.py, config/default.yaml
  - Done when: Settings load from default config file and can be overridden programmatically; all planner components respect config values

- [ ] Task 5: Build CLI interface
  - What: Implement a CLI entry point that lets users run the planner — list products, evaluate suppliers, and generate a sourcing plan
  - Files: src/dropgentic/cli.py (updated), src/dropgentic/commands/plan.py, src/dropgentic/commands/__init__.py
  - Done when: Running `dropgentic plan` from the command line produces a formatted sourcing recommendation using the planner engine