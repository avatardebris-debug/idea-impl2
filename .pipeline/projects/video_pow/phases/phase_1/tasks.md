# Phase 1 Tasks

- [x] Task 1: Project scaffolding and dependency setup
  - What: Create the project directory structure, pyproject.toml (or setup.py), requirements.txt, and a basic Python package layout for the `videopow` package.
  - Files: videopow/__init__.py, videopow/core.py, videopow/cli.py, pyproject.toml, requirements.txt, README.md
  - Done when: `pip install -e .` succeeds and `import videopow` works without errors.

- [x] Task 2: Core video processing engine
  - What: Implement the `VideoProcessor` class in `videopow/core.py` that can load a video file, extract frames, and write output video. Use a library like OpenCV or moviepy as the backend.
  - Files: videopow/core.py
  - Done when: `VideoProcessor` can load a video, extract frames, and write a new video file from those frames without errors.

- [x] Task 3: Text-to-video description parser
  - What: Implement a `VideoDescriber` class that takes a text description and converts it into structured video editing instructions (e.g., clip duration, transitions, effects, overlays).
  - Files: videopow/describer.py
  - Done when: `VideoDescriber.parse("a sunset over the ocean with slow zoom")` returns a structured dict with actionable fields (duration, effect, transition, etc.).

- [x] Task 4: End-to-end video generation pipeline
  - What: Wire together the describer and video processor into a `generate_video(description, input_video_path, output_path)` function that takes a text description and an input video, applies the described transformations, and produces an output video.
  - Files: videopow/pipeline.py
  - Done when: Calling `generate_video()` with a sample description and input video produces a valid output video file.

- [x] Task 5: CLI entry point
  - What: Implement a CLI in `videopow/cli.py` using argparse that accepts `--description`, `--input`, and `--output` arguments and calls the pipeline.
  - Files: videopow/cli.py
  - Done when: Running `python -m videopow --description "slow zoom on a forest" --input sample.mp4 --output result.mp4` produces an output video file.