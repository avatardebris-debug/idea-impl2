# Phase 1 Tasks - Transcript Extractor

## Phase 1: Core Audio Extraction & Transcription

### Description
Build the foundation - extract audio from video files and transcribe using Whisper/Faster Whisper.

### Deliverable
- CLI tool `transcript-extractor input.mp4 output.txt` that:
  - Accepts video/audio files (MP4, MOV, MKV, MP3, WAV, etc.)
  - Extracts audio stream
  - Transcribes using Faster Whisper (medium model by default)
  - Outputs plain text transcript

### Dependencies
- FFmpeg (system dependency)
- faster-whisper (pip install)
- pydub or moviepy for audio extraction

### Tasks

- [ ] Create project directory structure (`transcript_extractor/src/`, `transcript_extractor/tests/`, `transcript_extractor/config/`)
- [ ] Implement `audio_extractor.py` with `extract_audio()` function using FFmpeg/pydub
- [ ] Implement `transcriber.py` with `transcribe_audio()` function using faster-whisper
- [ ] Implement `cli.py` with argparse CLI interface (`transcript-extractor input output` command)
- [ ] Create `config/default_config.yaml` with Whisper model settings (model size, language, device)
- [ ] Implement error handling for: unsupported file formats, corrupted files, missing FFmpeg, transcription failures
- [ ] Write unit tests for `audio_extractor.py` (mock FFmpeg calls, test file format detection)
- [ ] Write unit tests for `transcriber.py` (test transcription with mock Whisper, test model loading)

<!-- 31 tasks removed by retroactive guardrail -->