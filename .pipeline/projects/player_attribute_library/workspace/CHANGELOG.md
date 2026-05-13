# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2025-01-01

### Added
- **CLI tool** (`scripts/cli.py`) with `create`, `match`, and `list` subcommands
- **JSON serialization**: `PlayerAttribute.to_json()` / `from_json()` methods
- **Batch I/O**: `save_players()` / `load_players()` functions in `core.py`
- **Type hints** and `__all__` exports on all modules (`models.py`, `core.py`, `demo.py`, `__init__.py`)
- **Integration / end-to-end tests** covering CLI, serialization round-trips, and full workflow
- **Deployment guide** in README (PyPI, Docker, GitHub Actions)
- **Dockerfile** for containerized builds
- **GitHub Actions workflow** for CI/CD (lint, test, build, publish)
- **Pre-commit hooks** configuration (black, isort, flake8, mypy)
- **`.gitignore`** for Python artifacts
- **`pyproject.toml`** with full project metadata, dependencies, and CLI entry point

### Changed
- Bumped version from `0.1.0` to `1.0.0`

### Fixed
- Clamping logic in `PlayerAttribute.__post_init__` to properly handle values outside 0–100

## [0.1.0] — Initial Release

### Added
- `PlayerAttribute` dataclass with 6 default attributes (speed, shooting, passing, defending, physical, mental)
- `create_player()`, `get_attribute()`, `get_all_attributes()` helpers
- `euclidean_distance()` and `cosine_similarity()` matching functions
- `match_players()` with metric selection and top-N filtering
- Demo script (`demo.py`)
- Basic test suite (`test_models.py`, `test_core.py`)
- Project scaffolding (`pyproject.toml`, `README.md`, `LICENSE`)
