# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and package structure
  - What: Create the Python package layout with __init__.py, core modules, and a top-level entry point so the project is importable.
  - Files: dfs_arb/__init__.py, dfs_arb/core/__init__.py, dfs_arb/core/models.py, dfs_arb/core/engine.py, setup.py
  - Done when: `import dfs_arb` succeeds with no errors; package has a valid __version__ and exposes a top-level API.

- [ ] Task 2: Data models for DFS lines and markets
  - What: Define Pydantic dataclasses for player props, team lines, odds formats (American/decimal/fractional), and market metadata.
  - Files: dfs_arb/core/models.py (extended)
  - Done when: Models can be instantiated from dicts, serialize to dicts, and validate odds formats correctly.

- [ ] Task 3: Odds conversion and normalization engine
  - What: Build functions to convert between American, decimal, and fractional odds; compute implied probabilities; and normalize all inputs to a common format.
  - Files: dfs_arb/core/odds.py (new)
  - Done when: Converting odds in both directions is lossless for standard values; implied probabilities sum to ≤ 100% for single-outcome lines.

- [ ] Task 4: Arbitrage detection engine
  - What: Implement the core algorithm that compares odds across multiple bookmakers/markets to find arbitrage opportunities (positive expected value situations).
  - Files: dfs_arb/core/arbitrage.py (new)
  - Done when: Given a list of odds from different books for the same market, the engine correctly identifies arbitrageable lines and computes the optimal stake distribution and guaranteed profit percentage.

- [ ] Task 5: Promo/bonus hunting module
  - What: Build a module that tracks and evaluates sign-up bonuses, deposit matches, and risk-free bet promos to calculate their expected value given current market conditions.
  - Files: dfs_arb/core/promos.py (new)
  - Done when: Given a promo offer and current odds, the module returns the expected value and whether the promo is profitable to exploit.

- [ ] Task 6: Integration entry point and example usage
  - What: Create a main CLI/demo script that ties all modules together — loads sample data, runs arbitrage detection, checks promos, and prints results.
  - Files: dfs_arb/cli.py (new), dfs_arb/data/sample_lines.json (new)
  - Done when: Running `python -m dfs_arb.cli` produces output showing detected arbitrage opportunities and promo evaluations with no errors.