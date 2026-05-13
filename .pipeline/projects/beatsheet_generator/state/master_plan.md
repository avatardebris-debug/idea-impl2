# Beatsheet Generator — Master Implementation Plan

## 1. Idea Analysis

**Core Deliverable:** A standalone `beatsheet_generator` project that takes a movie idea (title, genre, logline) — optionally sourced from the `movie_idea_generator` — and produces a complete **Save-the-Cat 15-beat sheet** with rich, context-aware descriptions, character involvement per beat, phase assignments, and estimated page ranges. The output must be a `BeatSheet` object compatible with the existing `ai_movie_gen_suite` data models and JSON schema, ready to feed downstream stages (character generation, script writing, scene descriptions).

**Key insight:** The `ai_movie_gen_suite` already has a `BeatGenerator` class in `ai_movie_gen_suite/stages/beat_generator.py` and `BeatSheet`/`Beat` models in `ai_movie_gen_suite/models.py`. This project does NOT reimplement beatsheet logic — it **wraps and extends** it, providing a polished, standalone CLI/API that bridges `movie_idea_generator` output into `ai_movie_gen_suite`'s beat generation pipeline.

---

## 2. Architecture Overview

```
movie_idea_generator          beatsheet_generator          ai_movie_gen_suite
───────────────────           ──────────────────           ──────────────────
MovieIdeaGenerator  ──────►   BeatSheetService    ──────►  BeatGenerator
  .generate()              │    (new class)           .generate_beat_sheet()
                           │    .generate()              (from models.py)
                           │    .save_to_file()          (BeatSheet, Beat)
                           │                            BeatSheet (pydantic)
                           │                            Beat (pydantic)
                           │                            SAVE_THE_CAT_BEATS
                           │                            BeatPhase
                           │                            DEFAULT_BEAT_TEMPLATES
```

### Dependency Mapping

| Dependency | Import Path | What We Use |
|---|---|---|
| `ai_movie_gen_suite.models` | `ai_movie_gen_suite.models` | `BeatSheet`, `Beat`, `BeatPhase`, `SAVE_THE_CAT_BEATS`, `CharacterRole` |
| `ai_movie_gen_suite.stages.beat_generator` | `ai_movie_gen_suite.stages.beat_generator` | `BeatGenerator` class, `DEFAULT_BEAT_TEMPLATES` |
| `ai_movie_gen_suite.formatters.json_formatter` | `ai_movie_gen_suite.formatters.json_formatter` | `JSONFormatter` (for saving beat sheets) |
| `ai_movie_gen_suite.pipeline.orchestrator` | `ai_movie_gen_suite.pipeline.orchestrator` | `PipelineConfig`, `MovieGenerationPipeline` (optional integration) |
| `movie_idea_generator.generator` | `movie_idea_generator.generator` | `MovieIdeaGenerator` class, `MovieIdeaGenerator.generate()` |

### Project Structure

```
beatsheet_generator/
├── workspace/
│   ├── beatsheet_generator/
│   │   ├── __init__.py          # Expose BeatSheetService, CLI entry
│   │   ├── service.py           # BeatSheetService — core orchestration
│   │   ├── cli.py               # CLI entry point
│   │   └── models.py            # Local dataclasses (thin wrappers, if needed)
│   ├── pyproject.toml
│   └── tests/
│       ├── __init__.py
│       ├── test_service.py
│       ├── test_cli.py
│       └── test_integration.py
└── state/
    └── master_plan.md           # This file
```

---

## 3. Implementation Details

### 3.1 `BeatSheetService` (`service.py`)

The heart of the project. A single class that:

1. **Accepts input** in two forms:
   - A `dict` from `movie_idea_generator` (keys: `title`, `genre`, `logline`, `characters`)
   - Raw strings: `title`, `genre`, `logline` (optional `characters` list)

2. **Generates the beat sheet** by:
   - Instantiating `BeatGenerator` from `ai_movie_gen_suite.stages.beat_generator`
   - Calling `beat_generator.generate_beat_sheet(logline, genre, title=title, characters=characters)`
   - Returning the `BeatSheet` pydantic model

3. **Formats and saves** output:
   - Uses `JSONFormatter` from `ai_movie_gen_suite.formatters.json_formatter` to serialize
   - Saves to a configurable output path

