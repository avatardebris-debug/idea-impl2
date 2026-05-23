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

