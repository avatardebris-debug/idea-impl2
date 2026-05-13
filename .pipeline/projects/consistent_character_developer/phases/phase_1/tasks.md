# Phase 1 Tasks

- [ ] Task 1: Create data models (models.py)
  - What: Define `CharacterVisualProfile` Pydantic model in `ai_consistent_char/models.py` that extends the existing `Character` / `CharacterRegistry` from `ai_movie_gen_suite.models`. Include fields: `character_id`, `reference_image_path`, `visual_anchor_text`, `prompt`, `status`, `seed`. Add `__init__.py` and package scaffolding.
  - Files: `consistent_character_developer/ai_consistent_char/__init__.py`, `consistent_character_developer/ai_consistent_char/models.py`
  - Done when: `CharacterVisualProfile` can be instantiated with all fields; `status` defaults to `"pending"`; model serializes/deserializes correctly via Pydantic; package imports cleanly.

- [ ] Task 2: Implement image provider abstraction (image_provider.py)
  - What: Create `CharacterImageProvider` ABC with `generate_reference_image` abstract method. Implement `KlingImageProvider` subclass that validates API key presence, constructs a text-to-image prompt from `visual_anchor_text`, and calls the Kling AI API (or a mock for testing). Include retry logic with exponential backoff.
  - Files: `consistent_character_developer/ai_consistent_char/image_provider.py`
  - Done when: ABC enforces `generate_reference_image` signature; `KlingImageProvider` raises a clear error if API key is missing; mock provider can be substituted for tests; retry logic covers transient failures.

- [ ] Task 3: Implement reference sheet generator (reference_sheet_generator.py)
  - What: Create `ReferenceSheetGenerator` class that takes a `CharacterImageProvider` and `output_dir`. Implement `generate_for_registry(registry)` that iterates all characters, calls the provider to generate a reference image per character, saves PNGs to `output_dir/characters/<char_id>.png`, creates a `CharacterVisualProfile` per character, and returns `{char_id: image_path}` dict.
  - Files: `consistent_character_developer/ai_consistent_char/reference_sheet_generator.py`
  - Done when: Empty registry returns empty dict; single character produces one PNG file; multiple characters produce distinct PNG files; returned dict maps every char_id to a valid file path; `CharacterVisualProfile` objects are created and attached to registry characters.

- [ ] Task 4: Implement ConsistentCharacterStage (consistent_character_stage.py)
  - What: Create `ConsistentCharacterStage` class that wraps `ReferenceSheetGenerator` and integrates with `MovieGenerationPipeline`. Constructor accepts `registry`, `output_dir`, and `provider`. `execute()` generates reference images, augments registry characters with `visual_anchor_image_path`, and returns the augmented registry.
  - Files: `consistent_character_developer/ai_consistent_char/stages/__init__.py`, `consistent_character_developer/ai_consistent_char/stages/consistent_character_stage.py`
  - Done when: Stage can be instantiated with a registry and provider; `execute()` returns a registry where every character has `visual_anchor_image_path` set; stage can be inserted into `MovieGenerationPipeline` between character generation and script writing without breaking existing flow.

- [ ] Task 5: Implement CLI extension (cli.py)
  - What: Create CLI entry point in `ai_consistent_char/cli.py` with a `run` subcommand that accepts `--title`, `--logline`, `--output-dir`, and `--provider` flags. The CLI should invoke the pipeline with the `ConsistentCharacterStage` inserted, generate reference images, and print a summary of generated characters and image paths.
  - Files: `consistent_character_developer/ai_consistent_char/cli.py`
  - Done when: `ai-consistent-char run --title "..." --logline "..."` executes end-to-end; reference images are generated for all characters; CLI prints a summary table of character IDs and image paths; `--provider kling` flag selects the image provider; invalid flags produce clear error messages.

- [ ] Task 6: Write unit tests (test_reference_sheet.py)
  - What: Create comprehensive test suite in `consistent_character_developer/tests/test_reference_sheet.py` covering all Phase 1 components. Use mocks for the image provider to avoid external API calls.
  - Files: `consistent_character_developer/tests/__init__.py`, `consistent_character_developer/tests/conftest.py`, `consistent_character_developer/tests/test_reference_sheet.py`
  - Done when: All 8 planned tests pass: `test_reference_sheet_generator_initialization`, `test_generate_for_registry_empty`, `test_generate_for_registry_single_char`, `test_generate_for_registry_multiple_chars`, `test_image_path_is_valid_file`, `test_registry_augmented_with_visual_data`, `test_consistent_character_stage_integration`, `test_kling_provider_validation`. No warnings or errors from test runner.