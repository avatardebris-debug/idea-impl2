# Phase 1 Tasks

- [ ] Task 1: Project scaffolding & CLI entry point
  - What: Create the `video_recipe/` Python package with project structure, dependencies, and a CLI entry point that accepts `--input <path_or_url>` and `--format json|markdown` flags.
  - Files: `video_recipe/__init__.py`, `video_recipe/cli.py`, `pyproject.toml`, `requirements.txt`
  - Done when: Running `python -m video_recipe --input test.mp4 --format json` prints a usage message or error (no crash); argparse correctly parses both flags with sensible defaults (format=json, input required)

- [ ] Task 2: Video input handler (file + YouTube URL)
  - What: Build a module that accepts a local video file path or a YouTube URL. For local files, validate the file exists and is a video. For YouTube URLs, use `yt-dlp` to download the video to a temp directory and return the local path.
  - Files: `video_recipe/input_handler.py`
  - Done when: Given a local video path, the module returns the path unchanged. Given a valid YouTube URL, the module downloads the video and returns the local file path. Invalid inputs raise clear errors.

- [ ] Task 3: Frame extraction & audio transcript pipeline
  - What: Build a module that takes a local video path and (a) extracts key frames at regular intervals (every 2 seconds) using FFmpeg, saving them to a temp directory with timestamps, and (b) extracts an audio transcript using Whisper (or a lightweight speech-to-text fallback). Returns a structured result with frame paths + timestamps and the transcript text.
  - Files: `video_recipe/extractor.py`
  - Done when: Given a 30-second video, the module produces ~15 key frame images and a non-empty transcript string. Frame files are named with their timestamp (e.g., `frame_002.png` for t=2s). The module returns a dict: `{"frames": [{"path": "...", "timestamp": 2.0}, ...], "transcript": "..."}`

- [ ] Task 4: LLM recipe generation
  - What: Build a module that constructs a structured prompt containing the extracted frames (as base64 or file paths) and the audio transcript, sends it to an LLM (OpenAI API with a vision model like gpt-4o), and parses the JSON response into the recipe schema: `title`, `steps` (array of `{timestamp, description, inferred_tools, inferred_materials}`), `summary`.
  - Files: `video_recipe/llm_client.py`, `video_recipe/prompts.py`
  - Done when: Given frame paths and a transcript, the module returns a dict matching the recipe schema with at least 5 steps for a cooking demo video. The LLM prompt includes system instructions to output valid JSON and to produce temporally ordered, distinct actions.

- [ ] Task 5: Output formatting (JSON + Markdown)
  - What: Build a module that takes the recipe dict and renders it in the requested format (JSON or Markdown). JSON output should be pretty-printed and valid. Markdown output should use headings, numbered steps, and tables for tools/materials.
  - Files: `video_recipe/formatter.py`
  - Done when: `render_recipe(recipe, "json")` returns a string that is valid JSON parseable by `json.loads()`. `render_recipe(recipe, "markdown")` returns a human-readable markdown string with title, summary, and numbered steps. Both formats include all recipe fields.

- [ ] Task 6: Integration & end-to-end wiring
  - What: Wire all modules together in `cli.py`: input validation → download/extract → frame+transcript extraction → LLM recipe generation → format output → print/write. Add error handling at each stage. Ensure the CLI exits cleanly with appropriate exit codes.
  - Files: `video_recipe/cli.py` (updated), `tests/test_e2e.py`
  - Done when: Running `python -m video_recipe --input <video.mp4> --format json` produces valid JSON output with at least 5 timestamped steps. Running `--format markdown` produces readable markdown. Invalid input produces a clear error message and non-zero exit code.