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
print(paths["scenes_dir"])  # Path to 