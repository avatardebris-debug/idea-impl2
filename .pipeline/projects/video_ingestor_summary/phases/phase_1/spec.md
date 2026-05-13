## Phase 1: Video Ingestion & Transcription Pipeline (MVP)

### Description
Build the foundational pipeline: accept a video, extract its audio track, transcribe the audio to timestamped text, and store the results. This is the smallest useful thing — it produces a searchable transcript from any video.

### Deliverables
- REST API endpoint for video upload (file or URL)
- Audio extraction module (FFmpeg-based)
- Speech-to-text transcription using Whisper or compatible ASR model
- Timestamped transcript storage (JSON or SQLite)
- Health check & status endpoint for job tracking
- Basic CLI tool for local testing

### Dependencies
- FFmpeg (audio extraction)
- Whisper or OpenAI Whisper-compatible library (transcription)
- Python 3.10+ with FastAPI (or equivalent framework)
- Storage backend (SQLite for MVP, configurable for later)

### Success Criteria
- [ ] Upload a video file or provide a URL and receive a transcript within 5 minutes for a 10-minute video
- [ ] Transcript includes word-level or sentence-level timestamps
- [ ] Transcript accuracy on clear dialogue exceeds 85% (WER < 15%) on test set
- [ ] System handles common video formats (MP4, MOV, AVI, MKV)
- [ ] API returns structured JSON with transcript, metadata, and status
- [ ] Graceful handling of unsupported formats and network errors

#