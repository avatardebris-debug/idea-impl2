# Fix Report — Phase 2

## Current Issues
# Validation Report — Phase 2
## Summary
- Tests: 56 passed, 11 failed
## Verdict: FAIL

## Details

### Test Results
- **56 tests passed** — primarily in `tests/test_formatters.py` (18 tests) and various model/stage tests.
- **11 tests failed** across three test files:

### Failures in `tests/test_stages.py` (5 failures)
1. `TestBeatGenerator.test_generate_beat_sheet` — `BeatSheet` validation error: missing required `title` field
2. `TestBeatGenerator.test_generate_beat_sheet_with_title` — same `BeatSheet` `title` validation error
3. `TestCharacterGenerator.test_character_has_required_fields` — `Character` object has no attribute `motivation`
4. `TestScriptWriter.test_write_script` — `Beat` object has no attribute `beat_name`
5. `TestScriptWriter.test_script_has_scenes` — `Beat` object has no attribute `beat_name`

### Failures in `tests/test_models.py` (1 failure)
6. `TestProject.test_project_model_dump` — AssertionError: `'characters'` not in dumped dict keys

### Failures in `tests/test_orchestrator.py` (5 failures)
7. `TestMovieGenerationPipeline.test_pipeline_runs` — `BeatSheet` validation error: missing `title`
8. `TestMovieGenerationPipeline.test_pipeline_creates_output_files` — `BeatSheet` validation error: missing `title`
9. `TestMovieGenerationPipeline.test_pipeline_with_yaml_format` — `BeatSheet` validation error: missing `title`
10. `TestMovieGenerationPipeline.test_pipeline_with_fdx_format` — `BeatSheet` validation error: missing `title`
11. `TestMovieGenerationPipeline.test_pipeline_stages_run_in_order` — `BeatSheet` validation error: missing `title`

### Root Causes
- **`BeatSheet` model** requires a `title` field but `beat_generator.py` instantiates it without providing one.
- **`Character` model** is missing a `motivation` attribute that tests expect.
- **`Beat` model** is missing a `beat_name` attribute that `script_writer.py` and tests expect.
- **`Project` model** dump does not include a `characters` key that tests assert.

### Core Files Status
All core Phase 2 files are present:
- `ai_movie_gen_suite/models.py`
- `ai_movie_gen_suite/stages/beat_generator.py`
- `ai_movie_gen_suite/stages/character_generator.py`
- `ai_movie_gen_suite/stages/script_writer.py`
- `ai_movie_gen_suite/stages/scene_description_engine.py`
- `ai_movie_gen_suite/formatters/json_formatter.py`
- `ai_movie_gen_suite/formatters/yaml_formatter.py`
- `ai_movie_gen_suite/formatters/fdx_formatter.py`
- `ai_movie_gen_suite/pipeline/orchestrator.py`
- `ai_movie_gen_suite/cli.py`
- `ai_movie_gen_suite/config.py`
- `ai_movie_gen_suite/tests/test_all.py`
- `tests/test_formatters.py`
- `tests/test_models.py`
- `tests/test_stages.py`
- `tests/test_orchestrator.py`


## Attempt History

### Attempt 1
- **Failures**: 1 (↓ improving)
- **Previous failures**: 2

