# VideoBabbel

A modular Python pipeline for video transcription, translation, summarization, and Q&A.

## Features

- **Video Ingestion**: Extract audio from video files using ffmpeg
- **Transcription**: Transcribe audio to text using OpenAI Whisper
- **Translation**: Translate text between languages using Google Translate or DeepL
- **Summarization**: Create concise summaries of transcripts
- **Q&A**: Answer questions based on transcript content
- **CLI**: Full command-line interface for scripting and automation
- **Docker**: Containerized deployment with docker-compose

## Installation

### Method 1: pip (from source)

```bash
cd video_babbel/workspace
pip install -e ".[dev]"
```

### Method 2: pip (from PyPI — once published)

```bash
pip install video-babbel
```

### Method 3: Docker

```bash
docker build -t video-babbel .
# or with docker-compose
docker compose build
```

### Prerequisites

- **Python 3.8+**
- **ffmpeg** — required for video ingestion. Install via:
  - Ubuntu/Debian: `apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: `choco install ffmpeg`

## CLI Usage

### Quick start

```bash
# Show help
video-babbel --help

# List supported languages
video-babbel languages

# Process a video and translate to Spanish
video-babbel process --video /path/to/video.mp4 --lang es

# Process with a larger Whisper model and DeepL backend
video-babbel process --video /path/to/video.mp4 --lang fr --whisper-model medium --backend deepL

# Process and save results to a JSON file
video-babbel process --video /path/to/video.mp4 --lang es --output result.json

# Process with a question
video-babbel process --video /path/to/video.mp4 --lang es --question "What is the main topic?"

# Verbose logging
video-babbel -v process --video /path/to/video.mp4 --lang es
```

### CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--video` | `-v` | Path to input video file (required) | — |
| `--lang` | `-l` | Target language ISO 639-1 code (required) | — |
| `--whisper-model` | `-m` | Whisper model size | `base` |
| `--max-sentences` | `-s` | Max sentences in summary | `5` |
| `--backend` | `-b` | Translation backend (`google` or `deepL`) | `google` |
| `--output` | `-o` | Path to write JSON output | stdout |
| `--question` | `-q` | Question to answer from transcript | — |
| `--verbose` | `-v` | Enable DEBUG logging | `False` |
| `--help` | `-h` | Show help message | — |

### Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |
| `ja` | Japanese |
| `ko` | Korean |
| `zh` | Chinese |
| `ru` | Russian |

## Python API Usage

### Basic pipeline

```python
from video_babbel import VideoBabbel

# Create a pipeline instance
pipeline = VideoBabbel(
    target_lang="es",
    whisper_model="base",
    max_sentences=5,
    backend="google",
)

# Process a video file
result = pipeline.process("/path/to/video.mp4")

# Access results
print(result["transcript"])   # List of segment dicts
print(result["translation"])  # Translated text
print(result["summary"])      # Summary text
```

### Q&A

```python
from video_babbel import VideoBabbel

pipeline = VideoBabbel(target_lang="es")
result = pipeline.process("/path/to/video.mp4")

# Answer a question
qa_engine = pipeline.qa_engine
answer = qa_engine.answer("What is the main topic?")
print(answer)
```

### Programmatic segments

```python
from video_babbel import VideoBabbel

pipeline = VideoBabbel(target_lang="fr")
result = pipeline.process("/path/to/video.mp4")

# Access transcript segments
for segment in result["transcript"]:
    print(f"[{segment['start']:.1f}s - {segment['end']:.1f}s] {segment['text']}")
```

## Docker Usage

### Build and run

```bash
# Build the image
docker build -t video-babbel .

# Run with a video file
docker run --rm -v /path/to/videos:/home/video/videos:ro video-babbel process \
    --video /home/video/videos/sample.mp4 \
    --lang es \
    --output /home/video/output/result.json
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
  video-babbel:
    build: .
    volumes:
      - ./videos:/home/video/videos:ro
      - ./output:/home/video/output
    command: ["--help"]
```

```bash
# Build and start
docker compose build
docker compose run video-babbel process \
    --video /home/video/videos/sample.mp4 \
    --lang es
```

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Video File  │────▶│  Ingestion   │────▶│  Audio File  │
└─────────────┘     └──────────────┘     └──────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Q&A Engine │◀────│   QA Engine  │◀────│  Transcript  │
└─────────────┘     └──────────────┘     └──────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Summary     │◀────│ Summarizer   │◀────│  Text        │
└─────────────┘     └──────────────┘     └──────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Translation  │◀────│ Translator   │◀────│  Text        │
└─────────────┘     └──────────────┘     └──────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Whisper     │────▶│ Transcriber  │────▶│  Audio File  │
└─────────────┘     └──────────────┘     └──────────────┘
```

### Pipeline Components

1. **Ingestion** — Extracts audio from video using ffmpeg
2. **Transcription** — Converts audio to text using OpenAI Whisper
3. **Translation** — Translates text to target language
4. **Summarization** — Creates a concise summary of the transcript
5. **Q&A** — Answers questions based on transcript content

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VIDEO_BABBEL_DEFAULT_LANG` | Default target language | `en` |
| `DEEPL_API_KEY` | DeepL API key (for deepL backend) | — |
| `OPENAI_API_KEY` | OpenAI API key (for Whisper) | — |

### Pipeline Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `target_lang` | `str` | ISO 639-1 language code | `en` |
| `whisper_model` | `str` | Whisper model size | `base` |
| `max_sentences` | `int` | Max summary sentences | `5` |
| `backend` | `str` | Translation backend | `google` |

## Error Handling

All pipeline operations raise specific exceptions:

| Exception | When |
|-----------|------|
| `VideoBabbelError` | General pipeline error |
| `IngestionError` | Audio extraction failed |
| `TranscriptionError` | Whisper transcription failed |
| `TranslationError` | Translation failed |
| `SummarizationError` | Summarization failed |
| `QAError` | Q&A failed |

```python
from video_babbel import VideoBabbel, VideoBabbelError

pipeline = VideoBabbel(target_lang="es")
try:
    result = pipeline.process("/path/to/video.mp4")
except VideoBabbelError as exc:
    print(f"Pipeline error: {exc}")
```

## Troubleshooting

### ffmpeg not found

```bash
# Ubuntu/Debian
apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

### Whisper model download fails

Ensure you have internet access and sufficient disk space. The model files are cached in `~/.cache/whisper/`.

### Translation errors

- For `google` backend: ensure you have internet access
- For `deepL` backend: set `DEEPL_API_KEY` environment variable

### Docker build fails

Ensure Docker is installed and running. Check that ffmpeg is available in the builder stage.

### Permission errors

Run with `--user` flag or ensure the output directory is writable.

## Development

### Running tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### Building the package

```bash
python -m build
```

### Linting

```bash
pip install ruff
ruff check video_babbel/
```

## License

MIT

## Author

VideoBabbel Contributors

## Version

0.1.0
