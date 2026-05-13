# Code Review — Phase 2

## What's Good

- **`scene_character_renderer.py`**: `SceneCharacterRenderer` has a clean public API — `render_scene()` and `render_script()` (note: spec called it `render_all_scenes`, see Non-Blocking Notes). The `_detect_present_characters` heuristic is well-documented with its multi-strategy approach (direct name, role, visual_anchor, and regex fallback). The `SceneCharacterRender` and `SceneCharacterRenderCollection` models are clean Pydantic models with proper `get_renders_for_scene()` and `to_dict()` methods.

- **`image_provider.py`**: The `CharacterImageProvider` ABC correctly defines both `generate_reference_image` and `render_character` signatures. `DummyCharacterImageProvider` is a robust test double — it generates a valid 1x1 PNG for reference images and writes descriptive text files for scene renders. `LLMCharacterImageProvider` is a well-structured placeholder for future integration.

- **`reference_sheet_generator.py`**: `ReferenceSheetGenerator.generate_for_registry()` correctly iterates over characters, generates reference images, and saves JSON profiles. The profile JSON includes all relevant character metadata.

- **`pipeline_extension.py`**: `PipelineExtension.add_character_consistency()` correctly integrates with `MovieGenerationPipeline` by setting `self.pipeline.state["character_image_provider"]`, `self.pipeline.state["reference_sheets_dir"]`, and `self.pipeline.state["generate_scene_renders"]`. The `run_character_consistency()` method correctly instantiates `ReferenceSheetGenerator` and `SceneCharacterRenderer`, and returns the collection.

- **`stages/scene_character_renderer.py`**: `SceneCharacterRendererStage` correctly wraps the renderer as a pipeline stage, building the reference-image lookup from the registry and delegating to `SceneCharacterRenderer.render_script()`.

- **`__init__.py`**: Package-level exports are clean and comprehensive, exposing all key classes.

- **`cli.py`**: The CLI correctly parses all arguments including `--generate-scene-renders` and `--output-dir`, and the `run()` function correctly instantiates the pipeline, extension, and calls `run_character_consistency()`.

- **`tests/test_scene_renderer.py`**: Comprehensive test suite with 10 tests covering all major components. Tests use `tempfile.TemporaryDirectory()` for isolation, `DummyCharacterImageProvider` for test doubles, and clear PASS/FAIL output.

## Blocking Bugs

- **`scene_character_renderer.py:100` — `render_all_scenes` method does not exist**: The spec calls for a `render_all_scenes(self, script, registry)` method, but the implementation only provides `render_script(self, script, registry)`. While `render_script()` does the same thing (iterates over all scenes), the method name mismatch means any code expecting `render_all_scenes` will fail with `AttributeError`. This is a breaking API contract violation.

- **`scene_character_renderer.py:100` — `_detect_present_characters` uses `character.role` as a string, but `Character.role` is a `str` field**: The code does `if character.role in action_text` which works because `role` is a `str`. However, the docstring says "role" and the implementation treats it as a string — this is fine but the docstring should clarify that `role` is matched as a substring.

- **`stages/scene_character_renderer.py:48` — `SceneCharacterRendererStage.execute()` does not store results on pipeline state**: The spec says the stage should "store results on the pipeline state." The current implementation returns the collection but does not store it in `self.pipeline.state` (which is not even accessible from the stage — the stage only has `script`, `registry`, `provider`, and `output_dir`). The stage should either accept a pipeline state dict or store results on a passed-in state object.

- **`pipeline_extension.py:30` — `add_character_consistency` does not validate that `provider` is a `CharacterImageProvider`**: The method accepts any object as `provider` without type checking. If a non-provider object is passed, errors will only surface later during `generate_reference_image` calls. A type check or `isinstance` guard would be more robust.

- **`pipeline_extension.py:45` — `run_character_consistency` does not check if `generate_scene_renders` was set**: The method always runs scene rendering regardless of the `generate_scene_renders` flag set by `add_character_consistency`. The flag is stored in `self.pipeline.state` but never read back. The method should check `self.pipeline.state.get("generate_scene_renders", False)` before rendering scenes.

- **`tests/test_scene_renderer.py:100` — Test 5 and Test 10 use `MockPipeline` with `state = {}` as a class attribute**: This is a shared mutable default. If any test modifies `MockPipeline.state`, it affects all subsequent tests. Each test should create its own `MockPipeline` instance with a fresh `state = {}`.

## Non-Blocking Notes

- **`scene_character_renderer.py:100` — `render_script` vs `render_all_scenes` naming**: Consider renaming `render_script` to `render_all_scenes` to match the spec, or add an alias `render_all_scenes = render_script`.

- **`scene_character_renderer.py:100` — `_detect_present_characters` regex fallback is fragile**: The regex `re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)` will match any word boundary occurrence of the character name. This could produce false positives (e.g., "Bob" matching "Bobby"). Consider adding a confidence score or requiring multiple signals.

- **`reference_sheet_generator.py:68` — `character.role.value` check is unnecessary**: `Character.role` is defined as `str` in `ai_movie_gen_suite.models`, so `hasattr(character.role, 'value')` will always be False. The `str(character.role)` fallback is sufficient.

- **`cli.py:30` — `run()` function does not handle exceptions**: If any stage fails (e.g., image generation error), the CLI will crash with an unhandled exception. Consider wrapping the main logic in a try/except with a user-friendly error message.

- **`tests/test_scene_renderer.py` — Test 6 imports `parse_args` from `ai_consistent_char.cli`**: This works because `sys.path.insert(0, str(pathlib.Path(__file__).parent))` adds the workspace directory. However, this is fragile — if the test is run from a different directory, it will fail. Consider using a proper test framework like `pytest` with `conftest.py` for path management.

- **`stages/__init__.py` — Empty**: The file exists but is empty. It should export `SceneCharacterRendererStage` for convenience.

- **`image_provider.py` — `DummyCharacterImageProvider.render_character` uses `time.time()` for filename**: This means the same character in the same scene will produce different filenames on repeated runs. For testing, this is fine, but for reproducibility, consider using a hash of the inputs.

## Verdict

FAIL — The `render_script`/`render_all_scenes` naming mismatch is a breaking API contract violation. The `PipelineExtension` does not respect the `generate_scene_renders` flag. The `SceneCharacterRendererStage` does not store results on pipeline state as specified. The `MockPipeline.state` class attribute is a shared mutable default that can cause test interference.
