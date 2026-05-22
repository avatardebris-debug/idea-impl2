# Video Recipe Mu — Master Implementation Plan

## Idea Summary

**video_recipe_mu** takes structured scene descriptions produced by `video_scribe` and uses an LLM to extract an ordered sequence of atomic actions as a robot recipe. The output is a JSON array of steps, each containing: `step`, `action`, `object`, `xyz_delta`, `duration_s`, `preconditions`, `success_state`. Any video of a real task becomes a structured skill recipe.

---

## Architecture Overview

```
video_scribe output (scene descriptions)
        │
        ▼
┌─────────────────────┐
│  Recipe Parser       │  Loads/parses video_scribe scene descriptions
│  (JSON or Markdown)  │  into a unified intermediate representation.
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  LLM Recipe          │  Sends scene descriptions to an LLM with a
│  Extractor           │  structured prompt to produce atomic action steps.
│  (LLM-driven)        │  Handles object grounding, spatial reasoning,
└─────────────────────┘  temporal ordering, and precondition inference.
        │
        ▼
┌─────────────────────┐
│  Recipe Validator    │  Validates step ordering, checks for
│  & Normalizer        │  dangling preconditions, normalizes xyz_delta
│                      │  formats, and emits final JSON.
└─────────────────────┘
        │
        ▼
  robot_recipe.json
  [{step, action, object, xyz_delta, duration_s, preconditions, success_state}, ...]
```

---

## Dependencies on `video_scribe`

This project **consumes** (does not modify) the following from `video_scribe`:

| Module | What We Use | Why |
|--------|-------------|-----|
| `video_scribe.output_formatter.format_single_frame_markdown()` | Markdown output format | To parse video_scribe's markdown scene descriptions |
| `video_scribe.output_formatter.format_multi_scene_markdown()` | Multi-scene markdown format | To parse multi-scene video_scribe output |
| `video_scribe.output_formatter.format_single_frame_json()` | JSON output format | To parse video_scribe's JSON scene descriptions |
| `video_scribe.output_formatter.format_multi_scene_json()` | Multi-scene JSON format | To parse multi-scene video_scribe JSON output |
| `video_scribe.scene_segmenter.SceneBoundary` | Tuple[int, int, float, float] | To understand scene boundary types (start, end, score, duration) |
| `video_scribe.config.PROVIDER_GPT4O`, `PROVIDER_CLAUDE` | Provider constants | To support the same LLM providers |
| `video_scribe.vlm_analyzer.SceneAnalysis` | TypedDict: content_summary, visual_elements, camera_notes, lighting_color_notes | To understand the scene analysis data model |
| `video_scribe.context_enricher.enrich_context()` | Function returning transition descriptions + global summary | To optionally consume enriched cross-scene context |
| `video_scribe.frame_extractor.extract_key_frame()` | Function returning PIL.Image | To optionally load key frames for spatial grounding |

**Integration approach:** We will import `video_scribe` as a dependency (via `sys.path` or pip install) and use its output formatters to parse scene descriptions. We will NOT modify `video_scribe` in any way.

---

## Phase 1 — MVP: Single-Scene Recipe Extraction

**Goal:** Take a single scene description (from video_scribe) and produce a robot recipe JSON for that one scene.

**Deliverable:** A working CLI and library that:
- Accepts a video_scribe JSON or markdown scene description as input
- Sends it to an LLM with a structured prompt to extract atomic actions
- Outputs valid `robot_recipe.json` with the required schema

**Dependencies:**
- `video_scribe.output_formatter` for parsing scene descriptions
- `video_scribe.vlm_analyzer.SceneAnalysis` as the input data model
- An LLM API (OpenAI or Anthropic, same as video_scribe)

**Success Criteria:**
1. Given a video_scribe JSON scene description, the tool produces a recipe with ≥3 steps
2. Each step contains all required fields: `step`, `action`, `object`, `xyz_delta`, `duration_s`, `preconditions`, `success_state`
3. `xyz_delta` is a valid `{"x": float, "y": float, "z": float}` object
4. Steps are ordered (step numbers are sequential starting at 1)
5. CLI `--help` works and shows usage
6. End-to-end: `python video_recipe_mu.py input.json --output recipe.json` produces valid output

