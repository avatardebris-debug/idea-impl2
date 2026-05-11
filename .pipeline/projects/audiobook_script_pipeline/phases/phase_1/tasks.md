# Phase 1 Tasks

- [ ] Task 1: Create project structure and package scaffold
  - What: Set up the Python package directory, __init__.py, and module layout for the audiobook_script_pipeline package.
  - Files: audiobook_script_pipeline/__init__.py, audiobook_script_pipeline/parser/__init__.py, audiobook_script_pipeline/formatter/__init__.py, audiobook_script_pipeline/pipeline/__init__.py
  - Done when: Package is importable (python -c "import audiobook_script_pipeline") succeeds with no errors.

- [ ] Task 2: Implement manuscript parser
  - What: Build a ManuscriptParser class that reads a plain-text manuscript file and splits it into chapters/sections based on heading markers (lines starting with "# " or "Chapter N"). Each chapter is represented as a dict with title, body text, and paragraph list.
  - Files: audiobook_script_pipeline/parser/manuscript_parser.py
  - Done when: ManuscriptParser can load a sample text file, detect chapter boundaries, and return a list of chapter dicts with correct titles and paragraph content.

- [ ] Task 3: Implement audio script formatter with pacing markers
  - What: Build an AudioScriptFormatter class that takes parsed chapter data and produces an audio script format. It adds pacing markers such as [PAUSE: 1s] for natural breaks, [EMPHASIS] for key terms, and [SLOW] / [FAST] for tempo changes. Output is a structured dict or formatted string ready for TTS consumption.
  - Files: audiobook_script_pipeline/formatter/audio_formatter.py
  - Done when: AudioScriptFormatter takes chapter dicts and outputs a list of audio script entries, each with text content and associated pacing markers, correctly placed at sentence and paragraph boundaries.

- [ ] Task 4: Implement pipeline orchestrator
  - What: Build a ScriptPipeline class that chains the parser and formatter: load manuscript → parse → format → return final audio script. Expose a single run() method that takes a file path and returns the complete formatted audio script.
  - Files: audiobook_script_pipeline/pipeline/script_pipeline.py
  - Done when: ScriptPipeline.run("sample.txt") returns a complete audio script dict with chapters, each containing formatted entries with pacing markers.

- [ ] Task 5: Create CLI entry point and sample manuscript
  - What: Add a cli.py module with a main() function that accepts a manuscript file path via command-line argument and runs the pipeline, printing or saving the output. Also create a sample manuscript file for testing.
  - Files: audiobook_script_pipeline/cli.py, audiobook_script_pipeline/sample_manuscript.txt
  - Done when: Running `python -m audiobook_script_pipeline.cli sample_manuscript.txt` produces a valid audio script output with pacing markers visible.