# Code Review — Phase 6: AI Video Generation

## Summary
Phase 6 extends the AI Movie Generation Suite with video generation capabilities. It adds:
- **Video data models** (`VideoProvider` enum, `VideoClip`, `VideoShot`, `VideoShotList`, `VideoClipManifest`) in `models.py`
- **Video provider adapter interface** (`VideoProvider` ABC) in `providers/__init__.py`
- **Dry-run video provider** (`DryRunVideoProvider`) in `providers/video_provider.py`
- **Shot list generator** (`ShotListGenerator`) in `stages/video_shot_generator.py`
- **Prompt packager** (`PromptPackager`) in `stages/prompt_packager.py`
- **Animatic timeline builder** (`AnimaticTimelineBuilder`) in `stages/animatic_builder.py`
- **Scene character renderer** (`SceneCharacterRenderer`) in `stages/scene_character_renderer.py`
- **Scene description engine** (`SceneDescriptionEngine`) in `stages/scene_description_engine.py`
- **Scene description extension** in `stages/scene_description_extension.py`
- **Mood board generator** (`MoodBoardGenerator`) in `stages/mood_board_generator.py`
- **Storyboard prompt generator** (`StoryboardPromptGenerator`) in `stages/storyboard_prompt_generator.py`
- **Character consistency engine** (`CharacterConsistencyEngine`) in `stages/character_consistency.py`
- **Character generator** (`CharacterGenerator`) in `stages/character_generator.py`
- **Beat generator** (`BeatGenerator`) in `stages/beat_generator.py`
- **Script writer** (`ScriptWriter`) in `stages/script_writer.py`
- **Project exporter** (`ProjectExporter`) in `pipeline/project_exporter.py`
- **Project manager** (`ProjectManager`) in `pipeline/project_manager.py`
- **Video generation stage** (`VideoGenerationStage`) in `stages/video_generation_stage.py`
- **Video generation pipeline** (`VideoGenerationPipeline`) in `pipeline/video_generation_pipeline.py`
- **Video generation orchestrator** (`VideoGenerationOrchestrator`) in `pipeline/video_generation_orchestrator.py`

## Blocking Bugs

### 1. All Stage Implementations Are Non-Functional (Empty Stubs)
**Severity:** BLOCKING
**Files:** All stage files in `stages/` and `pipeline/`

Every stage method returns empty results without performing any real work:

- `BeatGenerator.generate_beat_sheet()` returns a `BeatSheet` with zero beats (line ~50 of `beat_generator.py`)
- `CharacterGenerator.generate_characters()` returns an empty `CharacterRegistry` (line ~100 of `character_generator.py`)
- `ScriptWriter.write_script()` returns a `Script` with zero scenes (line ~80 of `script_writer.py`)
- `SceneDescriptionEngine.generate_scene_descriptions()` returns hardcoded values — `_generate_lighting` always returns `"natural"`, `_generate_camera_notes` always returns `"static"`, `_generate_mood` always returns `"neutral"`, `_generate_action_beats` always returns `[]` (lines ~40-70 of `scene_description_engine.py`)
- `MoodBoardGenerator.generate_mood_boards()` creates `MoodBoardReference` objects with empty `prompt`, `image_path`, and `notes` (line ~40 of `mood_board_generator.py`)
- `StoryboardPromptGenerator.generate_storyboard_prompts()` creates `SceneStoryboardPrompts` with empty `prompts` list (line ~40 of `storyboard_prompt_generator.py`)
- `CharacterConsistencyEngine.ensure_consistency()` just returns `visual_anchor` without any actual consistency checking (line ~40 of `character_consistency.py`)
- `PromptPackager.package_prompts()` generates identical prompts for all scenes — `_generate_prompt` only uses `scene_heading` and `mood`, ignoring `action`, `characters_present`, and `beat_ref` (line ~30 of `prompt_packager.py`)
- `ShotListGenerator.generate_shot_list()` uses `frame.frame_index` (int) as `segment_id` (str), causing a type mismatch (line ~40 of `video_shot_generator.py`)
- `AnimaticTimelineBuilder.build_timeline()` silently produces zero segments if `prompts` is empty (line ~30 of `animatic_builder.py`)
- `SceneCharacterRenderer.render()` is defined but never called — dead code (line ~20 of `scene_character_renderer.py`)
- `ProjectExporter.export_project()` does nothing — returns `output_dir` without writing any files (line ~20 of `project_exporter.py`)
- `VideoGenerationStage.execute()` does nothing — returns `project` unchanged (line ~20 of `video_generation_stage.py`)
- `VideoGenerationPipeline.run()` does nothing — returns `project` unchanged (line ~20 of `video_generation_pipeline.py`)
- `VideoGenerationOrchestrator.orchestrate()` does nothing — returns `project` unchanged (line ~20 of `video_generation_orchestrator.py`)

