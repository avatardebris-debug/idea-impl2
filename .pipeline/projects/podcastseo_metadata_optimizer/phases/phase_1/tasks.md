# Phase 1 Tasks

- [x] Task 1: Project scaffolding and dependency setup
  - What: Create the Python project structure with `pyproject.toml`, virtual-env-ready layout, and all required dependencies (spaCy, scikit-learn, typer, pytest, webvtt-py, srt, python-docx, pyyaml). Add spaCy English model download step.
  - Files: `pyproject.toml`, `requirements.txt`, `README.md`, `podcastseo/` package dir, `podcastseo/__init__.py`
  - Done when: `pip install -e .` succeeds; `python -m pytest --collect-only` runs with zero errors; `python -m spacy download en_core_web_sm` completes.

- [ ] Task 2: Transcript parser (`transcript_parser.py`)
  - What: Build a `TranscriptParser` class that auto-detects format (SRT, VTT, TXT, DOCX) and extracts clean text. SRT/VTT parsing strips timestamps and speaker labels; TXT passes through; DOCX uses `python-docx`. Expose a `parse(path: str) -> str` method and a `parse_raw(path: str) -> dict` returning both raw text and metadata (word count, line count, format detected).
  - Files: `podcastseo/transcript_parser.py`
  - Done when: Parses SRT, VTT, TXT, and DOCX files into clean text; handles empty files and special characters gracefully; `parse()` returns a non-empty string for valid inputs; format detection is correct for all four types.

- [ ] Task 3: Keyword extractor (`keyword_extractor.py`)
  - What: Build a `KeywordExtractor` class that takes clean transcript text and produces ranked keywords. Uses scikit-learn `TfidfVectorizer` for TF-IDF scoring, spaCy NER for entity-based keyword boosting, and a custom stopword list (extending spaCy's defaults) to filter noise. Extracts both single-word keywords and bigram/trigram keyphrases. Returns results as a list of dicts with keys: `keyword`, `score`, `category` (topic/brand/tech/person/other), `occurrences`.
  - Files: `podcastseo/keyword_extractor.py`, `podcastseo/stopwords.txt` (custom stopword list)
  - Done when: Extracts ≥15 meaningful keywords from a 30-minute podcast transcript; scores correlate with human judgment on 5 sample transcripts; handles edge cases (empty input, single word, all-stopword text) without crashing; output schema matches `[{"keyword": "...", "score": 0.95, "category": "topic", "occurrences": 12}]`.

- [ ] Task 4: CLI entry point (`cli.py`)
  - What: Build a Typer-based CLI with a `keywords` subcommand. Flags: `input` (positional, transcript file path), `--top` (int, default 20), `--output` (optional, file path for JSON output). If `--output` is given, writes results to file; otherwise prints JSON to stdout. Validates input file existence and format support before processing.
  - Files: `podcastseo/cli.py`, `pyproject.toml` (console_scripts entry)
  - Done when: `podcastseo keywords sample.srt --top 20 --output keywords.json` produces valid JSON with the expected schema; `podcastseo keywords sample.txt` prints JSON to stdout; invalid input file gives a clear error message; `podcastseo --help` shows usage.

- [ ] Task 5: Unit tests
  - What: Write comprehensive tests for the parser (SRT, VTT, TXT, DOCX, empty files, special characters, malformed input) and the extractor (empty input, single word, all-stopword text, bigram extraction, score normalization). Include integration test that runs the full pipeline: parse → extract → verify output schema.
  - Files: `tests/test_transcript_parser.py`, `tests/test_keyword_extractor.py`, `tests/test_cli.py`, `tests/conftest.py`, `tests/fixtures/` (sample SRT, VTT, TXT, DOCX files)
  - Done when: All tests pass with `pytest`; coverage ≥ 80% on `transcript_parser.py` and `keyword_extractor.py`; integration test validates end-to-end pipeline.

- [ ] Task 6: Sample data and end-to-end validation
  - What: Create at least 3 sample podcast transcripts (SRT, VTT, TXT) of realistic length (~30 min / ~4,500 words each) covering different topics (tech, health, business). Run the CLI against each, validate output has ≥15 keywords with reasonable scores, and confirm processing time < 10 seconds for a 50,000-word transcript.
  - Files: `tests/fixtures/sample_tech.srt`, `tests/fixtures/sample_health.vtt`, `tests/fixtures/sample_business.txt`, `tests/fixtures/sample_large.txt` (50k words for perf test)
  - Done when: All three sample transcripts produce ≥15 meaningful keywords; CLI runs end-to-end without errors; 50k-word transcript processes in < 10 seconds; output JSON is valid and schema-compliant.