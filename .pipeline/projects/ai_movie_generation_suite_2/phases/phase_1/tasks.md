# Phase 1 Tasks

- [ ] Task 1: Data Models — Pydantic entities with validation and serialization
  - What: Create all Pydantic data models with `to_dict()` methods, proper field validation, and type hints. Models: Project, BeatSheet, Beat, CharacterRegistry, CharacterProfile, Script, Scene, DialogueLine, SceneDescription.
  - Files: ai_movie_gen_suite/models.py
  - Done when: All models instantiate correctly, `to_dict()` round-trips produce valid JSON, Pydantic validation rejects invalid data (e.g., negative beat number, missing required fields), and all models have proper docstrings.

- [ ] Task 2: Configuration — LLMConfig and AppConfig with JSON persistence
  - What: Build LLMConfig (provider, api_key, model, use_json_mode, temperature, max_tokens) and AppConfig (project_dir, output_dir, verbose) with save/load via JSON files. Ensure `use_json_mode` flag is wired into the LLM layer for JSON schema enforcement.
  - Files: ai_movie_gen_suite/config.py
  - Done when: Config objects serialize/deserialize correctly via JSON, `use_json_mode` defaults to True, missing API key raises a clear error, and config persistence survives restart.

- [ ] Task 3: LLM Orchestration — Provider-agnostic interface with retry logic and error handling
  - What: Implement a provider-agnostic LLM client supporting OpenAI and Anthropic. Add retry logic with exponential backoff (3 retries, configurable), timeout handling, and JSON response parsing. Use Jinja2 for prompt templating.
  - Files: ai_movie_gen_suite/llm.py
  - Done when: Both OpenAI and Anthropic providers can be instantiated and called, retries trigger on 429/5xx errors and succeed on retry, invalid JSON responses are caught with descriptive errors, and prompt templates render correctly via Jinja2.

- [ ] Task 4: Pipeline Stages — Four LLM-driven stages with JSON schema validation
  - What: Implement the four pipeline stages: (1) beat_generator.py — generates 15-beat Save-the-Cat structure from logline, (2) character_generator.py — generates character profiles from beats, (3) script_writer.py — writes full screenplay from beats + characters, (4) scene_description_engine.py — generates visual direction per scene. Each stage must validate LLM output against Pydantic JSON schemas and handle errors gracefully.
  - Files: ai_movie_gen_suite/stages/beat_generator.py, ai_movie_gen_suite/stages/character_generator.py, ai_movie_gen_suite/stages/script_writer.py, ai_movie_gen_suite/stages/scene_description_engine.py, ai_movie_gen_suite/stages/__init__.py
  - Done when: Each stage accepts config + prior stage output, produces validated Pydantic model instances, handles LLM errors (falls back to default values or raises descriptive errors), and all stages pass unit tests with mocked LLM responses.

- [ ] Task 5: Project Manager, Formatters, and PDF Export
  - What: Implement project_manager.py with create/save/load/run_full_pipeline/regenerate methods including validation at each stage. Add formatters for text and FDX output. Add PDF export via fpdf. Ensure project directory structure matches the spec (project.json, beats.json, characters.json, script.json, scenes/, output/).
  - Files: ai_movie_gen_suite/project_manager.py, ai_movie_gen_suite/formatters/text_formatter.py, ai_movie_gen_suite/formatters/fdx_formatter.py, ai_movie_gen_suite/formatters/pdf_formatter.py, ai_movie_gen_suite/formatters/__init__.py
  - Done when: Full pipeline creates a valid project directory with all JSON artifacts, formatters produce correct output files (txt, fdx, pdf), regeneration of downstream stages works when upstream changes, and validation errors are raised before saving invalid data.

- [ ] Task 6: CLI, Integration Tests, and End-to-End Verification
  - What: Build Typer-based CLI with commands: init, generate, edit, regenerate, format, status, config (show/set). Add --verbose flag. Write integration tests covering the full pipeline (mocked LLM), CLI command routing, and formatter output validation.
  - Files: ai_movie_gen_suite/cli.py, tests/test_integration.py, tests/test_cli.py, tests/test_formatters.py, pyproject.toml (or setup.py), requirements.txt
  - Done when: All CLI commands execute correctly (with mocked LLM), --verbose flag prints debug output, integration tests cover init→generate→format→status flow, all tests pass, and the CLI can generate a complete screenplay from a logline end-to-end.