#### Test Output
```
# Validation Report — Phase 2
## Summary
- Tests: 56 passed, 11 failed
## Verdict: FAIL

## Details

### Test Results
- **56 tests passed** — primarily in `tests/test_formatters.py` (18 tests) and various model/stage tests.
- **11 tests failed** across three test files:

### Failures in `tests/test_stages.py` (5 failures)
1. `TestBeatGenerator.test_generate_beat_sheet` — `BeatSheet` validation error: missing required `title` field
2. `TestBeatGenerator.test_generate_beat_sheet_with_title` — same `BeatSheet` `title` validation error
3. `TestCharacterGenerator.test_character_has_required_fields` — `Character` object has no attribute `motivation`
4. `TestScriptWriter.test_write_script` — `Beat` object has no attribute `beat_name`
5. `TestScriptWriter.test_script_has_scenes` — `Beat` object has no attribute `beat_name`

### Failures in `tests/test_models.py` (1 failure)
6. `TestProject.test_project_model_dump` — AssertionError: `'characters'` not in dumped dict keys

### Failures in `tests/test_orchestrator.py` (5 failures)
7. `TestMovieGenerationPipeline.test_pipeline_runs` — `BeatSheet` validation error: missing `title`
8. `TestMovieGenerationPipeline.test_pipeline_creates_output_files` — `BeatSheet` validation error: missing `title`
9. `TestMovieGenerationPipeline.test_pipeline_with_yaml_format` — `BeatSheet` validation error: missing `title`
10. `TestMovieGenerationPipeline.test_pipeline_with_fdx_format` — `BeatSheet` validation error: missing `title`
11. `TestMovieGenerationPipeline.test_pipeline_stages_run_in_order` — `BeatSheet` validation error: missing `title`

### Root Causes
- **`BeatSheet` model** requires a `title` field but `beat_generator.py` instantiates it without providing one.
- **`Character` model** is missing a `motivation` attribute that tests expect.
- **`Beat` model** is missing a `beat_name` attribute that `script_writer.py` and tests expect.
- **`Project` model** dump does not include a `characters` key that tests assert.

### Core Files Status
All core Phase 2 files are present:
- `ai_movie_gen_suite/models.py`
- `ai_movie_gen_suite/stages/beat_generator.py`
- `ai_movie_gen_suite/stages/character_generator.py`
- `ai_movie_gen_suite/stages/script_writer.py`
- `ai_movie_gen_suite/stages/scene_description_engine.py`
- `ai_movie_gen_suite/formatters/json_formatter.py`
- `ai_movie_gen_suite/formatters/yaml_formatter.py`
- `ai_movie_gen_suite/formatters/fdx_formatter.py`
- `ai_movie_gen_suite/pipeline/orchestrator.py`
- `ai_movie_gen_suite/cli.py`
- `ai_movie_gen_suite/config.py`
- `ai_movie_gen_suite/tests/test_all.py`
- `tests/test_formatters.py`
- `tests/test_models.py`
- `tests/test_stages.py`
- `tests/test_orchestrator.py`

```


### Attempt 2
- **Failures**: 1 (→ stalled)
- **Previous failures**: 1

#### Test Output
```
# Validation Report — Phase 2
## Summary
- Tests: 56 passed, 11 failed
## Verdict: FAIL

## Details

### Test Results
- **56 tests passed** — primarily in `tests/test_formatters.py` (18 tests) and various model/stage tests.
- **11 tests failed** across three test files:

### Failures in `tests/test_stages.py` (5 failures)
1. `TestBeatGenerator.test_generate_beat_sheet` — `BeatSheet` validation error: missing required `title` field
2. `TestBeatGenerator.test_generate_beat_sheet_with_title` — same `BeatSheet` `title` validation error
3. `TestCharacterGenerator.test_character_has_required_fields` — `Character` object has no attribute `motivation`
4. `TestScriptWriter.test_write_script` — `Beat` object has no attribute `beat_name`
5. `TestScriptWriter.test_script_has_scenes` — `Beat` object has no attribute `beat_name`

### Failures in `tests/test_models.py` (1 failure)
6. `TestProject.test_project_model_dump` — AssertionError: `'characters'` not in dumped dict keys

### Failures in `tests/test_orchestrator.py` (5 failures)
7. `TestMovieGenerationPipeline.test_pipeline_runs` — `BeatSheet` validation error: missing `title`
8. `TestMovieGenerationPipeline.test_pipeline_creates_output_files` — `BeatSheet` validation error: missing `title`
9. `TestMovieGenerationPipeline.test_pipeline_with_yaml_format` — `BeatSheet` validation error: missing `title`
10. `TestMovieGenerationPipeline.test_pipeline_with_fdx_format` — `BeatSheet` validation error: missing `title`
11. `TestMovieGenerationPipeline.test_pipeline_stages_run_in_order` — `BeatSheet` validation error: missing `title`

### Root Causes
- **`BeatSheet` model** requires a `title` field but `beat_generator.py` instantiates it without providing one.
- **`Character` model** is missing a `motivation` attribute that tests expect.
- **`Beat` model** is missing a `beat_name` attribute that `script_writer.py` and tests expect.
- **`Project` model** dump does not include a `characters` key that tests assert.

### Core Files Status
All core Phase 2 files are present:
- `ai_movie_gen_suite/models.py`
- `ai_movie_gen_suite/stages/beat_generator.py`
- `ai_movie_gen_suite/stages/character_generator.py`
- `ai_movie_gen_suite/stages/script_writer.py`
- `ai_movie_gen_suite/stages/scene_description_engine.py`
- `ai_movie_gen_suite/formatters/json_formatter.py`
- `ai_movie_gen_suite/formatters/yaml_formatter.py`
- `ai_movie_gen_suite/formatters/fdx_formatter.py`
- `ai_movie_gen_suite/pipeline/orchestrator.py`
- `ai_movie_gen_suite/cli.py`
- `ai_movie_gen_suite/config.py`
- `ai_movie_gen_suite/tests/test_all.py`
- `tests/test_formatters.py`
- `tests/test_models.py`
- `tests/test_stages.py`
- `tests/test_orchestrator.py`

```


