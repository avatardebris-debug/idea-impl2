# Phase 1 Tasks

- [ ] Task 1: Scaffold project structure and configure dependencies
  - What: Create the project skeleton with pyproject.toml, package directory, and all required dependencies wired up
  - Files: pyproject.toml, beatsheet_generator/__init__.py, beatsheet_generator/models.py
  - Done when: pyproject.toml declares dependencies on movie-idea-generator and ai-movie-gen-suite, defines the beatsheet-gen CLI entry point, and includes pytest dev deps; beatsheet_generator/__init__.py exposes BeatSheetService and main; beatsheet_generator/models.py exists as a placeholder for local models (all models come from ai_movie_gen_suite)

- [ ] Task 2: Implement BeatSheetService core class
  - What: Build the BeatSheetService class that orchestrates the full flow from movie idea input to beat sheet output, including character enrichment
  - Files: beatsheet_generator/service.py
  - Done when: BeatSheetService supports initialization via (title/genre/logline/characters/tone), from_idea_dict(), and from_json_file(); generate() calls BeatGenerator.generate_beat_sheet(), enriches beats with character involvement, and returns a dict with beat_sheet, beat_sheet_json, beat_sheet_dict, output_path, title, genre, num_beats; save_to_file() uses JSONFormatter to persist the beat sheet; get_beat_sheet() returns the current BeatSheet or None; validation raises ValueError for missing logline/genre and RuntimeError for save without generate; character enrichment maps protagonist/antagonist/mentor/ally roles to appropriate beats by beat number

- [ ] Task 3: Implement CLI entry point
  - What: Build the CLI that accepts movie ideas (directly or from movie_idea_generator) and outputs beat sheets in text or JSON format
  - Files: beatsheet_generator/cli.py
  - Done when: CLI accepts --title, --genre, --logline, --tone, --output/-o, --format/-f (text|json), --source-movie-idea, --seed, --count; when --source-movie-idea is provided, loads idea from JSON file; when no logline provided, falls back to movie_idea_generator via MovieIdeaGenerator.generate_batch(); text format outputs formatted beat sheet with phase emojis and character lists; JSON format outputs raw JSON; --output saves to file; missing logline/genre produces a clear error message and exits with code 1

- [ ] Task 4: Write unit tests for BeatSheetService
  - What: Create comprehensive unit tests covering all BeatSheetService methods and edge cases
  - Files: tests/test_service.py
  - Done when: Tests cover init (strings, from_idea_dict, from_json_file), generate (from strings, from idea dict, missing logline, missing genre), save_to_file (success, without generate), character enrichment (with characters, without characters), get_beat_sheet (before/after generate), and repr (before/after generate); all mocks are properly configured for BeatGenerator

- [ ] Task 5: Write integration and CLI tests
  - What: Create integration tests that verify end-to-end flows and CLI behavior
  - Files: tests/test_integration.py, tests/test_cli.py
  - Done when: test_integration.py covers generate from movie idea dict, from JSON file, from strings, serialization, save/load, character enrichment, error handling, and CLI integration; test_cli.py covers CLI generation, JSON/text format output, source movie idea loading, file saving, missing logline error, and default format; all tests use proper mocking of BeatGenerator and BeatSheetService