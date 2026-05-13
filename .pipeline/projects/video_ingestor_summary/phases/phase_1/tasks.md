# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and configuration
  - What: Create the project directory structure, Python package, dependencies, and configuration system. Set up FastAPI app entry point, FFmpeg/Whisper dependency declarations, and SQLite storage config.
  - Files: `pyproject.toml`, `requirements.txt`, `src/video_ingestor/__init__.py`, `src/video_ingestor/config.py`, `src/video_ingestor/main.py`, `src/video_ingestor/storage.py`, `tests/`
  - Done when: `pip install -e .` succeeds, `uvicorn src.video_ingestor.main:app` starts without errors, config loads from environment variables or defaults, SQLite database file is created on first access

- [ ] Task 2: Video ingestion service (file upload + URL download)
  - What: Build the video ingestion module that accepts video uploads (multipart form file or URL). Validates file format (MP4, MOV, AVI, MKV), downloads from URL if needed, and stores the raw video temporarily for processing. Returns a job ID for async tracking.
  - Files: `src/video_ingestor/ingestor.py`, `src/video_ingestor/models.py`, `src/video_ingestor/api.py`
  - Done when: Uploading an MP4/MOV/AVI/MKV file returns a job ID; providing a valid video URL downloads and stores it; unsupported formats return a 400 error with a clear message; invalid URLs return a 400 error

- [ ] Task 3: Audio extraction module (FFmpeg-based)
  - What: Extract the audio track from the ingested video using FFmpeg. Convert to a format suitable for Whisper (16kHz mono WAV). Handle errors (missing audio track, corrupted files) gracefully.
  - Files: `src/video_ingestor/audio_extractor.py`
  - Done when: Given a video file path, produces a 16kHz mono WAV audio file; handles MP4, MOV, AVI, MKV inputs; returns a clear error if no audio track exists or FFmpeg fails; does not load entire file into memory (streaming where possible)

- [ ] Task 4: Speech-to-text transcription (Whisper)
  - What: Transcribe the extracted audio to timestamped text using Whisper (or whisper-compatible library). Support word-level or sentence-level timestamps. Allow language detection or explicit language specification.
  - Files: `src/video_ingestor/transcriber.py`
  - Done when: Given a WAV file, returns a list of segments with text, start/end timestamps, and optional word-level timing; supports multilingual audio; completes transcription of a 10-minute video in under 5 minutes (on reasonable hardware); handles empty or silent audio gracefully

- [ ] Task 5: Transcript storage and API endpoints
  - What: Store transcripts and job status in SQLite. Create REST API endpoints: POST /ingest (upload/URL), GET /jobs/{job_id} (status + transcript), GET /health (health check). Return structured JSON responses with transcript, metadata, and status.
  - Files: `src/video_ingestor/storage.py`, `src/video_ingestor/api.py`, `src/video_ingestor/main.py`
  - Done when: POST /ingest accepts file or URL and returns a job ID; GET /jobs/{job_id} returns structured JSON with status (pending/processing/completed/failed), transcript text, timestamps, and metadata; GET /health returns 200 with system info; all API responses are valid JSON; failed jobs include an error message

- [ ] Task 6: CLI tool and integration test
  - What: Build a basic CLI tool for local testing (upload a video, wait for transcript, display results). Add an integration test that exercises the full pipeline: ingest → extract → transcribe → store → retrieve.
  - Files: `src/video_ingestor/cli.py`, `tests/test_integration.py`, `tests/sample_video.mp4` (or reference to a test fixture)
  - Done when: `python -m video_ingestor.cli --file <path>` runs the full pipeline end-to-end and prints the transcript; `pytest tests/` passes with the integration test completing a full ingest-to-transcript cycle; CLI accepts both `--file` and `--url` flags