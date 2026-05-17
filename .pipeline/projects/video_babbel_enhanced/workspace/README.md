# video_babbel_enhanced

Frequency-ordered language learning clips from any video — **Krashen's Comprehensible Input + SUBTLEX-US word frequency ranking**.

If you've memorized a video in your native language, you already have the perfect comprehension scaffold. This tool extracts the most pedagogically valuable phrases, presents them in both languages, and prepares them for spaced repetition.

## Pipeline

```
Video (.mp4) → Whisper STT → LLM Translation → SUBTLEX-US Frequency Score → ffmpeg Clip Extract
```

- Segments scored by **mean inverse rank** of constituent words × length penalty (3–15 words ideal)
- Top-N clips = the phrases covering the most high-frequency vocabulary in drillable sentence lengths
- Each clip ships with a `.json` metadata sidecar (L1 text, L2 text, timestamps, score)

## Installation

```bash
pip install faster-whisper
# ffmpeg must be on PATH:
# Windows: winget install ffmpeg
# Linux:   sudo apt install ffmpeg
# macOS:   brew install ffmpeg

cd workspace/
pip install -e .
```

## Quick Start

```bash
# Download SUBTLEX-US word frequency data (first time only)
python -m video_babbel_enhanced fetch-data

# Extract top 50 Spanish clips from a video
python -m video_babbel_enhanced extract lecture.mp4 \
    --lang es \
    --top 50 \
    --output clips/ \
    --source-lang en

# Each clip produces:
# clips/clip_000.mp4   — short video segment
# clips/clip_000.json  — {l1_text, l2_text, start, end, freq_score, word_count, source_video}
```

## Supported Languages

Any language supported by Whisper (transcription) and your Ollama model (translation).  
Common target language codes: `es` `fr` `de` `zh` `ja` `ko` `pt` `it` `ru` `ar`

## Architecture

| Module | Role |
|---|---|
| `transcriber.py` | Whisper STT wrapper. Reuses `video_ingestor_summary` workspace if available; falls back to direct `faster-whisper`. |
| `translator.py` | LLM translation. Reuses `video_babbel` workspace if available; falls back to Ollama batch translate. |
| `frequency_scorer.py` | SUBTLEX-US frequency scorer. Mean inverse rank × length penalty. Returns segments sorted by score. |
| `clip_extractor.py` | ffmpeg clip cutter. Produces `.mp4` + `.json` per clip. |
| `cli.py` | Wires the pipeline. `extract` and `fetch-data` subcommands. |

## Phase Roadmap

- **Phase 1** ✅ — Core extraction engine (this package)
- **Phase 2** — SM-2 spaced repetition drill loop + SQLite session tracking + Anki export
- **Phase 3** — Flask web UI: upload → watch → drill. Optional lip-sync via `video_langfake`

## Running Tests

```bash
cd workspace/
pytest tests/ -v
```

Tests are offline-safe: the scorer tests auto-generate a minimal word list if SUBTLEX-US isn't downloaded yet. Extractor/integration tests auto-skip if ffmpeg is not on PATH.