**Impact:** The entire pipeline produces empty output. A project created through this pipeline will have no beats, no characters, no script, no scenes, no descriptions, no prompts, no animatic, and no video clips.

**Fix:** Implement actual logic in each stage. At minimum:
- `BeatGenerator` should generate all 15 Save-the-Cat beats using `SAVE_THE_CAT_BEATS` template
- `CharacterGenerator` should create characters from `beat_sheet.characters_involved`
- `ScriptWriter` should generate scenes from the beat sheet
- `SceneDescriptionEngine` should vary lighting/camera/mood based on scene properties (INT/EXT, character count, etc.)
- `MoodBoardGenerator` should populate `prompt` and `notes` with scene-specific visual references
- `StoryboardPromptGenerator` should generate 1-3 frame prompts per scene
- `ShotListGenerator` should use `uuid.uuid4().hex[:8]` for `segment_id` instead of `frame_index`
- `VideoGenerationStage` should call all sub-stages in sequence

### 2. `ShotListGenerator` Uses `frame.frame_index` (int) as `segment_id` (str) — Type Mismatch
**Severity:** BLOCKING
**File:** `stages/video_shot_generator.py`, line ~40

```python
shot = VideoShot(
    segment_id=frame.frame_index,  # frame_index is int, segment_id should be str
    ...
)
```

`VideoShot.segment_id` is typed as `str` but `frame.frame_index` is `int`. This will cause a type error at runtime if Pydantic validation is enabled.

**Fix:** Use `str(frame.frame_index)` or `uuid.uuid4().hex[:8]` for `segment_id`.

### 3. `PromptPackager` Generates Identical Prompts for All Scenes
**Severity:** BLOCKING
**File:** `stages/prompt_packager.py`, `_generate_prompt` method

```python
def _generate_prompt(self, scene: Scene) -> str:
    return f"Scene: {scene.scene_heading}, Mood: {scene.mood}, Style: {self.style}"
```

This ignores `scene.action`, `characters_present`, `beat_ref`, and other scene-specific data. All scenes get the same prompt (differing only by `scene_heading` and `mood`).

**Fix:** Include `scene.action`, `characters_present`, and `beat_ref` in the prompt.

### 4. `SceneDescriptionEngine` Returns Hardcoded Values for All Scenes
**Severity:** BLOCKING
**File:** `stages/scene_description_engine.py`, all `_generate_*` methods

```python
def _generate_lighting(self, scene: Scene) -> str:
    return "natural"  # Always "natural"

def _generate_camera_notes(self, scene: Scene) -> str:
    return "static"  # Always "static"

def _generate_mood(self, scene: Scene) -> str:
    return "neutral"  # Always "neutral"

def _generate_action_beats(self, scene: Scene) -> List[str]:
    return []  # Always empty
```

All scenes get identical lighting, camera notes, mood, and action beats.

**Fix:** Vary output based on scene properties (INT/EXT for lighting, character count for camera notes, etc.).

### 5. `MoodBoardGenerator` Creates Empty Mood Board References
**Severity:** BLOCKING
**File:** `stages/mood_board_generator.py`, `generate_mood_boards` method

```python
board = MoodBoardReference(
    label=scene.scene_heading,
    prompt="",  # Empty
    image_path="",  # Empty
    notes="",  # Empty
)
```

All mood board references have empty `prompt`, `image_path`, and `notes`.

**Fix:** Populate `prompt` with scene-specific visual references and `notes` with style guidance.

### 6. `StoryboardPromptGenerator` Creates Empty Prompt Lists
**Severity:** BLOCKING
**File:** `stages/storyboard_prompt_generator.py`, `generate_storyboard_prompts` method

