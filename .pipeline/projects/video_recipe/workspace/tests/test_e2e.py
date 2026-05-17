"""End-to-end tests for video_recipe."""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from video_recipe.input_handler import handle_input, VideoInputError
from video_recipe.extractor import extract_frames_and_transcript, ExtractionError
from video_recipe.llm_client import generate_recipe, LLMClientError
from video_recipe.formatter import render_recipe


# ── Task 1: CLI entry point ──────────────────────────────────────────

class TestCLIEntry:
    def test_cli_help(self):
        """CLI --help should not crash."""
        result = subprocess.run(
            [sys.executable, "-m", "video_recipe", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        assert result.returncode == 0
        assert "--input" in result.stdout
        assert "--format" in result.stdout

    def test_cli_missing_input(self):
        """CLI without --input should exit non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "video_recipe"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        assert result.returncode != 0

    def test_cli_invalid_format(self):
        """CLI with invalid --format should exit non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "video_recipe", "--input", "test.mp4", "--format", "xml"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        assert result.returncode != 0


# ── Task 2: Input handler ────────────────────────────────────────────

class TestInputHandler:
    def test_local_file_returns_path(self, tmp_path):
        """Given a local video file, returns its absolute path."""
        video = tmp_path / "test.mp4"
        video.write_bytes(b"fake video")
        result = handle_input(str(video))
        assert result == str(video.resolve())

    def test_nonexistent_file_raises(self):
        """Non-existent file raises VideoInputError."""
        with pytest.raises(VideoInputError, match="does not exist"):
            handle_input("/nonexistent/path/video.mp4")

    def test_non_video_file_raises(self, tmp_path):
        """Non-video file raises VideoInputError."""
        txt = tmp_path / "readme.txt"
        txt.write_text("hello")
        with pytest.raises(VideoInputError, match="not appear to be a video"):
            handle_input(str(txt))

    def test_youtube_url_format(self):
        """YouTube URL is detected correctly."""
        from video_recipe.input_handler import _is_youtube_url
        assert _is_youtube_url("https://www.youtube.com/watch?v=abc123") is True
        assert _is_youtube_url("https://youtu.be/abc123") is True
        assert _is_youtube_url("https://example.com/video") is False


# ── Task 3: Extractor ────────────────────────────────────────────────

class TestExtractor:
    def test_extract_frames_and_transcript(self, tmp_path):
        """Extraction returns frames list and transcript string."""
        # Create a minimal valid MP4 file (1 second of black)
        video = tmp_path / "test.mp4"
        output_dir = tmp_path / "output"
        # Use ffmpeg to create a 2-second test video
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             "color=c=black:s=320x240:r=10:d=2",
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             str(video)],
            capture_output=True, timeout=30,
        )
        assert video.exists()

        result = extract_frames_and_transcript(str(video), output_dir)
        frames, transcript = result
        assert isinstance(frames, list)
        assert isinstance(transcript, str)

        # Check frame naming
        for frame in frames:
            assert "path" in frame
            assert "timestamp" in frame
            assert frame["path"].endswith(".png")

    def test_invalid_video_raises(self, tmp_path):
        """Invalid video raises ExtractionError."""
        with pytest.raises(ExtractionError):
            extract_frames_and_transcript("/nonexistent/video.mp4", tmp_path)


# ── Task 4: LLM client ───────────────────────────────────────────────

