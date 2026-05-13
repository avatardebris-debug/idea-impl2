# Phase 2 Tasks

- [x] Task 1: Add input validation and error handling to the generator
  - What: Add validation for invalid genres, count <= 0, and other edge cases. Raise ValueError with descriptive messages.
  - Files: movie_idea_generator/generator.py
  - Done when: MovieIdeaGenerator raises ValueError for invalid genre names and count <= 0; valid genres still work; generate_batch with count=0 returns []

- [x] Task 2: Write comprehensive unit tests for the generator module
  - What: Add pytest tests covering: valid genre generation, invalid genre rejection, batch generation edge cases (count=0, count=1, large count), seed reproducibility, character generation structure, and all 10 genres.
  - Files: test_movie_idea_generator.py (extend), conftest.py (add fixtures if needed)
  - Done when: All generator tests pass via pytest; covers every public method and error path; test count >= 15

- [x] Task 3: Write CLI integration tests
  - What: Add pytest tests for the CLI: argument parsing, text output format, JSON output format, --genre flag, --count flag, --seed flag, and invalid argument handling.
  - Files: test_cli.py (new)
  - Done when: CLI tests pass via pytest; covers all CLI flags and output formats; test count >= 8

- [x] Task 4: Add a README.md with usage documentation
  - What: Write a complete README covering: project description, installation, usage (CLI examples), programmatic API usage, available genres, output format, and contributing notes.
  - Files: README.md (new)
  - Done when: README exists at project root; includes CLI examples showing text and JSON output; includes programmatic API example; covers all --genre, --count, --format, --seed flags

- [x] Task 5: Run full test suite and verify all tests pass
  - What: Execute pytest across the entire workspace to confirm everything works together. Fix any regressions.
  - Files: All test files
  - Done when: pytest runs with zero failures and zero errors; all smoke tests, unit tests, and CLI tests pass