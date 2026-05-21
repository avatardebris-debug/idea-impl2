# podcast — Extract Lessons from Podcast Episodes

**Pipeline:** audio/video → FastWhisper transcript → LLM lesson extractor → structured JSON/Markdown

## Overview

`podcast` extracts actionable lessons, insights, and quotes from podcast episodes. It supports:

- **Audio/video input** — `.mp3`, `.wav`, `.mp4`, `.m4a`, `.webm`, `.mov`
- **Text input** — paste or load a transcript directly
- **LLM-powered extraction** — uses any OpenAI-compatible API (default: `gpt-4o-mini`)
- **Rule-based fallback** — works without an LLM using heuristic extraction
- **Multiple output formats** — JSON or Markdown
- **Custom prompts** — focus on specific topics (marketing, leadership, etc.)

## Installation

```bash
cd workspace
pip install -e ".[dev]"          # core + dev deps
pip install -e ".[whisper]"      # optional: faster-whisper for audio transcription
```

## Quick Start

### From an audio file (with LLM):

```bash
python -m podcast episode.mp3 --lessons 10 --output lessons.md
```

### From an audio file (rule-based fallback, no LLM):

```bash
python -m podcast episode.mp3 --no-llm --lessons 10 --output lessons.md
```

### From raw transcript text:

```bash
python -m podcast transcript.txt --text-input --lessons 5 --format json --output lessons.json
```

### With a custom prompt:

```bash
python -m podcast episode.mp3 --lessons 7 --prompt "Focus on marketing tactics and growth strategies"
```

### Set a custom LLM model:

```bash
python -m podcast episode.mp3 --model claude-3.5-sonnet --lessons 10
```

## CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `episode` | Audio/video file or transcript path | (required) |
| `--lessons N` | Number of lessons to extract | `5` |
| `--output FILE` | Output file path | stdout |
| `--format json\|md` | Output format | `md` |
| `--prompt TEXT` | Custom extraction prompt | built-in |
| `--model NAME` | LLM model name | `gpt-4o-mini` |
| `--base-url URL` | OpenAI-compatible API base URL | `https://api.openai.com/v1` |
| `--api-key KEY` | API key for LLM | env `OPENAI_API_KEY` |
| `--text-input` | Treat input as transcript text | `False` |
| `--no-llm` | Use rule-based fallback | `False` |
| `--include-quotes` | Include direct quotes in output | `True` |
| `--no-quotes` | Exclude quotes from output | `False` |

## Architecture

```
podcast/
├── __init__.py        # Package init, version
├── __main__.py        # Entry point (python -m podcast)
├── cli.py             # CLI argument parsing & orchestration
├── transcriber.py     # Audio/video → transcript (faster-whisper)
├── extractor.py       # LLM or rule-based lesson extraction
├── formatter.py       # Render lessons to Markdown or plain text
tests/
└── test_podcast.py    # 16 unit tests (offline, no LLM/audio calls)
```

## Output Schema (JSON)

```json
{
  "episode": "Episode Title or filename",
  "lessons": [
    {
      "number": 1,
      "title": "Lesson title",
      "detail": "Detailed explanation",
      "quote": "Direct quote from transcript"
    }
  ],
  "summary": "Brief episode summary",
  "metadata": {
    "model": "gpt-4o-mini",
    "n_lessons": 5,
    "transcript_length": 12345,
    "custom_prompt": "",
    "extraction_method": "llm"
  }
}
```

## Error Handling

- **Missing audio file** — clear error message with suggestions
- **LLM API failure** — automatic fallback to rule-based extraction
- **Invalid transcript** — graceful handling with empty lessons
- **Missing API key** — helpful message pointing to environment variable

## Running Tests

```bash
cd workspace
pytest tests/test_podcast.py -v
```

## License

MIT
