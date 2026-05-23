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

