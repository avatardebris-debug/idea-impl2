# Phase 1 Review — Character Reference Sheet Generation (MVP)

## What's Good

- **`models.py`**: `CharacterVisualProfile` Pydantic model is clean, well-documented, and correctly defines all required fields (`character_id`, `reference_image_path`, `visual_anchor_text`, `prompt`, `status`, `seed`). The `status` field defaults to `"pending"` as specified. The model serializes/deserializes correctly via Pydantic's built-in `model_dump`.

- **`image_provider.py`**: The `CharacterImageProvider` ABC correctly enforces the `generate_reference_image` signature. `KlingImageProvider` validates API key presence and raises a clear `ValueError` if missing. The exponential backoff retry logic is well-implemented with configurable `MAX_RETRIES` and `BASE_DELAY`. The `_make_placeholder_png` method generates a valid minimal PNG without external dependencies, which is a clever approach for testing and MVP.

- **`reference_sheet_generator.py`**: `ReferenceSheetGenerator` correctly iterates over registry characters, generates reference images via the provider, saves PNGs to `output_dir/characters/<char_id>.png`, and returns a `{char_id: image_path}` dict. The empty registry case is handled correctly (returns empty dict). The `CharacterVisualProfile` objects are created per character.

- **`consistent_character_stage.py`**: `ConsistentCharacterStage` correctly wraps `ReferenceSheetGenerator`, accepts `registry`, `output_dir`, and `provider` in the constructor, and `execute()` returns the augmented registry with visual data stored in `self.registry._visual_data`.

- **`__init__.py`**: Package-level exports are clean, exposing `CharacterVisualProfile`.

- **Architecture alignment**: The code aligns well with the master plan's architecture — the stage sits between character generation and script writing, the data model extends the existing `Character`/`CharacterRegistry` concepts, and the provider abstraction allows swapping implementations.

- **Logging**: All major operations are logged at appropriate levels (info/warning), making debugging straightforward.

- **Placeholder PNG**: The `_make_placeholder_png` method is a self-contained, dependency-free PNG generator that enables testing without external APIs. This is a smart MVP approach.

## Blocking Bugs

- **`reference_sheet_generator.py:78` — `CharacterVisualProfile` created but never attached to the character**: The `_generate_for_character` method creates a `CharacterVisualProfile` object but never attaches it to the `Character` instance. The code has a commented-out line `# character_visual_anchor_image_path = str(output_path)` which is just a variable assignment, not an attachment. The `Character` model from `ai_movie_gen_suite.models` has no `visual_anchor_image_path` attribute, so the profile is effectively lost. The `ConsistentCharacterStage.execute()` method stores image paths in `self.registry._visual_data` but does not augment individual `Character` objects with `visual_anchor_image_path` as the spec requires.

- **`consistent_character_stage.py:62` — Registry characters not augmented with `visual_anchor_image_path`**: The `execute()` method stores image paths in `self.registry._visual_data` but does NOT set `visual_anchor_image_path` on each character object. The spec says: "augments registry characters with `visual_anchor_image_path`". The current code only stores paths in a registry-level dict, not on individual characters. This means downstream stages cannot access `character.visual_anchor_image_path` directly.

- **`ai_consistent_char/stages/__init__.py` — Missing**: The spec calls for `stages/__init__.py` but it does not exist. While Python can import `consistent_character_stage.py` directly, this is a packaging gap that would break `from ai_consistent_char.stages import ConsistentCharacterStage` style imports.

- **`cli.py` — Missing**: The spec calls for `ai_consistent_char/cli.py` with a `run` subcommand, but this file does not exist. This is a deliverable gap.

- **`tests/` — Missing**: The spec calls for `tests/__init__.py`, `tests/conftest.py`, and `tests/test_reference_sheet.py`, but none exist. This is a deliverable gap.

## Non-Blocking Notes

- **`models.py:42` — `model_dump` override is redundant**: The overridden `model_dump` just calls `super().model_dump(**kwargs)` with no modification. It can be removed without changing behavior.

- **`image_provider.py` — `_call_kling_api` is a placeholder**: The actual Kling API call is commented out. This is acceptable for MVP but should be flagged for Phase 2.

- **`reference_sheet_generator.py:68` — Seed is not stored on the character**: The `seed` is used for generation but not persisted on the `Character` or `CharacterVisualProfile` in a way that's accessible from the registry.

- **`reference_sheet_generator.py:70` — `visual_anchor` fallback logic**: Uses `character.visual_anchor or character.physical_description`. This is reasonable but could be more explicit about priority.

- **Naming**: `character_visual_anchor_image_path` in `reference_sheet_generator.py:78` is a local variable that's never used (dead code).

- **`consistent_character_stage.py:62` — Using `_visual_data` private attribute**: Storing data via a private attribute on the registry is a workaround. A cleaner approach would be to add `visual_anchor_image_path` as a dynamic attribute on each `Character` object.

## Reusable Components

- **`KlingImageProvider` with placeholder PNG**: The `KlingImageProvider` class with its retry logic, prompt building, and self-contained `_make_placeholder_png` method is a self-contained, general-purpose image generation provider that could be reused by any project needing a text-to-image API wrapper with fallback.

- **`CharacterImageProvider` ABC**: The abstract base class defining the `generate_reference_image` contract is a clean, reusable interface for swapping image generation backends.

- **`_make_placeholder_png`**: The standalone method that generates a valid 1x1 PNG from raw bytes without any external dependencies is a useful utility for testing and MVP scenarios.

## Verdict

FAIL — Missing deliverables (cli.py, tests/, stages/__init__.py) and blocking bugs where `CharacterVisualProfile` objects are created but never attached to characters, and registry characters are not augmented with `visual_anchor_image_path` as the spec requires.
