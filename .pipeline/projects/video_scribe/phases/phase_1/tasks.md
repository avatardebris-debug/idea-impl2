# Phase 1 Tasks

- [x] Task 1: Project scaffolding and CLI entry point
  - What: Create the project directory structure, requirements.txt, configuration module, and the main CLI entry point with argument parsing (--input, --output, --provider, --api-key).
  - Files: video_scribe/ (directory), video_scribe/__init__.py, video_scribe/cli.py, video_scribe/config.py, requirements.txt, README.md
  - Done when: Running `python video_scribe.py --help` prints usage with all flags; `--input` and `--output` arguments are parsed correctly; default provider is GPT-4o; config module loads API keys from environment variables or a .env file.

- [x] Task 2: Frame extraction and key frame selection
  - What: Build a module that opens a video file (mp4/mov), decodes frames using OpenCV, and selects one representative key frame per clip (mid-scene frame or highest-variance frame).
  - Files: video_scribe/frame_extractor.py
  - Done when: Given any valid mp4 or mov file, the module returns a single frame as a PIL Image or numpy array; handles videos of varying lengths by selecting the frame closest to the 50% mark; no external ffmpeg dependency required beyond what OpenCV provides.

- [x] Task 3: VLM integration for frame analysis
  - What: Build a module that encodes the key frame as base64, sends it to a VLM (default GPT-4o via OpenAI API) with a structured cinematography prompt, and parses the text response.
  - Files: video_scribe/vlm_analyzer.py
  - Done when: Given a PIL Image, the module returns a structured dict with keys: content_summary, visual_elements, camera_notes, lighting_color_notes; supports switching between OpenAI GPT-4o and Anthropic Claude via config; handles API errors gracefully with clear error messages.

- [x] Task 4: Markdown output formatting
  - What: Build a module that takes the VLM analysis dict and renders it as a formatted markdown scene description, with optional file output.
  - Files: video_scribe/output_formatter.py
  - Done when: Given the analysis dict, the module returns a markdown string with headings for each section (Scene Content, Visual Elements, Camera Position/Angle, Lighting & Color); writing to a file via --output flag produces a valid .md file; stdout output is human-readable.

- [x] Task 5: End-to-end integration and smoke test
  - What: Wire all modules together in the CLI tool so a single command processes a video and produces a scene description; add a smoke test with a synthetic video.
  - Files: video_scribe/cli.py (updated), tests/test_pipeline.py, tests/sample_input.mp4 (or generate one)
  - Done when: Running `python video_scribe.py input.mp4 --output description.md` processes a video end-to-end and writes a markdown file; the description contains at least 3 distinct visual observations; the full pipeline completes in under 60 seconds for a 30-second clip; smoke test passes with a generated test video.