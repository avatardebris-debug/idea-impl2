# Phase 1 Tasks

- [x] Task 1: Project scaffolding
  - What: Create the Python package structure with __init__.py, setup.py, and top-level package layout
  - Files: ffo/__init__.py, ffo/pyproject.toml, ffo/
  - Done when: Package is importable via `import ffo` and `from ffo import` works for submodules

- [x] Task 2: Player model and data structures
  - What: Define Player dataclass with attributes (name, position, overall_rating, age, contract_length, salary, value) and a FreeAgent subclass with availability status
  - Files: ffo/models/player.py
  - Done when: Player and FreeAgent classes can be instantiated, serialized to/from dict, and compared by value/salary ratio

- [x] Task 3: Salary cap and financial constraints engine
  - What: Implement SalaryCap class that tracks total payroll, enforces cap limits, and calculates remaining budget given roster additions/subtractions
  - Files: ffo/models/salary_cap.py
  - Done when: Can create a cap with a limit, add/remove players, and get accurate remaining budget; enforces cap violations

- [x] Task 4: Player valuation model
  - What: Implement a valuation function that computes a player's financial value (e.g., value-per-dollar = rating / salary, adjusted for age and contract length) and ranks players by efficiency
  - Files: ffo/models/valuation.py
  - Done when: Can value any Player/FreeAgent instance, rank a list by value efficiency, and produce a numeric score reflecting cost-effectiveness

- [x] Task 5: Free agent pool manager
  - What: Build a FreeAgentPool class that holds a collection of available free agents, supports filtering by position/rating range, and allows querying the top N candidates within a budget
  - Files: ffo/models/free_agent_pool.py
  - Done when: Can load a pool of agents, filter by position and rating, and retrieve top candidates sorted by valuation within a given budget

- [x] Task 6: Core optimizer and integration entry point
  - What: Implement the main optimize_roster function that takes a current roster, salary cap, and free agent pool, then returns an optimized roster by adding/subtracting players to maximize total team value within cap constraints
  - Files: ffo/optimizer.py, ffo/__init__.py (export)
  - Done when: Calling ffo.optimize_roster(roster, cap, pool) returns a valid optimized roster within cap; all core features are importable from the top-level ffo package