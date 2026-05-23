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
- *