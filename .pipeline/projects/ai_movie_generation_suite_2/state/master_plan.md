# AI Movie Generation Suite 2 — Master Implementation Plan

## Idea Summary

Build a multi-phase AI-powered movie generation suite that takes a logline/genre/tone as input and produces a complete screenplay with character profiles, beat sheets, scene descriptions, and formatted output — plus the infrastructure to bridge text screenplays into visual video content via external APIs.

**Core deliverable:** A production-ready screenplay generation pipeline (Phase 1) with a well-defined API surface, robust data models, and file formats that serve as the foundation for eventual video generation integration (Phases 2–3).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Layer (Typer)                   │
│  init │ generate │ edit │ regenerate │ format │ status  │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                 Project Manager                         │
│  create │ save │ load │ run_full_pipeline │ regenerate │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│              Pipeline Stages (LLM-driven)               │
│  Beat Sheet → Characters → Script → Scene Descriptions  │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│              LLM Orchestration Layer                    │
│  Provider-agnostic (OpenAI / Anthropic)                 │
│  Jinja2 prompt templates + JSON schema validation       │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                  Data Models (Pydantic)                 │
│  Project │ BeatSheet │ CharacterRegistry │ Script       │
│  Scene │ DialogueLine │ SceneDescription                │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Core Screenplay Generation Pipeline (Weeks 1–3)

**Goal:** A fully working screenplay generation tool with CLI, project management, and all four pipeline stages.

### 1.1 Data Models (`ai_movie_gen_suite/models.py`)

**Status:** ✅ Already exists. Pydantic models for all entities.

**Required:** Ensure all models have `to_dict()` methods and proper validation.

### 1.2 Configuration (`ai_movie_gen_suite/config.py`)

**Status:** ✅ Already exists. LLMConfig and AppConfig with JSON persistence.

**Required:** Ensure `use_json_mode` flag works correctly for JSON schema enforcement.

### 1.3 LLM Orchestration (`ai_movie_gen_suite/llm.py`)

**Status:** ✅ Already exists. Provider-agnostic interface.

**Required:** Add retry logic and error handling for API calls.

### 1.4 Pipeline Stages (`ai_movie_gen_suite/stages/`)

**Status:** ✅ All four stages exist:
- `beat_generator.py` — 15-beat Save-the-Cat structure
- `character_generator.py` — Character profiles
- `script_writer.py` — Full screenplay from beats + characters
- `scene_description_engine.py` — Visual direction per scene

**Required:** Ensure all stages use JSON schema validation and handle LLM errors gracefully.

### 1.5 Project Manager (`ai_movie_gen_suite/project_manager.py`)

**Status:** ✅ Exists with full pipeline and downstream regeneration.

**Required:** Add validation at each pipeline stage.

### 1.6 Formatters (`ai_movie_gen_suite/formatters/`)

**Status:** ✅ Text and FDX formats.

**Required:** Add PDF export via `fpdf` or `weasyprint`.

### 1.7 CLI (`ai_movie_gen_suite/cli.py`)

**Status:** ✅ Typer-based CLI with all commands.

**Required:** Add `--verbose` flag and better error messages.

### 1.8 Tests

**Status:** ✅ Comprehensive test suite exists.

**Required:** Add integration tests for the full pipeline.

---

## Phase 2: Visual Storyboarding & Shot Design (Weeks 4–6)

**Goal:** Bridge the gap between text screenplays and visual content by generating storyboards and shot lists.

### 2.1 Storyboard Generation

- Generate visual descriptions for each scene (composition, lighting, camera angles)
- Output as structured JSON with scene_id, shot_type, description, mood, lighting
- Support multiple shot types: wide, medium, close-up, extreme close-up, tracking, etc.

### 2.2 Shot List Generation

- Create a chronological shot list with timing estimates
- Include camera movement, lens type, and transition notes
- Output as CSV for production use

### 2.3 Visual Reference Generation

- Use DALL·E or Stable Diffusion to generate visual references for key scenes
- Store as images in the project directory
- Link back to scene descriptions

---

## Phase 3: Video Generation Integration (Weeks 7–10)

**Goal:** Integrate with external video generation APIs to produce actual visual content from screenplays.

### 3.1 Video Generation Pipeline

