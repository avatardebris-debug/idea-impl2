# Phase 3 Tasks

- [ ] Task 1: Add CLI entry point
- [ ] Task 1: Build a CLI tool using `argparse` that exposes the library's core functionality: create a player, get attributes, and match players. Register it as a console script in `pyproject.toml`.
  - **Files**: `scripts/cli.py` (new), `pyproject.toml` (update `[project.scripts]`)
  - **Done when**: `player-attr-cli create --name "Test" --speed 80` prints player info; `player-attr-cli match --target-file target.json --candidates-file candidates.json` outputs matches; `pip install -e .` makes the CLI available; `player-attr-cli --help` works.

- [ ] Task 2: Add JSON serialization helpers
- [ ] Task 2: Add `to_json()` / `from_json()` methods to `PlayerAttribute` for file-based persistence, plus `save_players()` and `load_players()` module-level functions for batch operations. This enables the CLI to read/write player data from files.
  - **Files**: `player_attribute_library/models.py` (add `to_json`, `from_json`), `player_attribute_library/core.py` (add `save_players`, `load_players`), `player_attribute_library/__init__.py` (export new functions)
  - **Done when**: `PlayerAttribute` objects can be serialized to JSON and deserialized back with identical attribute values; batch save/load works for lists of players; no regressions in existing tests.

- [ ] Task 3: Add type hints and `__all__` to all modules
- [ ] Task 3: Add complete type annotations to all public functions in `core.py` and `models.py` (e.g., proper `TypedDict` for player dicts, `Literal` for metric names). Add explicit `__all__` lists to `core.py`, `models.py`, and `demo.py` to declare the public API and prevent accidental imports of internal symbols.
  - **Files**: `player_attribute_library/core.py`, `player_attribute_library/models.py`, `player_attribute_library/demo.py`
  - **Done when**: All public functions have parameter and return type annotations; each module has an `__all__` list; `from player_attribute_library import *` only imports symbols in `__all__`; no regressions in existing tests.

- [ ] Task 4: Add integration / end-to-end tests
- [ ] Task 4: Create `tests/test_integration.py` with end-to-end tests covering: full workflow (create → query → match), CLI invocation via `subprocess`, and serialization round-trip (to_json → from_json → compare).
  - **Files**: `player_attribute_library/tests/test_integration.py` (new)
  - **Done when**: All integration tests pass; CLI tests verify output format; serialization tests verify data integrity; no regressions in existing tests.

- [ ] Task 5: Update README with deployment docs, add CHANGELOG, bump version
- [ ] Task 5: Create a `CHANGELOG.md` with version history (1.0.0). Update `README.md` to include: installation from PyPI, CLI usage examples, deployment/packaging instructions (how to build and publish the package), and a link to the CHANGELOG. Bump version from 0.1.0 to 1.0.0 in `__init__.py` and `pyproject.toml`.
  - **Files**: `CHANGELOG.md` (new), `README.md` (update), `player_attribute_library/__init__.py` (version bump), `pyproject.toml` (version bump)
  - **Done when**: CHANGELOG.md exists with a 1.0.0 section documenting all Phase 1-3 features; README.md has installation, CLI usage, deployment, and changelog sections; version is 1.0.0 everywhere; no broken links.

- [ ] Task 6: Final validation — run full test suite, verify package builds
- [ ] Task 6: Run the complete test suite with verbose output, verify the package builds correctly (`python -m build`), and confirm the CLI is functional. Update `current_phase.json` to mark Phase 3 as complete.
  - **Files**: `.pipeline/projects/player_attribute_library/state/current_phase.json`
  - **Done when**: `pytest -v` passes all tests (existing + new); `python -m build` produces a valid wheel and sdist; CLI is accessible after `pip install -e .`; current_phase.json reflects Phase 3 completion.