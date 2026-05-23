# Code Review — Phase 1

## Review Date
2025-01-01

## Scope
Phase 1: MVP — Single-Scene Recipe Extraction

## Files Reviewed
- `video_recipe_mu/__init__.py` — Package init
- `video_recipe_mu/cli.py` — CLI entry point
- `video_recipe_mu/recipe_extractor.py` — LLM-driven extraction
- `video_recipe_mu/recipe_parser.py` — JSON/Markdown parsing
- `video_recipe_mu/recipe_validator.py` — Step validation
- `video_recipe_mu/schema.py` — TypedDict schema
- `workspace/conftest.py` — pytest conftest

## Blocking Bugs

### Bug 1: Missing `prompts` directory
**File:** `video_recipe_mu/recipe_extractor.py`
**Issue:** `_load_prompt_template()` references a `prompts/` directory that does not exist. This will cause a `FileNotFoundError` when `_build_extraction_prompt()` is called.
**Fix:** Create the `prompts/` directory with the required `recipe_extraction.md` template.

### Bug 2: No tests exist
**File:** `workspace/` (no test files)
**Issue:** The validation report confirms "0 tests collected." Phase 1 spec requires tests that pass with pytest.
**Fix:** Create `workspace/test_recipe_parser.py` and `workspace/test_recipe_validator.py` with unit tests.

### Bug 3: Missing `__main__.py` for CLI invocation
**File:** `video_recipe_mu/` (no `__main__.py`)
**Issue:** The CLI module exists but there's no `__main__.py` to allow `python -m video_recipe_mu` invocation.
**Fix:** Create `video_recipe_mu/__main__.py`.

## Non-Blocking Notes
- Code structure is clean and well-organized.
- Schema uses TypedDict appropriately.
- Validator covers both single-step and cross-step validation.
- Parser handles both JSON and Markdown inputs.

## Verdict
FAIL — blocking bugs must be fixed before Phase 1 can pass validation.
