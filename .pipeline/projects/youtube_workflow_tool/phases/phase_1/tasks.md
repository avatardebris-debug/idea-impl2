# Phase 1 Tasks

- [ ] Task 1: Project scaffolding — pyproject.toml, package structure, config
  - What: Create the project skeleton with pyproject.toml, package layout, config module, and CLI entry point registration
  - Files: pyproject.toml, youtube_workflow_tool/__init__.py, youtube_workflow_tool/config.py, youtube_workflow_tool/cli.py, tests/__init__.py
  - Done when: pyproject.toml has project metadata + click dependency + entry point; package imports cleanly; `youtube-workflow --help` works; config module loads defaults and reads from a YAML/JSON file

- [ ] Task 2: Templates module — title/description templates with fill-in-the-blank patterns
  - What: Build a template engine that supports fill-in-the-blank patterns for video titles and descriptions, with built-in template categories (tutorials, reviews, vlogs, listicles, etc.)
  - Files: youtube_workflow_tool/templates.py, tests/test_templates.py
  - Done when: TemplateEngine class can load built-in templates + custom templates; fill_in() replaces {placeholders} with provided values; at least 5 title templates and 3 description templates provided; templates can be listed by category; all template substitutions produce valid strings

- [ ] Task 3: Metadata generator — titles, descriptions, tags, hashtags
  - What: Build the core metadata generation logic that takes a video topic/niche and produces multiple title options, a full description, keyword tags, and hashtags
  - Files: youtube_workflow_tool/metadata_generator.py, tests/test_metadata_generator.py
  - Done when: generate_metadata(topic, niche, tone) returns a dict with titles (list), description (str), tags (list), hashtags (list); generates at least 5 title variants; description includes structured sections (intro, content, CTA, links); tags are deduplicated and limited to 15; hashtags are limited to 10 and relevant to topic

- [ ] Task 4: Optimizer module — scoring, keyword density, CTR prediction
  - What: Build a scoring/optimizer that evaluates metadata quality — title CTR potential, keyword density, tag relevance, description completeness
  - Files: youtube_workflow_tool/optimizer.py, tests/test_optimizer.py
  - Done when: ScoreResult dataclass with overall_score (0-100), breakdown (title_score, description_score, tag_score, hashtag_score); evaluate_metadata() scores a metadata dict; keyword_density_report() returns density stats; CTR_prediction() returns a 0-1 probability based on title patterns; optimizer can rank multiple metadata sets and pick the best

- [ ] Task 5: CLI entry point — click commands for metadata generation
  - What: Build the CLI with click subcommands: `generate` (generate metadata from topic), `score` (score existing metadata), `list-templates` (list available templates)
  - Files: youtube_workflow_tool/cli.py (updated), tests/test_cli.py
  - Done when: `youtube-workflow generate --topic "..." --niche "..."` outputs formatted metadata to stdout; `youtube-workflow score --json "{...}"` outputs score breakdown; `youtube-workflow list-templates` lists templates by category; all CLI commands support --output-file flag; CLI errors are handled gracefully with helpful messages

- [ ] Task 6: Unit tests for Phase 1 (50+ tests, all passing)
  - What: Write comprehensive unit tests covering all Phase 1 modules — templates, metadata generation, optimizer, CLI
  - Files: tests/test_templates.py, tests/test_metadata_generator.py, tests/test_optimizer.py, tests/test_cli.py, tests/fixtures/sample_metadata.json
  - Done when: 50+ tests across all test files; all tests pass with `pytest`; test coverage > 85% for all Phase 1 modules; fixtures directory with sample data; tests cover edge cases (empty topic, special characters, unicode, very long topics)