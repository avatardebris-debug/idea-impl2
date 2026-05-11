# Phase 1 Tasks

- [x] Task 1: Project scaffolding and dependency setup
  - What: Create the Python project structure with `pyproject.toml`, virtual-env-ready layout, and all required dependencies (spaCy, scikit-learn, typer, pytest, webvtt-py, srt, python-docx, pyyaml). Add spaCy English model download step.
  - Files: `pyproject.toml`, `requirements.txt`, `README.md`, `podcastseo/` package dir, `podcastseo/__init__.py`
  - Done when: `pip install -e .` succeeds; `python -m pytest --collect-only` runs with zero errors; `python -m spacy download en_core_web_sm` completes.

- [ ] Task 2: Transcript parser (`transcript_parser.py`)
  - What: Build a `TranscriptParser` class that auto-detects format (SRT, VTT, TXT, DOCX) and extracts clean text. SRT/VTT parsing strips timestamps and speaker labels; TXT passes through; DOCX uses `python-docx`. Expose a `parse(path: str) -> str` method and a `parse_raw(path: str) -> dict` returning both raw text and metadata (word count, format).
  - Files: `podcastseo/transcript_parser.py`, `tests/test_parser.py`, `tests/fixtures/sample_tech.srt`, `tests/fixtures/sample_health.vtt`, `tests/fixtures/sample_business.txt`
  - Done when: All four formats parse correctly; empty files return empty strings; unsupported formats raise `ValueError`; `parse_raw` returns correct metadata.

- [ ] Task 3: Keyword extractor (`keyword_extractor.py`)
  - What: Build a `KeywordExtractor` class using spaCy for NER and POS tagging, scikit-learn's `TfidfVectorizer` for phrase scoring, and a custom stopword list. Extract single words (nouns, proper nouns, adjectives) and bigrams/trigrams. Score candidates via TF-IDF, boost NER entities, normalize scores with `MinMaxScaler`, and return top N keywords with score, category, and occurrence count.
  - Files: `podcastseo/keyword_extractor.py`, `podcastseo/stopwords.txt`, `tests/test_extractor.py`
  - Done when: Returns correct top N keywords; scores are normalized floats; categories are assigned; no duplicates; handles empty text gracefully.

- [ ] Task 4: CLI entry point (`cli.py`)
  - What: Build a Typer CLI with a `keywords` command that accepts an input file path, `--top` option, and optional `--output` path. Validates input file existence and format, parses the transcript, extracts keywords, and outputs JSON to stdout or file.
  - Files: `podcastseo/cli.py`, `tests/test_cli.py`
  - Done when: CLI runs end-to-end for all supported formats; `--top` and `--output` options work; invalid inputs produce clear error messages.

- [ ] Task 5: Validation and testing
  - What: Run the full test suite (`pytest`) to ensure all components work correctly. Verify that the CLI produces valid JSON output for all supported formats. Check that keyword extraction handles edge cases (empty files, single words, large files).
  - Files: `tests/`, `pytest.ini` or `pyproject.toml` test config
  - Done when: All tests pass; CLI produces correct output for all formats; edge cases handled properly.

- [ ] Task 6: Documentation and final review
  - What: Write comprehensive documentation in `README.md` including installation, usage examples, and API reference. Add inline docstrings to all public methods. Create a `review.md` file summarizing the code review findings.
  - Files: `README.md`, `review.md`, inline docstrings in all source files
  - Done when: README includes installation, usage, and API docs; all public methods have docstrings; review.md summarizes findings.