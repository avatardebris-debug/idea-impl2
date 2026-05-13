# Video Ingestor

Video ingestion pipeline with transcription using FastAPI, Whisper, and SQLite.

## Features

- **URL-based ingestion**: Provide a video URL and get a transcribed transcript
- **File upload**: Upload video files directly
- **Job tracking**: Check status of ongoing/completed jobs
- **CLI**: Command-line interface for quick ingestion
- **REST API**: Full FastAPI REST API

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
uvicorn video_ingestor.api:app --host 0.0.0.0 --port 8000

# Or use the CLI
python -m video_ingestor ingest https://example.com/video.mp4
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest/url` | Ingest from URL |
| POST | `/ingest/upload` | Ingest from file upload |
| GET | `/jobs/{job_id}` | Get job status/result |
| GET | `/jobs` | List recent jobs |
| DELETE | `/jobs/{job_id}` | Delete a job |

## Configuration

Set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Whisper model size |
| `WHISPER_DEVICE` | `cuda`/`cpu` | Inference device |
| `VIDEO_INGESTOR_PORT` | `8000` | Server port |
| `VIDEO_INGESTOR_DB_PATH` | `./data/ingestor.db` | SQLite database path |
| `VIDEO_INGESTOR_TEMP_DIR` | `./data/temp` | Temp file directory |
| `VIDEO_INGESTOR_MAX_UPLOAD_MB` | `500` | Max upload size in MB |

## Project Structure

```
video_ingestor/
├── src/
│   └── video_ingestor/
│       ├── __init__.py
│       ├── __main__.py
│       ├── api.py          # FastAPI application
│       ├── cli.py          # CLI entry point
│       ├── config.py       # Settings
│       ├── ingestion.py    # Pipeline logic
│       ├── models.py       # Pydantic models
│       └── storage.py      # SQLite layer
├── tests/
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_ingestion.py
│   └── test_storage.py
├── pyproject.toml
├── requirements.txt
└── .env
```