4. **Provides a `generate()` method** returning a dict with:
   ```python
   {
       "beat_sheet": BeatSheet,           # pydantic model
       "beat_sheet_json": str,            # JSON string
       "beat_sheet_dict": dict,           # serializable dict
       "output_path": str | None,         # if saved
       "title": str,
       "genre": str,
       "num_beats": int,
   }
   ```

### 3.2 CLI (`cli.py`)

Entry point `beatsheet-gen` with:

```
beatsheet-gen \
  --title "The Last Horizon" \
  --genre "Sci-Fi" \
  --logline "In 2087, a lone astronaut discovers a wormhole that changes everything." \
  --output ./output.json \
  --format json
```

Optional flags:
- `--source-movie-idea /path/to/idea.json` — load idea from `movie_idea_generator` output
- `--seed N` — pass seed to `MovieIdeaGenerator` if generating from scratch
- `--count N` — generate N ideas, then pick one (or all) for beat sheets

### 3.3 `pyproject.toml`

```toml
[project]
name = "beatsheet-generator"
version = "0.1.0"
dependencies = [
    "movie-idea-generator",
    "ai-movie-gen-suite",
]

[project.scripts]
beatsheet-gen = "beatsheet_generator.cli:main"
```

---

## 4. Tests

### `test_service.py`
- `test_generate_beat_sheet_from_strings` — pass title/genre/logline, verify 15 beats returned
- `test_generate_beat_sheet_from_idea_dict` — pass movie idea dict, verify beats match
- `test_save_to_file` — verify file is written and contains valid JSON
- `test_invalid_genre_raises` — pass empty genre, verify error

### `test_cli.py`
- `test_cli_generates_beat_sheet` — run CLI with `--title`, `--genre`, `--logline`, verify output
- `test_cli_json_format` — verify JSON output is valid
- `test_cli_source_movie_idea` — load from idea JSON, verify beats generated

### `test_integration.py`
- `test_end_to_end_movie_idea_to_beat_sheet` — generate idea via `MovieIdeaGenerator`, pass to `BeatSheetService`, verify output
- `test_pipeline_integration` — verify beat sheet feeds into `ai_movie_gen_suite` models correctly

---

## 5. File Manifest

| File | Purpose |
|---|---|
| `workspace/beatsheet_generator/__init__.py` | Package init, expose `BeatSheetService`, `main` |
| `workspace/beatsheet_generator/service.py` | `BeatSheetService` class — core logic |
| `workspace/beatsheet_generator/cli.py` | CLI entry point |
| `workspace/beatsheet_generator/models.py` | (Empty/minimal — reuse suite models) |
| `workspace/pyproject.toml` | Project config, dependencies |
| `workspace/tests/__init__.py` | Test package init |
| `workspace/tests/test_service.py` | Unit tests for `BeatSheetService` |
| `workspace/tests/test_cli.py` | Unit tests for CLI |
| `workspace/tests/test_integration.py` | Integration tests |

---

## 6. Implementation Steps

### Step 1: Scaffold the project
- Create directory structure
- Write `pyproject.toml` with dependencies on `movie-idea-generator` and `ai-movie-gen-suite`
- Create empty `__init__.py` and `models.py`

### Step 2: Implement `BeatSheetService` (`service.py`)
- Import `BeatGenerator` from `ai_movie_gen_suite.stages.beat_generator`
- Import `BeatSheet`, `Beat` from `ai_movie_gen_suite.models`
- Import `JSONFormatter` from `ai_movie_gen_suite.formatters.json_formatter`
- Implement `__init__(self, title: str, genre: str, logline: str, characters: list[dict] | None = None)`
- Implement `generate(self) -> dict` — calls `BeatGenerator`, returns structured result
- Implement `save_to_file(self, filepath: str) -> str` — uses `JSONFormatter`

### Step 3: Implement CLI (`cli.py`)
- Parse args: `--title`, `--genre`, `--logline`, `--output`, `--format`, `--source-movie-idea`, `--seed`, `--count`
- If `--source-movie-idea` provided, load JSON and extract title/genre/logline/characters
- Otherwise, use raw args
- Call `BeatSheetService`, display/save output

### Step 4: Write tests
- `test_service.py`: 4 tests (strings input, dict input, save, invalid genre)
- `test_cli.py`: 3 tests (basic CLI, JSON format, source movie idea)
- `test_integration.py`: 2 tests (end-to-end movie idea → beat sheet, pipeline integration)

### Step 5: Final review
- Verify all imports resolve correctly
- Ensure output is compatible with `ai_movie_gen_suite` schemas
- Confirm CLI works standalone and with `movie_idea_generator`