**Files to create:**
```
video_recipe_mu/
├── README.md
├── requirements.txt
├── video_recipe_mu/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── recipe_parser.py    # Parse video_scribe output → intermediate format
│   ├── recipe_extractor.py # LLM-driven extraction of atomic actions
│   ├── schema.py           # TypedDict for robot recipe step schema
│   └── recipe_validator.py # Validate and normalize output
├── prompts/
│   └── recipe_extraction.md  # LLM prompt template
└── tests/
    ├── __init__.py
    └── test_recipe_extraction.py  # Unit tests with mock LLM
```

---

## Phase 2 — Multi-Scene Recipe Assembly

**Goal:** Chain multiple scene descriptions into a single coherent robot recipe, resolving cross-scene transitions and shared objects.

**Deliverable:** A pipeline that:
- Accepts multi-scene video_scribe output (JSON or markdown)
- Extracts atomic actions per scene
- Merges steps across scene boundaries, deduplicating shared objects
- Resolves cross-scene preconditions (e.g., "object placed in scene N is picked up in scene N+1")
- Produces a unified `robot_recipe.json` with globally ordered steps

**Dependencies:**
- Phase 1 deliverables (recipe_parser, recipe_extractor, schema, validator)
- `video_scribe.context_enricher.enrich_context()` for cross-scene transition descriptions
- `video_scribe.scene_segmenter.SceneBoundary` for scene ordering metadata

**Success Criteria:**
1. Given multi-scene video_scribe output from a 3+ scene video, produces a recipe with ≥10 total steps
2. Cross-scene object references are correctly resolved (same object name across scenes)
3. Step ordering is globally consistent (no step references a precondition from a later step)
4. Shared objects between scenes are not duplicated as separate entities
5. Recipe preserves temporal ordering from the original video timeline
6. CLI supports `--multi-scene` flag and processes multi-scene JSON/markdown input

**Files to add/modify:**
```
video_recipe_mu/
├── video_recipe_mu/
│   ├── recipe_assembler.py   # NEW: merge multi-scene recipes
│   └── recipe_extractor.py   # MODIFIED: add multi-scene extraction mode
├── prompts/
│   └── recipe_extraction.md  # MODIFIED: add multi-scene prompt variant
└── tests/
    └── test_recipe_assembler.py  # NEW: multi-scene assembly tests
```

---

## Phase 3 — Video-to-Recipe Pipeline & Spatial Grounding

**Goal:** End-to-end pipeline: raw video → video_scribe → recipe. Add spatial grounding using key frames and coordinate estimation.

**Deliverable:** A complete pipeline that:
- Accepts a raw video file as input
- Runs video_scribe internally to produce scene descriptions
- Extracts and assembles the robot recipe
- Uses key frames for spatial grounding (estimating xyz_delta from visual cues)
- Supports both OpenAI and Anthropic LLM providers
- Includes a comprehensive test suite with synthetic video

**Dependencies:**
- Phase 1 & 2 deliverables
- `video_scribe.frame_extractor.extract_key_frame()` for spatial grounding
- `video_scribe.scene_segmenter.detect_scenes()` for scene boundary detection
- `video_scribe.vlm_analyzer.analyze_scene()` for scene analysis (optional, to bypass external API)
- `video_scribe.cache.VLMCache` for caching (optional optimization)

**Success Criteria:**
1. `python video_recipe_mu.py input.mp4 --output recipe.json` works end-to-end
2. Recipe includes spatial grounding: `xyz_delta` values are estimated from visual frame analysis
3. Supports `--provider gpt-4o` and `--provider claude` flags
4. Supports `--cache` flag to use video_scribe's VLMCache for repeated analysis
5. Test suite passes: ≥80% coverage on recipe_mu code, includes synthetic video tests
6. Recipe output is valid JSON conforming to the schema, with ≥15 total steps for a 5+ scene video
7. Precondition chains are logically consistent (no impossible action sequences)

**Files to add/modify:**
```
video_recipe_mu/
├── video_recipe_mu/
│   ├── video_pipeline.py     # NEW: end-to-end video → recipe pipeline
│   ├── spatial_grounding.py  # NEW: estimate xyz_delta from key frames
│   ├── recipe_extractor.py   # MODIFIED: add spatial grounding integration
│   └── cli.py                # MODIFIED: add --provider, --cache, --multi-scene flags
├── tests/
│   ├── test_video_pipeline.py  # NEW: end-to-end pipeline tests
│   └── test_spatial_grounding.py  # NEW: spatial grounding tests
└── requirements.txt            # MODIFIED: add any new deps
```

