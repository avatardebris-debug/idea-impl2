# Spec — Phase 1: Core Extraction Engine

## Goal
Given a video file, produce a ranked set of short clips with dual-language metadata. This is the heart of the project — everything else (drilling, web UI) feeds off the output of this phase.

## Package Structure to Build
```
video_babbel_enhanced/
├── __init__.py
├── transcriber.py        # Whisper STT wrapper
├── translator.py         # LLM translation wrapper
├── frequency_scorer.py   # SUBTLEX word list loader + segment scorer
├── clip_extractor.py     # ffmpeg clip cutter
├── cli.py                # Entry point: `python -m video_babbel_enhanced extract`
└── data/
    └── subtlex_us.txt    # Bundled top-10k English frequency list (or download on first run)
tests/
├── test_frequency_scorer.py
└── test_clip_extractor.py
```

## Key Implementation Details

### transcriber.py
- Try importing from `video_ingestor_summary` workspace first (path: `../../video_ingestor_summary/workspace/`)
- Fall back to direct `faster-whisper` call if workspace not available
- Output: list of `{"text": str, "start": float, "end": float, "words": [...]}` segments

### translator.py
- Try importing from `video_babbel` workspace first
- Fall back to direct `ollama` LLM call with a simple translate prompt
- Output: list of `{"original": str, "translated": str, "start": float, "end": float}`

### frequency_scorer.py
- Load SUBTLEX-US from `data/subtlex_us.txt` (tab-separated: word, rank, freq_per_million)
- If target language ≠ English, load target-language list too (Leipzig Corpora — downloadable)
- Score each segment:
  ```python
  freq_score = mean(1.0 / rank[w] for w in words if w.lower() in freq_list)
  length_score = 1.0 if 3 <= word_count <= 15 else 0.4
  segment.score = freq_score * length_score
  ```
- Return segments sorted descending by score

### clip_extractor.py
- Use `subprocess` to call `ffmpeg` — no Python bindings needed
- For each top-N segment: `ffmpeg -ss {start} -to {end} -i input.mp4 clip_N.mp4`
- Write `clip_N.json`: `{clip_id, l1_text, l2_text, start, end, freq_score, word_count, source_video}`

### cli.py
```
python -m video_babbel_enhanced extract input.mp4 \
    --lang es \          # target language code
    --top 50 \           # number of clips to extract
    --output clips/      # output directory
    --source-lang en     # source language (default: auto-detect)
```

## SUBTLEX-US Data
Download from: http://www.lexique.org/databases/SUBTLEX-US/SUBTLEX-US.zip
Or use a minimal bundled version with top 5000 words for offline use.
Format: `word\trank\tfreq_per_million\tPOS`

## Tests to Write
- `test_frequency_scorer.py`:
  - Common words (the, and, is) score higher than rare words
  - Very short (<3 words) and very long (>15 words) segments penalized
  - Handles empty segment gracefully
  - Handles words not in frequency list (score=0, no crash)
- `test_clip_extractor.py`:
  - Given mock segments + a test .mp4 (generate synthetic with ffmpeg in conftest),
    produces correct number of .mp4 files
  - Each output .mp4 has correct duration (end - start ± 0.1s)
  - Each .json has all required keys
  - Handles output directory creation if not exists
