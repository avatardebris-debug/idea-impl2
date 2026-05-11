# Phase 2 Review

### What's Good
- **Comprehensive error handling**: `ManuscriptParseError`, `FileNotFoundError`, `PermissionError`, and `ValueError` are raised with descriptive messages across all core modules.
- **Well-structured test suite**: 42 tests across 4 test files covering happy paths, edge cases, and integration scenarios. Tests use fixtures effectively (e.g., `parser`, `formatter`, `pipeline`, `sample_chapters`).
- **Clean regex patterns**: `HEADING_HASH` and `HEADING_CHAPTER` patterns correctly detect both Markdown-style and "Chapter N" headings. The `HEADING_CHAPTER` regex properly captures subtitles.
- **Robust emphasis detection**: The `_add_emphasis` method intelligently handles ALL CAPS words, proper nouns, and known acronyms with a well-maintained skip list.
- **Good stop-words list**: The `proper_noun_replacer` excludes a comprehensive set of common English words to avoid false-positive emphasis markers.
- **Pipeline abstraction**: `ScriptPipeline` cleanly chains `ManuscriptParser` and `AudioScriptFormatter` with clear `run()` and `run_from_text()` methods.
- **CLI usability**: The CLI supports `--output` and `--pause` flags, prints helpful usage info via `--help`, and exits with code 1 on errors.
- **Conftest.py injection**: The `conftest.py` correctly injects the workspace into `sys.path` so local imports work in pytest.
- **README is thorough**: Covers installation, usage (CLI and Python API), manuscript format, output format, architecture, testing, and error handling.
- **Sample manuscript**: `sample_manuscript.txt` provides a realistic test document with proper chapter structure.

## Blocking Bugs
None

## Non-Blocking Notes
- `ManuscriptParser.__init__` has an empty `pass` body — could be removed entirely since no initialization is needed.
- The `HEADING_HASH` and `HEADING_CHAPTER` regexes are compiled as class attributes but could be module-level constants for clarity.
- The `AudioScriptFormatter.FIRST_WORD` regex `(?:^|[.!?]\s+)([A-Z][a-z]+)(?=\s|$)` uses a non-capturing group with alternation that may match mid-string; consider whether `re.MULTILINE` flag is needed for `^` to work as expected.
- The `cli.py` `if __name__ == "__main__": main()` block is redundant since the file is invoked via `python cli.py` from the CLI tests (the `__main__.py` handles `python -m` invocation). Minor redundancy, not a bug.
- The `__main__.py` docstring says `python -m audiobook_script_pipeline.cli` but the module path is `audiobook_script_pipeline.__main__` — this works because `__main__.py` is at the package root, but the docstring could be clearer.
- The `format_to_string` method in `AudioScriptFormatter` produces output with `[SLOW]` and `[FAST]` markers but the README shows `[/SLOW]` and `[/FAST]` closing tags that don't exist in the actual code. The README output example is slightly misleading.
- The `skip_words` set in `caps_replacer` is quite large (30+ entries). Consider externalizing to a constant or config file if it grows further.
- No type hints on `cli.py`'s `main()` function or on the `run_cli` helper in the CLI integration tests.

## Reusable Components
- **ManuscriptParser** (`manuscript_parser.py`): Reusable parser for plain-text manuscripts with chapter headings. Can be used independently or as a building block for other text-processing pipelines.
- **AudioScriptFormatter** (`audio_formatter.py`): Pacing marker generator with emphasis detection. The `_add_emphasis` method is a self-contained utility that could be extracted.
- **ScriptPipeline** (`script_pipeline.py`): Orchestrator that can be subclassed or extended with additional stages (e.g., TTS generation, file I/O).
- **CLI entry point** (`cli.py`): Reusable CLI scaffold with argparse, file validation, and output handling.
- **Test fixtures** (`conftest.py`): The `sys.path` injection pattern is reusable for any local-package pytest setup.
- **Sample manuscript** (`sample_manuscript.txt`): Can be reused as a test fixture or demo document.