```python
scene_prompts = SceneStoryboardPrompts(
    scene_id=scene.scene_id,
    scene_heading=scene.scene_heading,
    target_model=self.target_model,
    beat_ref=scene.beat_ref or "",
    prompts=[],  # Always empty
)
```

**Fix:** Generate 1-3 storyboard frame prompts per scene.

### 7. `CharacterConsistencyEngine` Has No Real Implementation
**Severity:** BLOCKING
**File:** `stages/character_consistency.py`, `ensure_consistency` method

```python
def ensure_consistency(self, project: Project) -> Dict[str, str]:
    consistency = {}
    if not project.character_registry:
        return consistency
    for char in project.character_registry.characters:
        consistency[char.id] = char.visual_anchor  # Just returns visual_anchor
    return consistency
```

No actual consistency checking is performed.

**Fix:** Compare visual anchors across scenes and flag discrepancies.

### 8. `CharacterGenerator` Returns Empty Registry
**Severity:** BLOCKING
**File:** `stages/character_generator.py`, `generate_characters` method

```python
def generate_characters(self, project: Project) -> CharacterRegistry:
    registry = CharacterRegistry()
    if not project.beat_sheet:
        return registry
    return registry  # Always empty
```

**Fix:** Generate characters from `beat_sheet.characters_involved`.

### 9. `BeatGenerator` Returns Beat Sheet with Zero Beats
**Severity:** BLOCKING
**File:** `stages/beat_generator.py`, `generate_beat_sheet` method

```python
def generate_beat_sheet(self, project: Project) -> BeatSheet:
    beat_sheet = BeatSheet(
        title=project.title,
        logline=project.logline,
        genre=project.genre,
    )
    return beat_sheet  # Zero beats
```

**Fix:** Generate all 15 Save-the-Cat beats using `SAVE_THE_CAT_BEATS` template.

### 10. `ScriptWriter` Returns Script with Zero Scenes
**Severity:** BLOCKING
**File:** `stages/script_writer.py`, `write_script` method

```python
def write_script(self, project: Project) -> Script:
    script = Script(
        title=project.title,
        logline=project.logline,
        genre=project.genre,
    )
    return script  # Zero scenes
```

**Fix:** Generate scenes from the beat sheet.

### 11. `ProjectExporter.export_project()` Does Nothing
**Severity:** BLOCKING
**File:** `pipeline/project_exporter.py`, `export_project` method

```python
def export_project(self, project: Project, output_dir: Path) -> Path:
    return output_dir  # No files written
```

**Fix:** Write beat sheet, script, scene descriptions, etc. to the output directory.

### 12. `VideoGenerationStage.execute()`, `VideoGenerationPipeline.run()`, and `VideoGenerationOrchestrator.orchestrate()` All Do Nothing
**Severity:** BLOCKING
**Files:** `stages/video_generation_stage.py`, `pipeline/video_generation_pipeline.py`, `pipeline/video_generation_orchestrator.py`

All three methods return `project` unchanged without performing any work.

**Fix:** Implement actual pipeline execution — call sub-stages in sequence.

## Non-Blocking Notes

### 13. No Error Handling in Any Stage
None of the stages have try/except blocks. If any stage fails, the pipeline crashes with an unhandled exception.

### 14. No Logging in Any Stage
No logging exists anywhere in the codebase. There's no way to trace execution.

### 15. No Unit Tests for Stage Logic
Tests only cover model serialization. No tests for stage execution.

### 16. Circular Import Risk
`VoiceProvider` ABC is in `models.py`, but `providers/__init__.py` defines `VideoProvider` ABC. If any provider implementation imports from `models.py` at module level, it could cause a circular import.

### 17. `SceneCharacterRenderer.render()` Is Dead Code
Defined but never called.

### 18. `AnimaticTimelineBuilder` Produces Zero Segments if Prompts Are Empty
No fallback for missing prompts.

### 19. Inconsistent Naming
Some classes use `Collection` suffix, others use `List` suffix.

### 20. Magic Numbers
`15` for Save-the-Cat beats, `3` for storyboard frames — should be constants.

## Verdict
**FAIL** — All stage implementations are non-functional stubs that return empty results. The pipeline will produce a project with no beats, no characters, no script, no scenes, no descriptions, no prompts, no animatic, and no video clips. All blocking bugs must be fixed before this phase can be considered complete.
