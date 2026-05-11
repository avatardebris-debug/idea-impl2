# Phase 2 Code Review

## Overview

Phase 2 implements the **Storyboard, Shot List, and Visual Reference Generation** pipeline stages. This review covers the code quality, correctness, completeness, and adherence to the Phase 2 specification.

---

## 1. Architecture & Design

### Strengths

1. **Consistent Stage Pattern**: All stages (`StoryboardGenerator`, `AudioCuesGenerator`, `SoundDesignGenerator`, `MusicThemesGenerator`, `SceneDescriptionGenerator`, `SummaryGenerator`) follow the same `BaseStageGenerator` pattern with `execute(project) -> Project`. This makes the pipeline easy to extend.

2. **Prompt Library Abstraction**: The `PromptLibrary` class in `prompts/prompt_library.py` provides a clean, centralized way to manage prompt templates. Templates are registered once and rendered with variable substitution. This avoids prompt string duplication across stages.

3. **Model-Driven Design**: The `models.py` file defines clear Pydantic models (`Project`, `SceneDescription`, `Beat`, `Character`, `Script`, `BeatSheet`) with validation. This ensures data integrity throughout the pipeline.

4. **Separation of Concerns**: The pipeline is cleanly separated into:
   - `pipeline.py` — orchestration
   - `stages/` — individual stage logic
   - `prompts/` — prompt templates
   - `models/` — data models
   - `formatters/` — output formatting
   - `llm_client.py` — LLM interaction

### Issues

1. **Missing Phase 2 Deliverables**: The Phase 2 spec explicitly requires:
   - **Shot List Generation** (CSV output with shot_number, scene_number, shot_type, camera_angle, camera_movement, composition, visual_effects, audio_cues, duration, transitions, description)
   - **Visual Reference Generation** (image generation for each storyboard frame)
   
   Neither of these exists in the current codebase. The `StoryboardGenerator` generates JSON storyboard frames but does not produce a CSV shot list or generate images. This is a **critical gap** in Phase 2 completion.

2. **Duplicate Prompt Definitions**: The `prompts.py` file and `prompts/prompt_library.py` both define prompt templates. The `prompt_library.py` is the active one (used by stages), but `prompts.py` is not imported anywhere. This creates confusion and maintenance burden. One source of truth should be established.

3. **`summary_generator.py` References Non-Existent Template**: The `SummaryGenerator` uses the `"summary"` prompt template, but this template is defined in `prompts.py` (not in `prompt_library.py`). Since stages import from `prompt_library`, this will cause a `KeyError` at runtime.

---

## 2. Code Quality

### Strengths

1. **Type Hints**: All functions and methods have proper type hints. This improves IDE support and catch errors early.

2. **Docstrings**: Every class and method has descriptive docstrings explaining purpose, parameters, and return values.

3. **Error Handling**: Stages validate input data before processing (e.g., checking for `script` or `scenes` before generation).

4. **Logging**: Appropriate use of `logging` throughout for observability.

### Issues

1. **Magic Strings**: Prompt template names like `"beat_generator"`, `"scene_description"`, `"storyboard"` are hardcoded as strings. If a template name is misspelled, the error only surfaces at runtime. Consider using an `Enum` for template names.

2. **JSON Parsing Fragility**: The `_parse_json_response` method in `BaseStageGenerator` strips markdown code fences but doesn't handle other common LLM output issues (e.g., trailing commas, single quotes, extra text). This could cause silent failures or crashes with certain LLM outputs.

3. **No Retry Logic**: If an LLM call fails or returns invalid JSON, there's no retry mechanism. The pipeline will crash. For a production system, retries with exponential backoff should be implemented.

4. **`_validate_project_data` Unused**: The `BaseStageGenerator._validate_project_data` method is defined but never called by any stage. Each stage manually checks for required data instead. This dead code should be removed or used consistently.

---

## 3. Stage-by-Stage Review

### `storyboard_generator.py`

**Status**: Partially complete for Phase 2.

- ✅ Generates storyboard frames from scene descriptions
- ✅ Uses proper prompt template
- ✅ Returns JSON with frame data
- ❌ **Does not generate CSV shot list** (Phase 2 requirement)
- ❌ **Does not generate visual reference images** (Phase 2 requirement)
- ⚠️ The `frames` array structure matches the prompt template but there's no validation that the LLM output matches the expected schema

### `audio_cues_generator.py`

**Status**: Complete.

- ✅ Generates audio cues per scene
- ✅ Uses proper prompt template
- ✅ Returns structured JSON data

### `sound_design_generator.py`

**Status**: Complete.

- ✅ Generates overall sound design
- ✅ Uses proper prompt template
- ✅ Returns structured JSON data

### `music_themes_generator.py`

**Status**: Complete.

- ✅ Generates music themes
- ✅ Uses proper prompt template
- ✅ Returns structured JSON data

### `scene_description_generator.py`

**Status**: Complete.

