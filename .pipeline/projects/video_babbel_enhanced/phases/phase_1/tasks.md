# Tasks — Phase 1: Core Extraction Engine

- [ ] Task 1: Project scaffolding and package setup
  - What: Create the Python package structure. Initialize `video_babbel_enhanced/__init__.py` with version and package metadata. Create `pyproject.toml` (or `setup.py`) with dependencies: `faster-whisper`, `ffmpeg-python` (or subprocess-only), `requests`. Create `data/` directory and bundle a minimal top-5000 SUBTLEX-US word frequency list (word, rank, freq_per_million, POS — tab-separated). Create `tests/__init__.py` and `conftest.py` with a helper that generates a short synthetic .mp4 (3-second silent black video using ffmpeg subprocess) for use in extractor tests.
  - Files: `video_babbel_enhanced/__init__.py`, `pyproject.toml`, `data/subtlex_us.txt`, `tests/conftest.py`
  - Done when: `python -c "import video_babbel_enhanced"` succeeds; `data/subtlex_us.txt` has ≥5000 entries; `conftest.py` synthetic video fixture works.

- [ ] Task 2: Implement transcriber.py
  - What: Thin Whisper STT wrapper. First try importing from the `video_ingestor_summary` workspace (path: `../../../video_ingestor_summary/workspace/`). If not importable, fall back to direct `faster-whisper` transcription. Expose a single function: `transcribe(video_path: str, language: str = None) -> list[dict]`. Each dict: `{"text": str, "start": float, "end": float, "words": list[dict]}`. The `words` key should contain word-level timestamps if available.
  - Files: `video_babbel_enhanced/transcriber.py`
  - Done when: `transcribe("test.mp4")` returns a non-empty list of segment dicts; handles a silent/speech video; doesn't crash if video_ingestor workspace is unavailable.

- [ ] Task 3: Implement translator.py
  - What: LLM translation wrapper. Accepts a list of segment dicts (from transcriber), adds `l2_text` field to each. First try importing from `video_babbel` workspace. If not available, call Ollama directly with a one-shot prompt: `"Translate this to {lang}: {text}"`. Batch segments in groups of 20 for efficiency. Expose: `translate(segments: list[dict], target_lang: str, source_lang: str = "en") -> list[dict]`. Return same list with `l2_text` populated.
  - Files: `video_babbel_enhanced/translator.py`
  - Done when: Given a list of English segments, returns same list with `l2_text` set for each; handles empty input gracefully; Ollama fallback works when workspace unavailable.

- [ ] Task 4: Implement frequency_scorer.py
  - What: Load SUBTLEX-US from `data/subtlex_us.txt`. Build a `{word: rank}` dict (lowercase). Implement `score_segments(segments: list[dict]) -> list[dict]`: for each segment, tokenize `l1_text` (lowercase, strip punctuation), compute `freq_score = mean(1.0 / rank[w] for w in tokens if w in rank_dict)` (0.0 if no known words), compute `length_score = 1.0 if 3 <= len(tokens) <= 15 else 0.4`, set `segment["freq_score"] = freq_score * length_score`. Return segments sorted descending by freq_score. Write tests: common words score higher; very short/long penalized; missing words don't crash; empty segment returns 0.
  - Files: `video_babbel_enhanced/frequency_scorer.py`, `tests/test_frequency_scorer.py`
  - Done when: All frequency scorer tests pass; scorer runs on a 100-segment list in <1 second.

- [ ] Task 5: Implement clip_extractor.py and cli.py
  - What: `clip_extractor.py` — takes a video path, list of top-N scored segments, output directory. For each segment: run `ffmpeg -y -ss {start} -to {end} -i {input} {output_dir}/clip_{i:03d}.mp4`. Write `{output_dir}/clip_{i:03d}.json` with keys: `clip_id`, `l1_text`, `l2_text`, `start`, `end`, `freq_score`, `word_count`, `source_video`. Expose: `extract_clips(video_path, segments, output_dir, top_n=50)`. `cli.py` — implement `python -m video_babbel_enhanced extract input.mp4 --lang es --top 50 --output clips/ --source-lang en` using `argparse`. Wire together: transcribe → translate → score → extract. Print progress per step.
  - Files: `video_babbel_enhanced/clip_extractor.py`, `video_babbel_enhanced/cli.py`, `tests/test_clip_extractor.py`
  - Done when: `python -m video_babbel_enhanced extract sample.mp4 --lang es --top 10 --output clips/` produces 10 .mp4 files and 10 .json files; extractor tests pass.

- [ ] Task 6: Integration test and validation
  - What: Write `tests/test_integration.py` with a full end-to-end test using the synthetic test video from conftest. Mock the translator (return `l2_text = "[translated] " + l1_text`) so no LLM call needed. Run: transcribe → mock-translate → score → extract 3 clips. Assert: output dir has 3 .mp4 files and 3 .json files; each JSON has all required keys; clips are valid mp4 (check with ffprobe or file size > 0). Run `pytest` — all tests pass. Write `README.md` with installation and usage example.
  - Files: `tests/test_integration.py`, `README.md`
  - Done when: `pytest` shows all tests passing (including integration); README has working usage example.