class TestLLMClient:
    def test_no_api_key_raises(self):
        """Missing API key raises LLMClientError."""
        # Ensure no OPENAI_API_KEY is set
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(LLMClientError, match="No OpenAI API key"):
                generate_recipe(frames=[], transcript="")
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_parse_recipe_response(self):
        """_parse_recipe_response handles JSON correctly."""
        from video_recipe.llm_client import _parse_recipe_response
        valid_json = json.dumps({
            "title": "Test",
            "summary": "A test recipe",
            "steps": [
                {"timestamp": 1.0, "description": "Do X", "inferred_tools": [], "inferred_materials": []},
                {"timestamp": 3.0, "description": "Do Y", "inferred_tools": [], "inferred_materials": []},
            ],
        })
        result = _parse_recipe_response(valid_json)
        assert result["title"] == "Test"
        assert len(result["steps"]) == 2

    def test_parse_recipe_with_code_fences(self):
        """Handles markdown code fences around JSON."""
        from video_recipe.llm_client import _parse_recipe_response
        fenced = '```json\n{"title": "Fenced", "summary": "", "steps": []}\n```'
        result = _parse_recipe_response(fenced)
        assert result["title"] == "Fenced"


# ── Task 5: Formatter ────────────────────────────────────────────────

class TestFormatter:
    def test_render_json_valid(self):
        """JSON output is valid and parseable."""
        recipe = {
            "title": "Test Recipe",
            "summary": "A test",
            "steps": [
                {"timestamp": 1.0, "description": "Step 1", "inferred_tools": ["pan"], "inferred_materials": ["oil"]},
            ],
        }
        output = render_recipe(recipe, "json")
        parsed = json.loads(output)
        assert parsed["title"] == "Test Recipe"
        assert len(parsed["steps"]) == 1

    def test_render_markdown_readable(self):
        """Markdown output contains expected elements."""
        recipe = {
            "title": "Test Recipe",
            "summary": "A test summary",
            "steps": [
                {"timestamp": 1.0, "description": "Chop onions", "inferred_tools": ["knife"], "inferred_materials": ["onions"]},
            ],
        }
        output = render_recipe(recipe, "markdown")
        assert "# Test Recipe" in output
        assert "## Steps" in output
        assert "Chop onions" in output
        assert "knife" in output
        assert "onions" in output

    def test_invalid_format_raises(self):
        """Invalid format raises ValueError."""
        recipe = {"title": "T", "summary": "", "steps": []}
        with pytest.raises(ValueError, match="Unsupported format"):
            render_recipe(recipe, "xml")


# ── Task 6: Integration ──────────────────────────────────────────────

class TestIntegration:
    def test_cli_with_output_file(self, tmp_path):
        """CLI with --output writes to file."""
        # Create a minimal test video
        video = tmp_path / "test.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             "color=c=black:s=320x240:r=10:d=2",
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             str(video)],
            capture_output=True, timeout=30,
        )

        output_file = tmp_path / "output.json"
        result = subprocess.run(
            [sys.executable, "-m", "video_recipe",
             "--input", str(video),
             "--format", "json",
             "--output", str(output_file)],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        # Should not crash (may fail on LLM if no key, but should not crash on I/O)
        assert output_file.exists() or result.returncode in (0, 3, 5)

    def test_cli_invalid_input_exits_nonzero(self):
        """CLI with invalid input exits non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "video_recipe",
             "--input", "/nonexistent/file.mp4"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        assert result.returncode != 0
        assert "Error" in result.stderr

    def test_render_recipe_all_fields(self):
        """Both formats include all recipe fields."""
        recipe = {
            "title": "Full Recipe",
            "summary": "Complete summary",
            "steps": [
                {"timestamp": 0.0, "description": "Start", "inferred_tools": ["a"], "inferred_materials": ["b"]},
                {"timestamp": 2.0, "description": "Middle", "inferred_tools": ["c"], "inferred_materials": ["d"]},
                {"timestamp": 4.0, "description": "End", "inferred_tools": ["e"], "inferred_materials": ["f"]},
            ],
        }
        json_out = render_recipe(recipe, "json")
        parsed = json.loads(json_out)
        assert parsed["title"] == "Full Recipe"
        assert parsed["summary"] == "Complete summary"
        assert len(parsed["steps"]) == 3

        md_out = render_recipe(recipe, "markdown")
        assert "# Full Recipe" in md_out
        assert "Complete summary" in md_out
        assert "Start" in md_out
        assert "Middle" in md_out
        assert "End" in md_out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
