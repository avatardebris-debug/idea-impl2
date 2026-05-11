# Phase 2 Tasks

- [ ] Task 1: Add input validation and custom exceptions
  - What: Create a custom exceptions module and add input validation across the codebase. Add validation in `run_simulation`, `GBM`, `MarketSimulator`, `PortfolioSimulator`, and model constructors.
  - Files: Create `financial_portfolio_simulator/exceptions.py`, modify `financial_portfolio_simulator/api.py`, `financial_portfolio_simulator/simulators/gbm.py`, `financial_portfolio_simulator/simulators/market_simulator.py`, `financial_portfolio_simulator/simulators/portfolio_simulator.py`, `financial_portfolio_simulator/models/asset.py`, `financial_portfolio_simulator/models/portfolio.py`, `financial_portfolio_simulator/__init__.py`
  - Done when: All public functions validate inputs (e.g., empty asset lists, missing required keys, negative quantities, invalid correlation matrices, non-positive prices). Custom exceptions (`InvalidAssetError`, `InvalidPortfolioError`, `SimulationError`, `StrategyError`) are defined and raised appropriately.

- [ ] Task 2: Expand test coverage — edge cases, error handling, and integration tests
  - What: Add tests for all new error handling paths and fill existing coverage gaps. Add tests for: GBM edge cases (zero volatility, extreme drift), Portfolio edge cases (negative quantities, zero prices, duplicate tickers), Position `__post_init__` logic, `Portfolio.from_assets` classmethod, `weight_list`, `update_prices`, `SimulationResult` edge cases (all identical final values), correlated simulation with invalid correlation matrix, `run_simulation` with missing keys and invalid strategy names. Add integration tests that exercise the full pipeline.
  - Files: Modify `tests/test_models.py`, `tests/test_simulators.py`, `tests/test_api.py`, `tests/test_strategies.py`, create `tests/test_exceptions.py`, create `tests/test_integration.py`
  - Done when: Every new exception path has at least one test. All edge cases for models and simulators are covered. Integration test exercises `run_simulation` end-to-end with multi-asset, correlated, and strategy scenarios.

- [ ] Task 3: Write README.md with usage examples and documentation
  - What: Create a comprehensive README.md with project overview, installation instructions, quick start guide, API reference, example code snippets, and explanation of Monte Carlo simulation methodology.
  - Files: Create `README.md`
  - Done when: README includes: project description, installation (`pip install`), quick-start code example, detailed API usage examples (single asset, multi-asset, correlated), explanation of key classes (Asset, Portfolio, GBM, PortfolioSimulator, SimulationResult), configuration options (drift, volatility, seed, time_steps), and a note on Monte Carlo methodology.

- [ ] Task 4: Add pytest configuration and improve test infrastructure
  - What: Add pytest configuration to `pyproject.toml` (testpaths, markers, filterwarnings). Add useful fixtures in `conftest.py` (e.g., sample portfolio, sample assets, small simulation config). Ensure `pyproject.toml` dev dependencies are complete.
  - Files: Modify `pyproject.toml`, modify `conftest.py`
  - Done when: `pyproject.toml` has `[tool.pytest.ini_options]` with testpaths and markers. `conftest.py` provides reusable fixtures for common test data. `pytest --collect-only` discovers all tests without errors.

- [ ] Task 5: Run full test suite and verify all tests pass
  - What: Execute the complete test suite with pytest, fix any failures or warnings, and confirm 100% of tests pass cleanly.
  - Files: Run via `pytest` command in workspace directory
  - Done when: `pytest` runs with zero failures, zero errors, and zero warnings. All test classes and methods are discovered and executed.