---

## Architecture Notes

### Data Flow
```
video_scribe output:
{
  "scene_boundaries": [[0, 5, 0.95, 5.0], ...],
  "scenes": [{
    "frame": {"content_summary": "...", "visual_elements": [...], ...},
    "transition": "..."
  }, ...]
}

Intermediate representation (recipe_parser output):
{
  "scenes": [{
    "index": 0,
    "time_range": [0, 5],
    "description": "...",
    "visual_elements": [...],
    "key_frame": "base64..."  // optional
  }],
  "global_summary": "..."
}

Final output (robot_recipe.json):
[
  {
    "step": 1,
    "action": "pick_up",
    "object": "mug",
    "xyz_delta": {"x": 0.15, "y": -0.3, "z": 0.05},
    "duration_s": 2.5,
    "preconditions": ["mug is on table"],
    "success_state": "mug is held by gripper"
  },
  ...
]
```

### LLM Prompt Strategy
- **Phase 1:** Single-scene prompt asking for atomic actions with spatial estimates
- **Phase 2:** Multi-scene prompt asking for cross-scene object tracking and merged action sequences
- **Phase 3:** Same as Phase 2 but with key frame base64 images for spatial grounding

### Schema Design
```python
class RobotRecipeStep(TypedDict):
    step: int                      # Sequential step number (1-based)
    action: str                    # Atomic action verb (pick_up, place, rotate, move_to, etc.)
    object: str                    # Object identifier (string, shared across steps)
    xyz_delta: Dict[str, float]    # {"x": float, "y": float, "z": float} in meters
    duration_s: float              # Estimated duration in seconds
    preconditions: List[str]       # List of precondition strings
    success_state: str             # State description after this step succeeds
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM fails to extract accurate spatial coordinates | High | Use key frames for spatial grounding (Phase 3); add heuristic fallback for xyz_delta estimation |
| Cross-scene object tracking is inconsistent | Medium | Use video_scribe's context_enricher for cross-scene summaries; add object name normalization in recipe_assembler |
| Recipe steps are too coarse or too fine-grained | Medium | Add configurable granularity parameter; use LLM prompt with examples of desired granularity |
| Dependency on video_scribe API changes | Low | Pin video_scribe version; write integration tests that catch API changes early |
| LLM cost for multi-scene videos | Medium | Add caching via video_scribe's VLMCache; add step count limits |

---

## Testing Strategy

1. **Unit tests:** Mock LLM responses to test recipe_parser, recipe_extractor, recipe_validator, and recipe_assembler
2. **Integration tests:** Use synthetic videos (from video_scribe's test utilities) to test end-to-end pipeline
3. **Schema validation tests:** Ensure all output conforms to the robot recipe schema
4. **CLI tests:** Test --help, --input, --output, --provider, --cache, --multi-scene flags
5. **Spatial grounding tests:** Verify xyz_delta values are reasonable given visual input

---

## Implementation Order

1. **Phase 1** (Week 1-2):
   - Create project structure and schema
   - Implement recipe_parser (parse video_scribe JSON/markdown)
   - Implement recipe_extractor (LLM prompt + extraction logic)
   - Implement recipe_validator (schema validation + normalization)
   - Implement CLI (Phase 1 flags)
   - Write unit tests with mock LLM
   - **Milestone:** Single-scene recipe extraction works end-to-end

2. **Phase 2** (Week 3-4):
   - Implement recipe_assembler (merge multi-scene recipes)
   - Add multi-scene prompt variant
   - Add cross-scene object tracking logic
   - Update CLI with --multi-scene flag
   - Write multi-scene assembly tests
   - **Milestone:** Multi-scene recipe assembly works end-to-end

3. **Phase 3** (Week 5-6):
   - Implement video_pipeline (raw video → recipe)
   - Implement spatial_grounding (key frame → xyz_delta estimation)
   - Add --provider, --cache flags to CLI
   - Write end-to-end pipeline tests with synthetic video
   - Write spatial grounding tests
   - **Milestone:** Full video-to-recipe pipeline works end-to-end
