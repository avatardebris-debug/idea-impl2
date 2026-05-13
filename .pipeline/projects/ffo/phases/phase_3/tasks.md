# Phase 3 Tasks

- [x] Task 1: Create CLI entry point for FFO
  - What: Build a command-line interface so users can run the optimizer from the terminal. The CLI should accept a roster file (JSON), a free agent pool file (JSON), and a salary cap value, then output the optimized roster as JSON to stdout.
  - Files: ffo/__main__.py (package entry point for `python -m ffo`), ffo/cli.py (CLI argument parsing and orchestration), ffo/io_utils.py (JSON read/write helpers)
  - Done when: Running `python -m ffo --roster roster.json --pool pool.json --cap 150000000` prints a valid JSON-serialized optimized roster to stdout; `--help` shows usage; invalid inputs produce clear error messages with non-zero exit codes

- [x] Task 2: Add comprehensive test suite for all ffo modules
  - What: Write unit tests covering every public function and class in the ffo package — Player/FreeAgent serialization, SalaryCap add/remove/can_afford, valuation scoring and ranking, FreeAgentPool filtering and top-N queries, and the optimize_roster greedy algorithm (including edge cases like empty pool, already-over-cap roster, single-player roster).
  - Files: tests/test_player.py, tests/test_salary_cap.py, tests/test_valuation.py, tests/test_free_agent_pool.py, tests/test_optimizer.py, tests/conftest.py (shared fixtures for sample players/pools)
  - Done when: `pytest` runs all tests with 100% pass rate; test coverage for ffo package is at least 90%; tests exercise edge cases (zero salary, negative rating, empty lists, cap-exceeding inputs)

- [ ] Task 3: Create public API surface and programmatic usage examples
  - What: Add a high-level `ffo/api.py` module that exposes a clean, documented public API for programmatic use. This should include convenience functions like `load_roster_from_json`, `load_pool_from_json`, `optimize`, and `generate_report` (which returns a summary dict of the optimization result). Also add example scripts in `examples/` demonstrating common workflows (e.g., full optimization pipeline, filtering agents by position, comparing strategies with different weights).
  - Files: ffo/api.py, examples/optimize_roster.py, examples/filter_and_rank.py, examples/README.md
  - Done when: `from ffo.api import optimize, load_roster_from_json, load_pool_from_json, generate_report` works; both example scripts run without errors and produce correct output; API docstrings follow Google style

- [ ] Task 4: Write complete README and usage documentation
  - What: Create a comprehensive README.md at the project root with: project overview, installation instructions (pip install from source), quick-start CLI example, quick-start Python API example, full API reference (all public classes and functions with signatures and descriptions), configuration options (age_weight, contract_weight), and a FAQ/troubleshooting section.
  - Files: README.md
  - Done when: README covers installation, CLI usage, Python API usage, all public API signatures, and configuration; a reader can install the package and run the optimizer end-to-end using only the README

- [ ] Task 5: Finalize deployment configuration and add deployment docs
  - What: Update pyproject.toml with proper package metadata (author, license, classifiers, python_requires), add CLI entry point in [project.scripts], add test and dev extras ([project.optional-dependencies]), and create a DEPLOY.md with step-by-step instructions for building the package (`python -m build`), publishing to PyPI, and verifying the installation.
  - Files: pyproject.toml (updated), DEPLOY.md
  - Done when: `pip install -e .` installs the package with the `ffo` CLI command available; `pip install -e ".[test,dev]"` installs test and dev dependencies; DEPLOY.md has clear build and publish steps; `python -m build` produces a valid wheel and sdist