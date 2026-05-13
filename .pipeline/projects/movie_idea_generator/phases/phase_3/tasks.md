# Phase 3 Tasks

- [x] Task 1: Create pyproject.toml for modern Python packaging
  - What: Write a pyproject.toml with project metadata (name, version, description, authors), build-system config (setuptools), and package configuration including the movie_idea_generator package. Include console_scripts entry point so `movie-idea-generator` CLI command works after install.
  - Files: pyproject.toml (new)
  - Done when: pyproject.toml exists with [build-system], [project], and [project.scripts] sections; `pip install -e .` succeeds; `movie-idea-generator --help` works from the command line

- [x] Task 2: Add LICENSE, CHANGELOG, and requirements files
  - What: Create a MIT LICENSE file, a CHANGELOG.md with an initial v0.1.0 entry documenting the core features, and a requirements.txt listing pytest as a dev dependency.
  - Files: LICENSE (new), CHANGELOG.md (new), requirements.txt (new)
  - Done when: LICENSE contains a valid MIT license text; CHANGELOG.md has a v0.1.0 section with feature list; requirements.txt lists pytest under dev dependencies

- [x] Task 3: Create Makefile for common development commands
  - What: Write a Makefile with targets for: install (pip install -e .[dev]), test (pytest -v), lint (optional placeholder), clean (remove build artifacts), and release (bump version and build sdist/wheel).
  - Files: Makefile (new)
  - Done when: `make install` installs the package; `make test` runs the full test suite; `make clean` removes __pycache__, build/, dist/, *.egg-info; all targets are documented with comments

- [x] Task 4: Add deployment documentation
  - What: Create docs/deployment.md with step-by-step instructions for: building the package (python -m build), testing locally (pip install dist/*.whl), publishing to PyPI (twine upload), and a quick-start guide for end users. Update README.md to reference the deployment docs and add a "Installation from PyPI" section.
  - Files: docs/deployment.md (new), README.md (modify)
  - Done when: deployment.md covers build, test, publish, and install steps; README.md includes a PyPI installation section and links to deployment docs

- [x] Task 5: Verify the full package build and install cycle
  - What: Run the complete build-and-install cycle end-to-end: clean artifacts, build sdist and wheel, install the wheel in a fresh context, run `movie-idea-generator --help`, run `python -m movie_idea_generator --count 2 --format json`, and run the full test suite one final time.
  - Files: All existing files (verification only)
  - Done when: `python -m build` produces dist/ with .tar.gz and .whl; `pip install` from the wheel works; CLI command works; `python -m movie_idea_generator` works; all 68+ tests pass with zero failures