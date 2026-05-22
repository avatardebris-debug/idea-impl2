# Code Review — Phase 4 (Storyboard to Animatic)

## Review Date
2025-01-01

## Verdict
PASS

---

## Summary
Phase 4 implements the transition from storyboard frames to a timed animatic sequence. The implementation includes:

1. **Animatic Timeline Builder** (`ai_movie_gen_suite/stages/animatic_builder.py`) — Maps storyboard frames to timed segments with transitions and beat alignment.
2. **Pacing Engine** — Calculates hold times per frame from dialogue length, action beats, and genre/tone presets.
3. **Preview Manifest** (`animatic/preview_manifest.json`) — Exports structured frame data with start/end times.
4. **Pipeline Integration** — The orchestrator (`pipeline/orchestrator.py`) calls `export_phase4()` on `ProjectExporter` to produce animatic artifacts.

---

## Blocking Bugs
None.

---

## Issues Found

### Severity: Low

#### 1. Hardcoded constants in `animatic_builder.py`
- **File:** `ai_movie_gen_suite/stages/animatic_builder.py`
- **Line:** ~14-16
- **Issue:** `BASE_FRAME_MS = 2500`, `MS_PER_DIALOGUE_LINE = 1200`, and `MOOD_DURATION_MODIFIER` are hardcoded module-level constants. These should be configurable via `PipelineConfig` or a dedicated `AnimaticConfig` class to allow tuning per project.
- **Recommendation:** Extract to a config class or allow override via pipeline config.

#### 2. UUID generation uses `uuid.uuid4()` without deterministic seed
- **File:** `ai_movie_gen_suite/stages/animatic_builder.py`
- **Line:** ~70+
- **Issue:** Segment IDs use `uuid.uuid4()` which produces non-deterministic IDs. This is fine for production but makes testing/reproducibility harder.
- **Recommendation:** Consider a deterministic ID scheme (e.g., `SEG-{scene_id}-{frame_index}`) for testability, or document that IDs are intentionally random.

#### 3. `export_phase4` in `ProjectExporter` assumes `storyboards` dict has `SceneStoryboardPrompts` values
- **File:** `ai_movie_gen_suite/pipeline/project_exporter.py`
- **Issue:** The method iterates over `storyboards.items()` and accesses `.storyboard_prompt` on each value. If any value is not a `SceneStoryboardPrompts` instance, this will raise `AttributeError`.
- **Recommendation:** Add a type guard or `isinstance` check before accessing attributes.

#### 4. No validation that `total_duration_ms` in timeline matches sum of segment durations
- **File:** `ai_movie_gen_suite/stages/animatic_builder.py`
- **Issue:** `total_duration_ms` is computed as `sum(seg.duration_ms for seg in segments)` but there is no assertion or validation that this matches the manifest's `total_duration_ms`.
- **Recommendation:** Add an assertion or validation step to ensure consistency between timeline and manifest.

### Severity: Informational

#### 5. `AnimaticTimeline` model does not validate segment ordering
- **File:** `ai_movie_gen_suite/models.py`
- **Issue:** Segments in `AnimaticTimeline` are stored as a list without enforced ordering by `frame_index` or `start_ms`.
- **Recommendation:** Add a validator that sorts segments by `frame_index` or `start_ms` on assignment.

#### 6. Audio cues do not validate against segment IDs
- **File:** `ai_movie_gen_suite/stages/animatic_builder.py`
- **Issue:** `AnimaticAudioCues` stores cues by segment ID but there is no cross-reference validation that every cue's `segment_id` exists in the timeline.
- **Recommendation:** Add a validation step that checks all cue segment IDs exist in the timeline.

---

## Non-Blocking Notes

### Positive Observations
- The animatic builder correctly chains from storyboard prompts through to timeline segments.
- The `AnimaticTransition` enum provides a clean set of transition types (cut, dissolve, fade, wipe).
- The preview manifest (`preview_manifest.json`) correctly computes `start_ms` and `end_ms` for each frame.
- Pipeline integration via `export_phase4()` in `ProjectExporter` is clean and well-scoped.
- All 106 tests pass with 0 failures and 0 errors.

### Code Quality
- Type hints are used consistently.
- Pydantic models are used appropriately for data validation.
- The code follows the project's existing patterns (e.g., `__future__` annotations, logging).

---

## Test Coverage
- **Tests run:** 106 passed, 0 failed, 0 errors
- **Phase 4-specific tests:** `test_pipeline.py` includes `TestPipelineIntegration` which exercises the full pipeline including animatic export. `test_orchestrator.py` includes `test_pipeline_exports_visual_and_animatic`.
- **Coverage gap:** No dedicated unit tests for `AnimaticTimelineBuilder.build_timeline()` or `AnimaticTimelineBuilder.build_audio_cues()` directly. The animatic builder is tested indirectly through the pipeline integration tests.

---

## Final Verdict: PASS
Phase 4 meets its acceptance criteria:
- ✅ `animatic/timeline.json` exports structured segments with duration, transition, and beat refs
- ✅ `animatic/audio_cues.json` provides pacing cues per segment
- ✅ `animatic/preview_manifest.json` exports frame-level timing data
- ✅ Pipeline integration via orchestrator works correctly
- ✅ All 106 tests pass

The issues identified are all low-severity and informational. No blocking bugs remain.
