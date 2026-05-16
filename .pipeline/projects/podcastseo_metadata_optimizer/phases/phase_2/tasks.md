# Phase 2 Tasks

- [ ] Task 1: Show notes template engine with Jinja2
  - What: Create a `ShowNotesGenerator` class that uses Jinja2 to render show notes from keyword data + transcript text. Implement template loading from a `templates/` directory with Markdown, HTML, and plain-text variants. Each template must produce sections: episode summary, key takeaways, timestamped keyword anchors, related topics/tags, and CTA placeholder.
  - Files: `podcastseo/show_notes_generator.py`, `podcastseo/templates/show_notes.md.j2`, `podcastseo/templates/show_notes.html.j2`, `podcastseo/templates/show_notes.txt.j2`
  - Done when: Generator accepts a dict of keywords + transcript text and returns rendered strings for all three formats; templates contain all five required sections; no runtime errors on sample data.

- [ ] Task 2: Timestamp anchor builder
  - What: Build a `TimestampAnchorBuilder` class that maps each keyword to its first occurrence in the original transcript text, returning the timestamp (for SRT/VTT) or line number (for TXT/DOCX). This powers the "timestamped keyword anchors" section in show notes.
  - Files: `podcastseo/show_notes_generator.py` (add `TimestampAnchorBuilder` class)
  - Done when: Given a keyword and a raw transcript path, returns the first timestamp/line reference; handles all four formats (SRT, VTT, TXT, DOCX); returns `None` gracefully when keyword is not found in transcript.

- [ ] Task 3: Config file and template customization
  - What: Create a `config.yaml` file and a `ConfigLoader` class that reads template customization options: tone (e.g., professional, casual, enthusiastic), summary length (short/medium/long), section order, and CTA text. The generator must merge config defaults with any user overrides.
  - Files: `config.yaml`, `podcastseo/show_notes_generator.py` (add `ConfigLoader` class)
  - Done when: Default config produces valid show notes; changing tone/length/section order in config produces visibly different output; missing config falls back to sensible defaults without crashing.

- [ ] Task 4: CLI extension for show notes
  - What: Extend `cli.py` with a new `notes` command: `podcastseo notes input.srt --format markdown --output show_notes.md`. The command must accept `--format` (markdown/html/txt), `--output`, `--keywords` (path to Phase 1 keywords.json, or auto-discover), `--config` (path to config.yaml), and `--top` (override keyword count). It should run the full pipeline: parse transcript → extract keywords (if no keywords file provided) → generate show notes → write output.
  - Files: `podcastseo/cli.py` (add `notes` command), `podcastseo/__init__.py` (update version if needed)
  - Done when: CLI runs end-to-end with all format options; auto-generates keywords if no `--keywords` file given; `--output` writes to file; invalid options produce clear error messages; `podcastseo notes --help` shows all options.

- [ ] Task 5: Integration tests
  - What: Write end-to-end integration tests that verify the full pipeline: transcript → keywords → show notes → file output. Test all three output formats (Markdown, HTML, plain text). Validate that output includes all required sections. Test config-driven customization (changing tone/length updates output). Test timestamp accuracy on sample transcripts.
  - Files: `tests/test_show_notes.py`
  - Done when: All integration tests pass; tests cover all three formats; tests validate presence of all five sections; timestamp accuracy validated on sample transcripts; config customization tested; tests run in < 5 seconds.