# Phase 2 Tasks

- [ ] Task 1: Add `--enrich` CLI flag and enriched recipe schema
  - What: Add a `--enrich` boolean flag to the CLI argparse. When enabled, the pipeline calls an enrichment step after recipe generation that adds fields: `ingredients`, `equipment`, `difficulty`, `estimated_time_minutes`, `key_takeaways`, `total_steps`, `avg_step_duration`. Update the formatter to include enriched fields in both JSON and Markdown output.
  - Files: `video_recipe/cli.py` (add --enrich flag, wire enrichment call), `video_recipe/formatter.py` (update render_json and render_markdown to include enriched fields)
  - Done when: Running `python -m video_recipe --input test.mp4 --enrich --format json` produces JSON with all 7 enriched fields present. Running without `--enrich` produces the original Phase 1 output (no regression).

- [ ] Task 2: Build the enrichment LLM client and prompt
  - What: Create `video_recipe/enricher.py` with a function `enrich_recipe(recipe: dict, frames: list[dict], transcript: str) -> dict` that sends the base recipe + frames + transcript to the LLM with a structured prompt asking for: ingredient list, equipment list, difficulty (easy/medium/hard), estimated time in minutes, and key takeaways. The prompt should instruct the LLM to infer these from visual and audio evidence. Also create `video_recipe/enricher_prompts.py` with the enrichment system prompt and user prompt builder.
  - Files: `video_recipe/enricher.py` (new), `video_recipe/enricher_prompts.py` (new)
  - Done when: Given a base recipe dict, frames, and transcript, `enrich_recipe()` returns a dict with all 5 enriched fields populated. The enrichment prompt clearly instructs the LLM to output valid JSON with the enriched schema.

- [ ] Task 3: Adaptive frame extraction
  - What: Replace the uniform-interval frame extraction in `extractor.py` with an adaptive approach. Use frame differencing (compare consecutive frames via pixel difference) to detect motion intensity. During high-motion segments, extract frames at a shorter interval (e.g., every 1 second). During static segments, extract at a longer interval (e.g., every 4 seconds). Add a `_detect_motion()` helper and `_extract_adaptive_frames()` function. Keep the existing `_extract_frames()` as a fallback for the non-enriched path.
  - Files: `video_recipe/extractor.py` (add motion detection and adaptive extraction logic)
  - Done when: Given a 30-second video with mixed motion, adaptive extraction produces ~30% fewer total frames than uniform 2-second extraction while still capturing all distinct action segments. The function returns frames with timestamps that correctly cover the video duration.

- [ ] Task 4: Expand video format support in input handler and extractor
  - What: Update `input_handler.py` to explicitly support MP4, MOV, AVI, and YouTube URLs with proper validation for each format. Update `extractor.py` to handle format-specific quirks (e.g., MOV codec compatibility, AVI container issues) by normalizing all inputs to a consistent intermediate format (MP4 with H.264 codec) via ffmpeg before frame extraction. Add format detection and logging.
  - Files: `video_recipe/input_handler.py` (add format validation and normalization), `video_recipe/extractor.py` (add format normalization step)
  - Done when: Given a MOV or AVI file, the pipeline processes it identically to an MP4 file. The input handler validates supported formats and rejects unsupported ones with clear errors. All supported formats produce equivalent output quality.

- [ ] Task 5: Update prompts for enriched recipe generation
  - What: Update `prompts.py` to add an enriched system prompt variant that instructs the LLM to produce the enriched recipe schema (with ingredients, equipment, difficulty, estimated_time_minutes, key_takeaways). Update `build_recipe_prompt()` to optionally include enrichment instructions. Ensure the enriched prompt maintains the same temporal ordering and distinct-action guarantees as the base prompt.
  - Files: `video_recipe/prompts.py` (add enriched prompt variant), `video_recipe/enricher_prompts.py` (if created in Task 2, merge or cross-reference)
  - Done when: The enriched prompt produces LLM responses with all 5 enriched fields. The prompt explicitly instructs the LLM to infer ingredients from visual/audio evidence, estimate difficulty based on step complexity, and estimate time based on step count and descriptions.

- [ ] Task 6: Add Phase 2 tests and integration validation
  - What: Add tests in `tests/test_e2e.py` (or a new `tests/test_phase2.py`) covering: (a) `--enrich` flag parsing, (b) enriched recipe output contains all 7 fields, (c) enrichment function returns correct schema, (d) adaptive frame extraction reduces frame count by ~30%, (e) MOV/AVI format support works end-to-end, (f) non-enriched mode still works (no regression). Add pytest fixtures for test videos in multiple formats.
  - Files: `tests/test_phase2.py` (new), `tests/test_e2e.py` (append Phase 2 tests)
  - Done when: All Phase 2 tests pass. The enriched output JSON is valid and contains all required fields. Adaptive extraction test confirms ~30% frame reduction. Format support test confirms MOV/AVI/MP4 equivalence.