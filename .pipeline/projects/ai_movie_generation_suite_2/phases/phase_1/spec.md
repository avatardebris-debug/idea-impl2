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