- Integrate with Runway ML, Pika Labs, or similar APIs
- Generate short video clips per scene
- Stitch clips into a complete video

### 3.2 Audio Generation

- Generate voiceovers for dialogue using ElevenLabs or similar
- Generate background music and sound effects
- Sync audio with video clips

### 3.3 Final Assembly

- Combine video clips, audio, and transitions
- Export as MP4 or other video formats

---

## File Format Specifications

### Project Directory Structure

```
projects/
└── {project_id}/
    ├── project.json          # Project metadata
    ├── beats.json            # Beat sheet
    ├── characters.json       # Character registry
    ├── script.json           # Screenplay data
    ├── storyboard.json       # Storyboard (Phase 2)
    ├── shot_list.csv         # Shot list (Phase 2)
    ├── scenes/
    │   └── {scene_id}/
    │       └── description.json  # Scene visual direction
    ├── output/
    │   ├── screenplay.txt    # Formatted screenplay
    │   ├── screenplay.fdx    # Final Draft export
    │   └── screenplay.pdf    # PDF export (Phase 1)
    └── assets/
        └── storyboard/       # Visual references (Phase 2)
```

### JSON Schema

- `project.json` — Top-level project container
- `beats.json` — 15-beat Save-the-Cat structure
- `characters.json` — Character profiles
- `script.json` — Screenplay with scenes and dialogue
- `storyboard.json` — Visual descriptions per scene (Phase 2)
- `description.json` — Scene-level visual direction

---

## API Surface

### CLI Commands

```bash
# Initialize a new project
ai-movie init --title "My Movie" --logline "..." --genre "drama"

# Generate the full pipeline
ai-movie generate --project-dir ./projects/my_movie

# Edit a specific element
ai-movie edit --project-dir ./projects/my_movie --type beats --beat 5 --content "New content"

# Regenerate downstream artifacts
ai-movie regenerate --project-dir ./projects/my_movie --type beats

# Format output
ai-movie format --project-dir ./projects/my_movie --output screenplay.txt

# View project status
ai-movie status --project-dir ./projects/my_movie

# Configure LLM settings
ai-movie config show
ai-movie config set llm.api_key sk-...
```

### Python API

```python
from ai_movie_gen_suite.project_manager import create_project, run_full_pipeline
from ai_movie_gen_suite.config import AppConfig
from pathlib import Path

# Create a new project
project = create_project(
    title="My Movie",
    logline="A detective must solve a murder in a small town.",
    genre="mystery",
    tone="noir",
)

# Run the full pipeline
config = AppConfig()
paths = run_full_pipeline(project, config, Path("./projects/my_movie"))

# Access artifacts
print(paths["beats"])   # Path to beats.json
print(paths["script"])  # Path to script.json
print(paths["scenes_dir"])  # Path to scenes/
```

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| LLM API rate limits | Implement retry logic with exponential backoff |
| JSON parsing errors | Add strict JSON schema validation |
| Large context windows | Chunk beat sheets and scripts for LLM input |
| Video generation quality | Start with storyboard phase, integrate video later |
| Cost management | Use cheaper models for drafting, expensive for final output |

---

## Success Criteria

### Phase 1
- [ ] CLI works for all commands
- [ ] Full pipeline generates valid screenplay from logline
- [ ] All artifacts are saved correctly
- [ ] Downstream regeneration works
- [ ] Tests pass with >80% coverage

### Phase 2
- [ ] Storyboard generation produces valid visual descriptions
- [ ] Shot list is exportable as CSV
- [ ] Visual references are generated and stored

### Phase 3
- [ ] Video clips are generated per scene
- [ ] Audio is synced with video
- [ ] Final video is exportable as MP4

---

## Next Steps

1. **Week 1:** Review and finalize Phase 1 code (data models, config, LLM layer)
2. **Week 2:** Complete pipeline stages and project manager
3. **Week 3:** CLI, formatters, and tests
4. **Week 4:** Begin Phase 2 storyboard generation
5. **Week 5:** Shot list and visual references
6. **Week 6:** Phase 2 testing and refinement
7. **Week 7:** Begin Phase 3 video generation integration
8. **Week 8:** Audio generation
9. **Week 9:** Final assembly and export
10. **Week 10:** Testing, documentation, and release