- ✅ Generates visual scene descriptions
- ✅ Uses proper prompt template
- ✅ Returns structured JSON data with all required fields

### `summary_generator.py`

**Status**: **Broken** — will crash at runtime.

- ❌ References `"summary"` template which exists in `prompts.py` but not in `prompt_library.py`
- ❌ The `Project` model does not have a `summary` field — this will cause a Pydantic validation error when setting `project.summary = data`
- ⚠️ The template in `prompts.py` expects `synopsis` but the generator passes `synopsis` from `beat_sheet` which may not exist

---

## 4. Pipeline Integration

### Strengths

1. **Pipeline Orchestration**: `pipeline.py` correctly chains all stages in order.
2. **Status Tracking**: Each stage updates `project.status` appropriately.
3. **Error Handling**: The pipeline catches exceptions and sets status to `"error"`.

### Issues

1. **No Stage Skipping**: If a stage fails, the pipeline stops. There's no way to resume from a specific stage. For iterative development, stage skipping/resumption would be valuable.

2. **No Progress Tracking**: The pipeline doesn't track which stages have been completed. If the pipeline is restarted, it will re-run all stages.

3. **`summary_generator` Not in Pipeline**: Looking at `pipeline.py`, the `SummaryGenerator` is imported but **not added to the pipeline stages list**. The pipeline ends at `SceneDescriptionGenerator`. This means the summary stage is never executed.

---

## 5. Data Model Issues

### `Project` Model

- ✅ Has all core fields
- ✅ Has validation for `title`
- ❌ **Missing `summary` field** — `SummaryGenerator` tries to set `project.summary` but this field doesn't exist in the model
- ❌ **Missing `shot_list` field** — Phase 2 requires shot list output but there's no field to store it
- ❌ **Missing `visual_references` field** — Phase 2 requires visual reference output but there's no field to store it

### `SceneDescription` Model

- ✅ Well-defined with all required fields
- ✅ Has proper validation

---

## 6. Missing Phase 2 Requirements

| Requirement | Status | Notes |
|------------|--------|-------|
| Storyboard Generation | ✅ Partial | JSON frames generated but no CSV shot list |
| Shot List CSV Generation | ❌ Missing | No `ShotListGenerator` or CSV output |
| Visual Reference Generation | ❌ Missing | No image generation (e.g., via Stable Diffusion, DALL-E) |
| Audio Cues Generation | ✅ Complete | |
| Sound Design Generation | ✅ Complete | |
| Music Themes Generation | ✅ Complete | |
| Scene Description Generation | ✅ Complete | |
| Summary Generation | ❌ Broken | Template mismatch + missing model field |

---

## 7. Recommendations

### Critical (Must Fix Before Phase 2 Completion)

1. **Add Shot List CSV Generation**: Create a `ShotListGenerator` stage that:
   - Takes storyboard frames as input
   - Converts them to CSV format with columns: `shot_number`, `scene_number`, `shot_type`, `camera_angle`, `camera_movement`, `composition`, `visual_effects`, `audio_cues`, `duration`, `transitions`, `description`
   - Writes to `output/shot_list.csv`

2. **Add Visual Reference Generation**: Create a `VisualReferenceGenerator` stage that:
   - Takes storyboard frames as input
   - Generates images using an image generation API (e.g., DALL-E, Stable Diffusion)
   - Saves images to `output/visual_references/`
   - Stores image paths in the project data

3. **Fix `SummaryGenerator`**:
   - Add `"summary"` template to `prompt_library.py`
   - Add `summary: Optional[Dict[str, Any]]` field to `Project` model
   - Add `SummaryGenerator` to the pipeline stages list

### Important (Should Fix)

4. **Consolidate Prompt Definitions**: Remove `prompts.py` and use only `prompt_library.py` as the single source of truth for prompts.

5. **Add Template Name Enum**: Create `PromptTemplateName` enum to prevent typos in template names.

6. **Add JSON Response Validation**: Add schema validation for LLM responses to catch malformed output early.

7. **Add Retry Logic**: Implement retry with exponential backoff for LLM calls.

### Nice to Have

8. **Stage Resumption**: Allow the pipeline to resume from a specific stage.

9. **Progress Tracking**: Track completed stages to avoid re-processing.

10. **Unit Tests**: Add tests for each stage, the pipeline, and the prompt library.

---

## 8. Summary

**Overall Assessment**: Phase 2 code is **partially complete**. The core architecture is solid and well-designed, but critical Phase 2 deliverables (shot list CSV generation and visual reference image generation) are missing. Additionally, the `SummaryGenerator` is broken due to template/model mismatches.

**Priority Actions**:
1. Implement shot list CSV generation
2. Implement visual reference image generation
3. Fix `SummaryGenerator`
4. Consolidate prompt definitions
5. Add missing `Project` model fields

**Estimated Effort**: 2-3 days to complete the missing Phase 2 requirements and fix the identified issues.
