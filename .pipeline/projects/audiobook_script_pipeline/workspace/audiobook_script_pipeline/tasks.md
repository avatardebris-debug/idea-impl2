# Phase 1 Tasks

- [x] Task 1: Create project structure and package scaffold
  - What: Set up the Python package directory, __init__.py, and module layout for the audiobook_script_pipeline package.
  - Files: audiobook_script_pipeline/__init__.py, audiobook_script_pipeline/parser/__init__.py, audiobook_script_pipeline/formatter/__init__.py, audiobook_script_pipeline/pipeline/__init__.py
  - Done when: Package is importable (python -c "import audiobook_script_pipeline") succeeds with no errors.

- [x] Task 2: Implement manuscript parser
  - What: Build a ManuscriptParser class that reads a plain-text manuscript file and splits it into chapters/sections based on heading markers (lines starting with "# " or "Chapter N"). Each chapter is represented as a dict with title, body text, and paragraph list.
  - Files: audiobook_script_pipeline/parser/manuscript_parser.py
  - Done when: ManuscriptParser can load a sample text file, detect chapter boundaries, and return a list of chapter dicts with correct titles and paragraph content.

- [x] Task 3: Implement audio script formatter with pacing markers
  - What: Build an AudioScriptFormatter class that takes parsed chapter data and produces an audio script format. It adds pacing markers such as [PAUSE: 1s] for natural breaks, [EMPHASIS] for key terms, and [SLOW] / [FAST] for tempo changes. Output is a structured dict or formatted string ready for TTS consumption.
  - Files: audiobook_script_pipeline/formatter/audio_formatter.py
  - Done when: AudioScriptFormatter takes chapter dicts and outputs a list of audio script entries, each with text content and associated pacing markers, correctly placed at sentence and paragraph boundaries.

- [x] Task 4: Implement pipeline orchestrator
  - What: Build a ScriptPipeline class that chains the parser and formatter: load manuscript → parse → format → return final audio script. Expose a single run() method that takes a file path and returns the complete formatted audio script.
  - Files: audiobook_script_pipeline/pipeline/script_pipeline.py
  - Done when: ScriptPipeline.run("sample.txt") returns a complete audio script dict with chapters, each containing formatted entries with pacing markers.

- [x] Task 5: Create CLI entry point and sample manuscript
  - What: Add a cli.py module with a main() function that accepts a manuscript file path via command-line argument and runs the pipeline, printing or saving the output. Also create a sample manuscript file for testing.
  - Files: audiobook_script_pipeline/cli.py, audiobook_script_pipeline/sample_manuscript.txt
  - Done when: Running `python -m audiobook_script_pipeline.cli sample_manuscript.txt` produces a valid audio script output with pacing markers visible.

- [x] Bug Fix 1: Fix HEADING_CHAPTER regex to capture subtitle text after chapter number/word
  - What: The regex `^Chapter\s+(\d+|[a-zA-Z]+)` did not capture subtitle text (e.g., "Chapter One: The Beginning" → title "Chapter One" losing ": The Beginning").
  - Fix: Updated regex to `^Chapter\s+(\d+|[a-zA-Z]+)(?::\s*(.+))?$` and updated title extraction logic to include the captured subtitle.
  - File: audiobook_script_pipeline/parser/manuscript_parser.py

- [x] Bug Fix 2: Fix FIRST_WORD regex to exclude common stop words from emphasis
  - What: The FIRST_WORD regex matched the first word of every sentence and wrapped it in [EMPHASIS] if it started with a capital letter, incorrectly marking common words like "The", "With", "As", "When".
  - Fix: Added a comprehensive stop_words set and updated the proper_noun_replacer to skip these common words.
  - File: audiobook_script_pipeline/formatter/audio_formatter.py

- [x] Bug Fix 3: Fix ALL_CAPS regex to skip common acronyms
  - What: The ALL_CAPS regex matched any word with 2+ uppercase letters, incorrectly wrapping common acronyms like "API", "TTS", "HTTP".
  - Fix: Added a skip_words set of common acronyms to the caps_replacer function.
  - File: audiobook_script_pipeline/formatter/audio_formatter.py

- [x] Bug Fix 4: Clarify document title in format_chapters
  - What: The top-level title was set to `chapters[0]["title"]` which was misleading — it should be the document title.
  - Fix: Extracted the title into a clearly-named `doc_title` variable with a clarifying comment.
  - File: audiobook_script_pipeline/formatter/audio_formatter.py

- [x] Bug Fix 5: Deduplicate skip_words set in caps_replacer
  - What: The skip_words set in caps_replacer had duplicate entries ("AI" appeared twice)
  - Fix: Removed duplicate "AI" entry from the set
  - Impact: Minor code cleanliness improvement

- [x] Bug Fix 6: Rename "paragraphs" to "sentences" in parser/formatter
  - What: The parser was splitting text into sentences but storing them in a field called "paragraphs", which was semantically incorrect
  - Fix: Renamed "paragraphs" to "sentences" throughout manuscript_parser.py and audio_formatter.py
  - Impact: Correct semantic naming — the data structure now accurately reflects what it contains

- [x] Bug Fix 7: Remove unnecessary sys.path.insert from cli.py
  - What: cli.py had `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` which is unnecessary when the package is properly installed
  - Fix: Removed the sys.path manipulation code
  - Impact: Cleaner code, no functional change (the import worked before and continues to work)

- [x] Bug Fix 8: Fix double PAUSE markers in formatter
  - What: The formatter was adding a PAUSE marker after each sentence AND a PAUSE marker before each sentence (except the first), resulting in double PAUSE markers
  - Fix: Removed the trailing PAUSE marker after each sentence entry, keeping only the leading PAUSE marker between sentences
  - Impact: Correct pacing — each sentence is preceded by exactly one PAUSE marker, not two

- [x] Bug Fix 9: Remove redundant trailing PAUSE in formatter
  - What: The formatter had a separate "Add [PAUSE] after each paragraph" block that was redundant with the "Add [PAUSE] before each sentence" logic
  - Fix: Removed the trailing PAUSE block entirely
  - Impact: Cleaner output, no functional change (the leading PAUSE already handles the break)