### Attempt 3
- **Failures**: 2 (→ stalled)
- **Previous failures**: 1

#### Test Output
```
# Validation Report — Phase 2
## Summary
- Tests: 63 passed, 4 failed
## Verdict: FAIL

### Failed Tests Detail

1. **tests/test_models.py::TestProject::test_project_model_dump**
   - Error: `AssertionError: assert 'characters' in {'beat_sheet': None, 'character_registry': None, ...}`
   - Cause: `Project.model_dump()` does not include a `characters` key in its output dict.

2. **tests/test_orchestrator.py::TestMovieGenerationPipeline::test_pipeline_stages_run_in_order**
   - Error: `AttributeError: 'dict' object has no attribute 'scenes'`
   - Cause: `results["script"]` is returned as a dict rather than a Script object with a `.scenes` attribute.

3. **tests/test_stages.py::TestBeatGenerator::test_generate_beat_sheet**
   - Error: `AssertionError: assert '' == 'Untitled'`
   - Cause: `BeatSheet.title` is an empty string instead of the expected default `"Untitled"`.

4. **tests/test_stages.py::TestCharacterGenerator::test_character_has_required_fields**
   - Error: `AttributeError: 'Character' object has no attribute 'motivation'`
   - Cause: `Character` objects generated by `CharacterGenerator` are missing the `motivation` attribute.

### Core Files Status
All core Phase 2 files are present:
- `ai_movie_gen_suite/models.py` ✓
- `ai_movie_gen_suite/stages/beat_generator.py` ✓
- `ai_movie_gen_suite/stages/character_generator.py` ✓
- `ai_movie_gen_suite/stages/script_writer.py` ✓
- `ai_movie_gen_suite/stages/scene_description_engine.py` ✓
- `ai_movie_gen_suite/pipeline/orchestrator.py` ✓
- `ai_movie_gen_suite/formatters/yaml_formatter.py` ✓
- `ai_movie_gen_suite/formatters/json_formatter.py` ✓
- `ai_movie_gen_suite/formatters/fdx_formatter.py` ✓
- `ai_movie_gen_suite/cli.py` ✓
- `ai_movie_gen_suite/config.py` ✓
- `ai_movie_gen_suite/__main__.py` ✓

### Root Causes
- **Model mismatch**: `Project.model_dump()` omits `characters` field; `Character` model lacks `motivation`.
- **Pipeline return type**: `script_writer` stage returns a dict instead of a `Script` instance.
- **Default value**: `BeatSheet` title defaults to `""` instead of `"Untitled"`.

```

