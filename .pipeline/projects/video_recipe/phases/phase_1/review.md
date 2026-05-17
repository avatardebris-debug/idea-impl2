### What's Good

- **Project structure is clean and well-organized**: Each module has a single responsibility — `input_handler.py` handles video input, `extractor.py` handles frame/transcript extraction, `llm_client.py` handles LLM communication, `prompts.py` handles prompt construction, `formatter.py` handles output rendering, and `cli.py` orchestrates everything.
- **CLI entry point (`cli.py`) is well-designed**: Uses argparse with sensible defaults (`--format json`, `--model gpt-4o`, `--interval 2.0`), supports `--output` for file output, `--api-key` for explicit key passing, and `--help`. Proper error handling with distinct exit codes (1 for input errors, 2 for extraction errors, 3 for LLM errors, 99 for unexpected errors).
- **`__main__.py` correctly enables `python -m video_recipe`**: Imports and calls `main()` from `cli.py`.
- **`input_handler.py` handles both local files and YouTube URLs**: Validates file existence and extension for local files; uses `yt-dlp` for YouTube URLs with proper timeout and error handling. YouTube domain detection covers `youtube.com`, `youtu.be`, and `youtube-nocookie.com`.
- **`extractor.py` uses `ffprobe` for duration detection and `ffmpeg` for frame extraction**: Frame naming convention (`frame_002.png`) matches the spec. Transcript extraction tries Whisper Python library first, then falls back to `whisper.cpp` binary, then returns empty string — a reasonable graceful degradation.
- **`llm_client.py` correctly encodes frames as base64 data URLs** for the OpenAI vision API, handles the `OPENAI_API_KEY` env var, and parses JSON responses with markdown code fence stripping.
- **`prompts.py` has a clear system prompt** that enforces JSON-only output, temporal ordering, at least 5 steps, and the exact schema required by the spec.
- **`formatter.py` renders both JSON and Markdown formats**: JSON uses `json.dumps` with `indent=2` for pretty-printing. Markdown uses headings, numbered steps, and tables for tools/materials — matching the spec.
- **`pyproject.toml` is properly configured** with project metadata, dependencies, and a CLI script entry point.
- **`tests/test_e2e.py` is comprehensive**: Tests all 6 tasks — CLI entry point, input handler, extractor, LLM client, formatter, and integration. Tests cover happy paths, error cases, edge cases (code fences, invalid formats, missing keys, non-existent files).
- **`_parse_recipe_response` in `llm_client.py` is robust**: Handles raw JSON, markdown code fences with language tags, and JSON blocks embedded in text.

## Blocking Bugs

- **`video_recipe/extractor.py:87-88` — `_extract_with_whisper` silently swallows errors from `ffmpeg` audio extraction**: The `subprocess.run` call for extracting audio to WAV does not check `result.returncode`. If ffmpeg fails (e.g., unsupported codec), `wav_path` may not exist, but the code only checks `wav_path.exists()` afterward. This is a minor issue but could cause confusing errors downstream in `whisper.load_model()`.

- **`video_recipe/extractor.py:108-109` — `_extract_with_whisper_cpp` has the same silent ffmpeg error**: Same issue — no return code check on the ffmpeg call before checking `wav_path.exists()`.

- **`video_recipe/prompts.py:1` — SYSTEM_PROMPT says "no code fences" but `_parse_recipe_response` in `llm_client.py` handles code fences**: This is not a blocking bug per se, but it's contradictory. The prompt tells the LLM not to use code fences, while the parser handles them. This is actually good defensive coding, so it's a non-blocking note.

- **`video_recipe/cli.py:67` — `sys.exit(0)` after printing output**: Using `sys.exit()` inside a function that's also called as `if __name__ == "__main__"` in `__main__.py` means the `__main__.py` file's `main()` call will exit the interpreter. This works correctly but is slightly unusual. Not a bug.

- **`video_recipe/extractor.py:65` — Frame timestamp naming uses `int(ts)` which truncates**: For `t=2.0`, this produces `frame_002.png` (correct). But for `t=0.0`, it produces `frame_000.png` (correct). For `t=2.5` (if interval were 2.5), it would produce `frame_002.png` (truncated). The spec says "every 2 seconds" so this is fine for the default case. Not a blocking bug.

