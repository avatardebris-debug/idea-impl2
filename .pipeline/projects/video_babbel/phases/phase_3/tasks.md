# Phase 3 Tasks

- [ ] Task 1: Add CLI entry point (console script)
  - What: Create a `video_babbel/cli.py` module with a Click-based CLI that exposes the full pipeline. Add a `__main__.py` so `python -m video_babbel` works. Register the CLI as a console script entry point in pyproject.toml.
  - Files: `video_babbel/cli.py` (new), `video_babbel/__main__.py` (new), `pyproject.toml` (modify — add `[project.scripts]` section)
  - Done when: Running `video-babbel --help` from the command line prints usage info; `video-babbel --video /path/to/video.mp4 --lang es` executes the pipeline end-to-end; `python -m video_babbel --help` also works.

- [ ] Task 2: Create Dockerfile and docker-compose for deployment
  - What: Write a multi-stage Dockerfile that installs ffmpeg, Python dependencies, and copies the package. Add a docker-compose.yml with a service that mounts a local videos directory for easy use.
  - Files: `Dockerfile` (new), `docker-compose.yml` (new), `.dockerignore` (new)
  - Done when: `docker build -t video-babbel .` succeeds; `docker compose up` starts the service; the container can process a video file passed via mounted volume.

- [ ] Task 3: Write comprehensive README with installation, usage, and API docs
  - What: Expand the existing README.md to include: full installation instructions (pip, Docker, from source), CLI usage examples (all flags), Python API usage examples (programmatic), architecture overview diagram (text-based), configuration options, and troubleshooting section.
  - Files: `README.md` (modify)
  - Done when: README covers installation (3 methods), CLI examples, Python API examples, architecture overview, configuration, and troubleshooting; all code blocks are syntactically valid.

- [ ] Task 4: Add programmatic API reference and type hints
  - What: Ensure all public classes and functions in `video_babbel/__init__.py` have docstrings. Add type hints to any remaining untyped function signatures. Create an `api_reference.md` file documenting every public class, method, parameter, return type, and exception.
  - Files: `video_babbel/__init__.py` (modify — docstrings), `video_babbel/core.py` (modify — type hints if missing), `video_babbel/pipeline.py` (modify — type hints if missing), `video_babbel/cli.py` (modify — type hints if missing), `docs/api_reference.md` (new)
  - Done when: All public symbols have docstrings and type hints; `docs/api_reference.md` lists every public class/method with parameters, return types, and exceptions; running `python -c "from video_babbel import VideoBabbel; help(VideoBabbel)"` shows complete docs.

- [ ] Task 5: Add integration tests and smoke tests
  - What: Create `tests/test_integration.py` with end-to-end smoke tests that mock external dependencies (ffmpeg, whisper, googletrans) to validate the full pipeline and CLI work correctly. Add a `tests/test_cli.py` with CLI argument parsing tests.
  - Files: `tests/test_integration.py` (new), `tests/test_cli.py` (new)
  - Done when: `pytest tests/test_integration.py` passes with mocked dependencies; `pytest tests/test_cli.py` passes; integration tests cover: full pipeline flow, CLI with all flags, error handling paths.

- [ ] Task 6: Final package validation and release prep
  - What: Verify the package builds correctly with `python -m build`, check that `pip install` works, ensure all tests pass, verify the package metadata in pyproject.toml is complete (license, authors, classifiers), and add a CHANGELOG.md.
  - Files: `pyproject.toml` (modify — add license, authors, classifiers), `CHANGELOG.md` (new), `LICENSE` (new — MIT), `MANIFEST.in` (new)
  - Done when: `python -m build` produces a wheel and sdist; `pip install dist/video_babbel-*.whl` installs correctly; all tests pass; CHANGELOG documents all Phase 3 changes; LICENSE file is MIT; pyproject.toml has complete metadata.