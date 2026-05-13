# Makefile for Movie Idea Generator
# Common development commands

.PHONY: install test lint clean release

# Install the package in development mode with dev dependencies
install:
	pip install -e ".[dev]"

# Run the full test suite with verbose output
test:
	pytest -v test_movie_idea_generator.py test_cli.py

# Lint the codebase (placeholder — add flake8/ruff/mypy as needed)
lint:
	@echo "Linting placeholder — add flake8, ruff, or mypy here"

# Remove build artifacts and cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info movie_idea_generator.egg-info
	rm -rf .pytest_cache/ .mypy_cache/

# Bump version and build sdist/wheel distributions
release:
	python -m build
	@echo "Build complete. Check dist/ for the artifacts."