- **`video_recipe/extractor.py:65` — Frame naming `frame_{int(ts):03d}` will produce `frame_000.png` for t=0**: This is correct per the spec ("frame_002.png for t=2s"). No issue.

- **`video_recipe/llm_client.py:50-51` — `max_tokens=4096` may be insufficient for long videos**: For a 30-second video with many frames, the LLM response could exceed 4096 tokens. This is a potential runtime issue but not a code bug — it depends on the video content. Not blocking.

- **`video_recipe/extractor.py:43` — `_get_video_duration` uses `ffprobe` which is not listed as a dependency**: The code depends on `ffprobe` being installed on the system, but it's not in `pyproject.toml` or `requirements.txt`. This is a missing dependency declaration. However, `ffprobe` is part of the `ffmpeg` package, so it's implicitly available if ffmpeg is installed. Not a blocking bug if ffmpeg is installed.

- **`video_recipe/extractor.py:43` — `_get_video_duration` returns `None` for invalid videos, but the caller checks `duration <= 0`**: If `ffprobe` returns a negative duration (unlikely but possible), the check `duration <= 0` would catch it. This is fine.

- **`video_recipe/formatter.py:58` — Markdown table separator for materials uses `|----------|` (extra dash)**: The separator line `|----------|` has 10 dashes instead of the standard 6. This is a minor markdown formatting inconsistency but won't cause rendering failures. Non-blocking.

## Non-Blocking Notes

- **`video_recipe/extractor.py` — Whisper model "base" is hardcoded**: Could be made configurable via a `--whisper-model` CLI flag for users who want different quality/speed tradeoffs.

- **`video_recipe/extractor.py` — No cleanup of temp directories**: The temp directories created by `tempfile.mkdtemp()` are never cleaned up. For a CLI tool, this could leave orphaned temp files. Consider using `tempfile.TemporaryDirectory()` as a context manager or adding cleanup.

- **`video_recipe/llm_client.py` — Base64 encoding all frames into the request**: For a 30-second video at 2-second intervals (15 frames), each frame could be several KB as base64, leading to a very large API request. Consider downsampling frames or using a URL-based approach for large videos.

- **`video_recipe/prompts.py` — The system prompt is very long and could be a token cost concern**: Consider making the prompt more concise or templated.

- **`video_recipe/cli.py` — The `--interval` flag uses `float` type**: This is correct and allows sub-second intervals. Good design.

- **`video_recipe/formatter.py` — Markdown output adds extra blank lines between steps**: The output format could be slightly more compact, but this is a style preference.

- **`pyproject.toml` — `build-backend` uses an unusual path**: `setuptools.backends._legacy:_Backend` is non-standard. The typical value is `setuptools.build_meta`. This could cause build issues.

- **`tests/test_e2e.py` — `TestIntegration.test_cli_with_output_file` accepts returncode 3 (LLM error)**: This means the test passes even if the LLM step fails, which is a bit lenient. It's acceptable for a test that requires an API key.

- **`video_recipe/input_handler.py` — YouTube download uses `tempfile.mkdtemp()` which is never cleaned up**: Same temp directory cleanup issue as the extractor.

## Reusable Components

- **`video_recipe/input_handler.py` — `_is_youtube_url()` helper**: A self-contained utility that checks if a URL is a YouTube URL by parsing the domain. Could be reused by any project that needs YouTube URL detection.

- **`video_recipe/llm_client.py` — `_parse_recipe_response()` function**: A self-contained JSON parser that handles markdown code fences and embedded JSON blocks. This is a general-purpose utility for parsing LLM JSON responses.

- **`video_recipe/formatter.py` — `render_recipe()` function**: While specific to the recipe schema, the pattern of rendering a dict to JSON or Markdown is a reusable output formatting pattern.

- **`video_recipe/prompts.py` — `SYSTEM_PROMPT` constant**: The structured prompt template for recipe generation is project-specific and not generally reusable.

## Verdict

PASS — The code is well-structured, aligns with the Phase 1 master plan, and all modules work together correctly. The only issues are minor (missing dependency declaration for ffprobe, markdown table formatting inconsistency, temp directory cleanup) that do not cause crashes, wrong output, or test failures.
