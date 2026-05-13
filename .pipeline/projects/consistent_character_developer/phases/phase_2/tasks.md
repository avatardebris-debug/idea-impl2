# Phase 2 Tasks

- [ ] Task 1: Build `SceneCharacterRenderer` and supporting models
  - What: Create `SceneCharacterRenderer` class that generates per-scene character renders by injecting reference images into the image-generation provider. Also create `SceneCharacterRender` and `SceneCharacterRenderCollection` data models to hold render results.
  - Files: `consistent_character_developer/ai_consistent_char/scene_character_renderer.py` (new), `consistent_character_developer/ai_consistent_char/models.py` (append `SceneCharacterRender` and `SceneCharacterRenderCollection`)
  - Done when: `SceneCharacterRenderer` accepts a `CharacterImageProvider`, `{char_id: ref_image_path}` dict, and output dir; `render_scene` returns a list of `SceneCharacterRender` objects with correct scene/character mapping; `render_all_scenes` returns a `SceneCharacterRenderCollection` with all scenes processed; unit tests pass for initialization, single-character scene, multi-character scene, and reference-image-path injection verification.

- [ ] Task 2: Build `SceneDescriptionEngineExtension`
  - What: Create a wrapper/extension class that composes a base `SceneDescriptionEngine` with a `SceneCharacterRenderer` so that scene descriptions and character renders are produced together. The extension should call the base engine for descriptions, then invoke the renderer to attach per-scene character render paths to each `SceneDescription`.
  - Files: `consistent_character_developer/ai_consistent_char/stages/scene_description_engine_extension.py` (new)
  - Done when: `SceneDescriptionEngineExtension.generate_descriptions()` returns a `SceneDescriptionCollection` where each scene description has an attached list of character render paths; the base engine is called once per scene; unit tests verify that descriptions are generated and renders are attached correctly.

- [ ] Task 3: Build `PipelineExtension` — insert scene renderer into `MovieGenerationPipeline`
  - What: Create a `PipelineExtension` class that wires the new stages into the existing `MovieGenerationPipeline`. It should add a `generate_scene_renders` config flag, insert the `SceneDescriptionEngineExtension` stage between script writing and formatting, and ensure the pipeline can run end-to-end with scene renders enabled or disabled.
  - Files: `consistent_character_developer/ai_consistent_char/pipeline_extension.py` (new)
  - Done when: Pipeline can be instantiated with scene renders enabled; the renderer stage is inserted at the correct position; when `generate_scene_renders=False` the pipeline behaves identically to the original; integration tests verify the full pipeline path (logline → beats → characters → reference images → scene descriptions with renders).

- [ ] Task 4: Update CLI to support scene render generation
  - What: Extend the existing CLI (`consistent_character_developer/ai_consistent_char/cli.py`) with a `--generate-scene-renders` flag (default False) and a `--skip-scene-renders` alias. When enabled, the CLI should invoke the `PipelineExtension` with scene renders turned on and log progress for each scene rendered.
  - Files: `consistent_character_developer/ai_consistent_char/cli.py` (new — does not yet exist, create it)
  - Done when: CLI accepts `--generate-scene-renders` flag; passing it triggers the scene render pipeline; CLI prints per-scene progress; CLI works end-to-end with a mock provider (placeholder PNGs).

- [ ] Task 5: Write unit tests for `SceneCharacterRenderer`
  - What: Create comprehensive unit tests covering renderer initialization, single-character scene rendering, multi-character scene rendering, reference image path injection verification, and the `SceneCharacterRenderCollection` data structure.
  - Files: `consistent_character_developer/tests/test_scene_renderer.py` (new)
  - Done when: All seven test cases from the Phase 2 spec pass: `test_scene_renderer_initialization`, `test_render_scene_single_character`, `test_render_scene_multiple_characters`, `test_reference_image_injected`, `test_render_all_scenes`, `test_collection_contains_all_renders`; tests use mock providers (no real API calls).

- [ ] Task 6: Write integration tests for the full pipeline with scene renders
  - What: Create integration tests that exercise the full pipeline from logline through beat sheet, character generation, reference image generation, scene description + render generation, and output formatting. Use mock providers and placeholder images.
  - Files: `consistent_character_developer/tests/test_full_pipeline.py` (new)
  - Done when: `test_full_pipeline_with_scene_renders` passes end-to-end; the pipeline produces a `SceneCharacterRenderCollection` with correct scene-to-renders mapping; tests pass with `generate_scene_renders=True` and with `generate_scene_renders=False` (verifying no regression).