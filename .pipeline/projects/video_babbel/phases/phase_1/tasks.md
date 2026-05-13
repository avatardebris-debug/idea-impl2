# Phase 1 Tasks

- [x] Task 1: Project scaffolding and package setup
  - What: Create the Python package structure with __init__.py, setup.py/pyproject.toml, and a top-level package directory so the project is importable.
  - Files: video_babbel/__init__.py, video_babbel/core.py, pyproject.toml
  - Done when: `pip install -e .` succeeds and `import video_babbel` works without errors.

- [x] Task 2: Video ingestion module
  - What: Build a `VideoIngestor` class that accepts a video file path or URL and extracts raw audio using a library like `ffmpeg-python` or `moviepy`.
  - Files: video_babbel/ingestor.py
  - Done when: `VideoIngestor.from_path()` and `VideoIngestor.from_url()` load a video and produce a valid audio buffer / temporary audio file.

- [x] Task 3: Speech-to-text (transcription) module
  - What: Build a `Transcriber` class that takes an audio input and produces a text transcript with timestamps using a speech recognition library (e.g., `whisper` or `speech_recognition`).
  - Files: video_babbel/transcriber.py
  - Done when: `Transcriber.transcribe(audio_path)` returns a list of dicts with `text`, `start`, and `end` keys.

- [x] Task 4: Translation module
  - What: Build a `Translator` class that takes text (or transcript segments) and a target language, and returns translated text. Use a placeholder/mock translation for MVP (e.g., a simple dict-based or rule-based fallback) so the module is functional without external API keys.
  - Files: video_babbel/translator.py
  - Done when: `Translator.translate(text, target_lang="es")` returns a translated string (even if mock), and the class is designed to accept a pluggable backend.

- [x] Task 5: Summary and Q&A module
  - What: Build a `Summarizer` class that takes full transcript text and returns a concise summary, and a `QAEngine` class that takes a question and the transcript and returns an answer (using a simple keyword / extractive approach for MVP).
  - Files: video_babbel/summarizer.py
  - Done when: `Summarizer.summarize(transcript)` returns a non-empty string summary, and `QAEngine.answer(question, transcript)` returns a plausible answer string.

- [x] Task 6: Main pipeline orchestration and integration test
  - What: Build a `VideoBabbel` top-level class that chains ingest → transcribe → translate → summarize/answer, and write a simple integration script demonstrating the full pipeline on a sample video.
  - Files: video_babbel/pipeline.py, examples/run_demo.py
  - Done when: `VideoBabbel.process(video_path, target_lang="es")` runs the full pipeline and returns a dict with `transcript`, `translated_transcript`, `summary`, and `qa` keys.