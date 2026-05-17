# Code Review — Phase 2

## Blocking Bugs

### 1. Enrichment parser accepts `total_steps` and `avg_step_duration` as required fields but they are not part of the enrichment schema
**File:** `video_recipe/enricher.py` — `_parse_enrichment_response()`
**Issue:** The parser validates that `ingredients`, `equipment`, `difficulty`, `estimated_time_minutes`, and `key_takeaways` are present. It then unconditionally sets `total_steps` and `avg_step_duration` from `data.get()`, but these fields are never defined in the enrichment schema (the prompt, the parser's required fields, or the `enrich_recipe()` return contract). This is dead code that will silently do nothing useful and misleads anyone reading the code into thinking these are part of the enrichment output.
**Fix:** Remove the two lines that set `total_steps` and `avg_step_duration`. If they are needed later, add them to the schema and prompt first.

### 2. `build_enrichment_prompt()` uses the wrong system prompt constant
**File:** `video_recipe/enricher_prompts.py`
**Issue:** The module defines `ENRICH_SYSTEM_PROMPT` but `enricher.py` imports `SYSTEM_PROMPT_ENRICHED` from `video_recipe.prompts`. There is no guarantee that `prompts.py` actually exports `SYSTEM_PROMPT_ENRICHED` — if it doesn't, the import will fail at runtime. The test `test_enriched_prompt_has_enriched_system` only checks that the string *contains* certain keywords, not that the import works.
**Fix:** Verify that `video_recipe/prompts.py` defines and exports `SYSTEM_PROMPT_ENRICHED`. If it doesn't, either add it there or change the import in `enricher.py` to use `ENRICH_SYSTEM_PROMPT` from `enricher_prompts`.

### 3. `build_enriched_recipe_prompt()` in prompts.py doesn't match the actual enrichment prompt builder
**File:** `video_recipe/prompts.py` (referenced by test `test_enriched_recipe_prompt_includes_frames_and_transcript`)
**Issue:** The test imports `build_enriched_recipe_prompt` from `video_recipe.prompts`, but the actual enrichment prompt builder is `build_enrichment_prompt` in `video_recipe/enricher_prompts.py`. These are different functions with different signatures. The test will fail with an `ImportError` unless `prompts.py` also exports a function with that exact name and signature.
**Fix:** Either rename `build_enrichment_prompt` in `enricher_prompts.py` to `build_enriched_recipe_prompt` and export it from `prompts.py`, or update the test to import from the correct module.

### 4. `test_adaptive_extraction_fallback_on_failure` expects an empty list but the function may raise
**File:** `tests/test_phase2.py` — `TestAdaptiveFrameExtraction.test_adaptive_extraction_fallback_on_failure`
**Issue:** The test calls `_extract_adaptive_frames` with a non-existent video path and asserts the result is a list. However, if `_extract_adaptive_frames` raises an `ExtractionError` instead of returning an empty list, the test will fail. The docstring says "should fall back gracefully" but the assertion `assert isinstance(frames, list)` will never be reached if an exception is raised.
**Fix:** Either (a) ensure `_extract_adaptive_frames` actually returns `[]` on failure (and update the docstring), or (b) wrap the call in `pytest.raises(ExtractionError)` if raising is the correct behavior.

### 5. `test_normalize_unsupported_format_raises` creates a file with `.xyz` extension but `_normalize_video_format` may not check extension
**File:** `tests/test_phase2.py` — `TestVideoFormatNormalization.test_normalize_unsupported_format_raises`
**Issue:** The test creates a file `test.xyz` and expects `_normalize_video_format` to raise `ExtractionError`. However, if the function checks the file extension against a whitelist (e.g., `[".mp4", ".mov", ".avi"]`), it will raise. But if it checks the file *content* or uses `ffmpeg` to probe the format, it may not raise because `.xyz` is just a filename — ffmpeg might still try to process it. The test's assumption about *why* it raises is fragile.
**Fix:** Either (a) ensure the function checks extension first and raises for unknown extensions, or (b) use a file with a known-but-unsupported extension (like `.webm` if not supported) and verify the error message.

## Medium Issues

### 6. Enrichment prompt instructs "no markdown, no code fences" but the parser handles them
**File:** `video_recipe/enricher_prompts.py` (prompt) vs `enricher.py` (parser)
**Issue:** The system prompt explicitly says "You MUST output valid JSON only — no markdown, no explanation, no code fences." But `_parse_enrichment_response()` handles JSON wrapped in markdown code fences. This is contradictory — the prompt discourages what the parser is prepared to handle. While this is defensive coding (good), it creates confusion about the expected contract.
**Fix:** Either remove the code-fence handling from the parser (trust the prompt), or update the prompt to say "JSON wrapped in markdown code fences is acceptable."

### 7. `estimated_time_minutes` validation is too strict
**File:** `video_recipe/enricher.py` — `_parse_enrichment_response()`
**Issue:** The parser checks `isinstance(data["estimated_time_minutes"], int)`. However, JSON numbers like `15.0` will be parsed as `float` by `json.loads()`, causing this check to fail. The prompt says "number" in the schema, not "integer". This will reject valid LLM responses that return `15.0` instead of `15`.
**Fix:** Change the check to `isinstance(data["estimated_time_minutes"], (int, float))` and convert to `int` if needed.

### 8. `enrich_recipe()` copies the recipe but doesn't deep-copy nested structures
**File:** `video_recipe/enricher.py` — `enrich_recipe()`
**Issue:** `result = recipe.copy()` is a shallow copy. If the caller mutates `result["steps"]` or `result["summary"]` after calling `enrich_recipe()`, the original `recipe` dict will also be mutated. This is a subtle bug that could cause issues in the CLI pipeline.
**Fix:** Use `copy.deepcopy(recipe)` or at least `result["steps"] = [s.copy() for s in recipe.get("steps", [])]`.

### 9. Tests use real `ffmpeg` subprocess calls — fragile and slow
**File:** `tests/test_phase2.py`
**Issue:** Multiple tests (`test_motion_detection_returns_array`, `test_adaptive_extraction_returns_frames`, `test_normalize_mov_to_mp4`, etc.) spawn real `ffmpeg` processes to create test videos. This makes the test suite:
- Slow (each test spawns a subprocess)
- Fragile (depends on `ffmpeg` being installed and working)
- Non-portable (may fail on CI environments without ffmpeg)
**Fix:** Mock `subprocess.run` or use `unittest.mock.patch` to avoid real ffmpeg calls. Alternatively, use a pre-generated test video file committed to the repo.

### 10. `test_cli_with_output_file` in `test_e2e.py` has a confusing assertion
**File:** `tests/test_e2e.py` — `TestIntegration.test_cli_with_output_file`
**Issue:** The assertion `assert output_file.exists() or result.returncode in (0, 3, 5)` is logically incorrect. It will pass if the file exists OR if the return code is 0/3/5, regardless of whether the other condition is true. The intent seems to be "the command should not crash due to I/O errors," but the assertion doesn't verify that. If the command crashes with return code 1 (LLM error), the file might not exist and the test still passes.
**Fix:** Clarify the intent. If the goal is to ensure the CLI doesn't crash on I/O, check `result.returncode != -1` (not crashed) and verify the file exists if the return code is 0.

## Low Issues / Suggestions

### 11. `build_enrichment_prompt()` string formatting is inefficient
**File:** `video_recipe/enricher_prompts.py`
**Issue:** The function builds the prompt by concatenating strings in a loop (`steps_info += ...`). For recipes with many steps, this creates many intermediate string objects.
**Fix:** Use `"".join()` with a list comprehension or generator expression for better performance.

### 12. Missing type hints on `enrich_recipe()` parameters
**File:** `video_recipe/enricher.py`
**Issue:** The function signature uses `dict[str, Any]` for `recipe` and `list[dict[str, Any]]` for `frames`, but these are overly generic. The prompt and parser define a specific schema.
**Fix:** Consider using TypedDict or dataclasses for `Recipe`, `Frame`, and `Enrichment` types to make the contract explicit and catch errors at type-check time.

### 13. `EnrichmentError` is defined in `enricher.py` but not re-exported from the package `__init__.py`
**File:** `video_recipe/__init__.py` (if it exists)
**Issue:** Consumers of the package can't easily import `EnrichmentError` without importing from the submodule.
**Fix:** Re-export `EnrichmentError` from `video_recipe/__init__.py` if it's part of the public API.

### 14. Test `test_enriched_recipe_with_code_fences` uses triple backticks in the string
**File:** `tests/test_phase2.py` — `TestEnrichmentSchema.test_enriched_recipe_with_code_fences`
**Issue:** The mock response uses `"""` (triple quotes) to wrap the string, but the content itself contains ` ```json ` and ` ``` `. This is syntactically valid Python but visually confusing. The triple backticks in the content could be misread as ending the triple-quoted string.
**Fix:** Use a raw string or escape the backticks for clarity.

### 15. No test for `enrich_recipe()` when `OPENAI_API_KEY` is missing
**File:** `tests/test_phase2.py`
**Issue:** The `enrich_recipe()` function checks for `OPENAI_API_KEY` and raises `EnrichmentError` if it's missing. There's no test covering this code path.
**Fix:** Add a test that patches `os.environ` to remove `OPENAI_API_KEY` and verifies the error is raised.

### 16. `test_cli_with_output_file` creates a video but doesn't verify the output content
**File:** `tests/test_e2e.py` — `TestIntegration.test_cli_with_output_file`
**Issue:** The test creates a video, runs the CLI, and checks that the output file exists or the return code is in an expected set. But it doesn't verify the *content* of the output file. If the CLI writes an empty file or an error message, the test still passes.
**Fix:** Add assertions to verify the output file contains valid JSON with expected fields (e.g., `title`, `steps`).

### 17. `build_enrichment_prompt()` doesn't handle missing `inferred_tools` or `inferred_materials` gracefully
**File:** `video_recipe/enricher_prompts.py`
**Issue:** The function accesses `step.get("inferred_tools", [])` and `step.get("inferred_materials", [])`, which is correct. But if a step dict is `None` or not a dict, this will raise an `AttributeError`. The function assumes all steps are valid dicts.
**Fix:** Add a guard: `if not isinstance(step, dict): continue` or document that steps must be dicts.

### 18. The enrichment prompt's schema says `"estimated_time_minutes": number` but the parser expects `int`
**File:** `video_recipe/enricher_prompts.py` (prompt) vs `enricher.py` (parser)
**Issue:** The prompt's JSON schema says `number` (which includes floats), but the parser's validation requires `int`. This mismatch means the LLM could return `15.5` and the parser would reject it, even though the prompt says `number`.
**Fix:** Align the prompt schema to say `integer` or update the parser to accept floats.

### 19. `test_normalize_mov_to_mp4` and `test_already_normalized_mp4_returns_same` both create videos with `ffmpeg` — DRY violation
**File:** `tests/test_phase2.py`
**Issue:** Both tests create a test video using the same `ffmpeg` command. This is repetitive and makes it harder to maintain.
**Fix:** Extract the video creation into a fixture or helper function.

### 20. No test for `enrich_recipe()` with a recipe that has no steps
**File:** `tests/test_phase2.py`
**Issue:** The `sample_recipe` fixture always has steps. There's no test for edge cases like an empty steps list or a recipe with no `steps` key at all.
**Fix:** Add a test case with an empty or missing `steps` field.
