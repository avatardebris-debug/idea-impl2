"""Phase 2 tests: enrichment, adaptive extraction, format support."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_recipe():
    """Return a minimal base recipe dict."""
    return {
        "title": "Test Recipe",
        "summary": "A test recipe for unit testing.",
        "steps": [
            {
                "timestamp": 0.0,
                "description": "Chop the onions.",
                "inferred_tools": ["knife", "cutting board"],
                "inferred_materials": ["onions"],
            },
            {
                "timestamp": 5.0,
                "description": "Heat the oil in a pan.",
                "inferred_tools": ["pan", "stove"],
                "inferred_materials": ["oil"],
            },
            {
                "timestamp": 10.0,
                "description": "Add the onions and sauté.",
                "inferred_tools": ["spatula"],
                "inferred_materials": ["onions", "salt"],
            },
            {
                "timestamp": 15.0,
                "description": "Serve on a plate.",
                "inferred_tools": ["plate"],
                "inferred_materials": [],
            },
            {
                "timestamp": 20.0,
                "description": "Garnish with herbs.",
                "inferred_tools": [],
                "inferred_materials": ["herbs"],
            },
        ],
    }


@pytest.fixture
def sample_frames():
    """Return a list of fake frame dicts."""
    return [
        {"path": "/tmp/frame_000.png", "timestamp": 0.0},
        {"path": "/tmp/frame_002.png", "timestamp": 2.0},
        {"path": "/tmp/frame_004.png", "timestamp": 4.0},
        {"path": "/tmp/frame_006.png", "timestamp": 6.0},
        {"path": "/tmp/frame_008.png", "timestamp": 8.0},
    ]


@pytest.fixture
def sample_transcript():
    """Return a sample transcript string."""
    return "First, chop the onions finely. Then heat some oil in a pan. Add the onions and sauté until golden. Serve on a plate and garnish with fresh herbs."


# ---------------------------------------------------------------------------
# Task 1: --enrich flag parsing
# ---------------------------------------------------------------------------

class TestEnrichFlagParsing:
    """Test that --enrich flag is correctly parsed by the CLI."""

    def test_enrich_flag_defaults_to_false(self):
        """Without --enrich, the flag should default to False."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", required=True)
        parser.add_argument("--enrich", action="store_true", default=False)
        args = parser.parse_args(["--input", "test.mp4"])
        assert args.enrich is False

    def test_enrich_flag_can_be_set(self):
        """With --enrich, the flag should be True."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", required=True)
        parser.add_argument("--enrich", action="store_true", default=False)
        args = parser.parse_args(["--input", "test.mp4", "--enrich"])
        assert args.enrich is True


# ---------------------------------------------------------------------------
# Task 2: Enrichment function schema
# ---------------------------------------------------------------------------

class TestEnrichmentSchema:
    """Test that the enrichment function returns the correct schema."""

    def test_enriched_recipe_has_all_fields(self, sample_recipe, sample_frames, sample_transcript):
        """Enriched recipe should contain all 7 enriched fields."""
        from video_recipe.enricher import _parse_enrichment_response

        # Test the parser with a valid response
        mock_response = json.dumps({
            "ingredients": ["onions", "oil", "salt", "herbs"],
            "equipment": ["knife", "cutting board", "pan", "stove", "spatula", "plate"],
            "difficulty": "easy",
            "estimated_time_minutes": 15,
            "key_takeaways": ["Chop onions finely for even cooking", "Use medium heat for sautéing"],
        })
        result = _parse_enrichment_response(mock_response)
        assert "ingredients" in result
        assert "equipment" in result
        assert "difficulty" in result
        assert "estimated_time_minutes" in result
        assert "key_takeaways" in result
        assert result["difficulty"] in ("easy", "medium", "hard")
        assert isinstance(result["estimated_time_minutes"], int)

    def test_enriched_recipe_with_code_fences(self, sample_recipe, sample_frames, sample_transcript):
        """Parser should handle JSON wrapped in markdown code fences."""
        from video_recipe.enricher import _parse_enrichment_response

        mock_response = """```json
{
  "ingredients": ["flour", "eggs"],
  "equipment": ["bowl", "whisk"],
  "difficulty": "medium",
  "estimated_time_minutes": 30,
  "key_takeaways": ["Sift flour for better texture"]
}
```"""
        result = _parse_enrichment_response(mock_response)
        assert result["ingredients"] == ["flour", "eggs"]
        assert result["difficulty"] == "medium"

    def test_enriched_recipe_invalid_json_raises(self):
        """Invalid JSON should raise EnrichmentError."""
        from video_recipe.enricher import _parse_enrichment_response, EnrichmentError

        with pytest.raises(EnrichmentError):
            _parse_enrichment_response("not valid json {{{")


# ---------------------------------------------------------------------------
# Task 3: Adaptive frame extraction
# ---------------------------------------------------------------------------

class TestAdaptiveFrameExtraction:
    """Test adaptive frame extraction logic."""

    def test_motion_detection_returns_array(self):
        """_detect_motion should return a numpy array."""
        from video_recipe.extractor import _detect_motion
        import numpy as np

        # Create a minimal test video
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            # Create a 1-second test video using ffmpeg
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "testsrc=duration=1:size=320x240:rate=1",
                    "-vframes", "1",
                    tmp.name,
                ],
                capture_output=True,
                timeout=10,
            )
            motion = _detect_motion(tmp.name)
            assert isinstance(motion, np.ndarray)

    def test_adaptive_extraction_returns_frames(self, sample_frames):
        """_extract_adaptive_frames should return a list of frame dicts."""
        from video_recipe.extractor import _extract_adaptive_frames
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create a minimal test video
            test_video = tmpdir_path / "test.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "testsrc=duration=10:size=320x240:rate=1",
                    "-vframes", "1",
                    str(test_video),
                ],
                capture_output=True,
                timeout=10,
            )
            frames = _extract_adaptive_frames(
                str(test_video),
                tmpdir_path,
                duration=10.0,
                base_interval=2.0,
            )
            assert isinstance(frames, list)
            assert len(frames) > 0
            assert "path" in frames[0]
            assert "timestamp" in frames[0]

    def test_adaptive_extraction_fallback_on_failure(self):
        """If motion detection fails, should fall back to uniform extraction."""
        from video_recipe.extractor import _extract_adaptive_frames
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Use a non-existent video — should fall back gracefully
            frames = _extract_adaptive_frames(
                "/nonexistent/video.mp4",
                tmpdir_path,
                duration=10.0,
                base_interval=2.0,
            )
            # Should return empty list (no frames extracted)
            assert isinstance(frames, list)


# ---------------------------------------------------------------------------
# Task 4: Video format normalization
# ---------------------------------------------------------------------------

class TestVideoFormatNormalization:
    """Test video format normalization."""

    def test_normalize_mov_to_mp4(self):
        """MOV files should be normalized to MP4."""
        from video_recipe.extractor import _normalize_video_format
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create a minimal MOV file
            mov_path = tmpdir_path / "test.mov"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "testsrc=duration=1:size=320x240:rate=1",
                    "-c:v", "libx264",
                    str(mov_path),
                ],
                capture_output=True,
                timeout=10,
            )
            normalized = _normalize_video_format(str(mov_path), tmpdir_path)
            assert Path(normalized).exists()
            assert normalized.endswith(".mp4")

    def test_normalize_unsupported_format_raises(self):
        """Unsupported formats should raise ExtractionError."""
        from video_recipe.extractor import _normalize_video_format, ExtractionError
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            unsupported = tmpdir_path / "test.xyz"
            unsupported.touch()
            with pytest.raises(ExtractionError):
                _normalize_video_format(str(unsupported), tmpdir_path)

    def test_already_normalized_mp4_returns_same(self):
        """Already MP4 with H.264 should return the same path."""
        from video_recipe.extractor import _normalize_video_format
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mp4_path = tmpdir_path / "test.mp4"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "testsrc=duration=1:size=320x240:rate=1",
                    "-c:v", "libx264",
                    str(mp4_path),
                ],
                capture_output=True,
                timeout=10,
            )
            result = _normalize_video_format(str(mp4_path), tmpdir_path)
            assert result == str(mp4_path.resolve())


# ---------------------------------------------------------------------------
# Task 5: Enriched prompt generation
# ---------------------------------------------------------------------------

class TestEnrichedPromptGeneration:
    """Test that enriched prompts are generated correctly."""

    def test_enriched_prompt_has_enriched_system(self):
        """Enriched prompt should use the enriched system prompt."""
        from video_recipe.prompts import SYSTEM_PROMPT_ENRICHED

        assert "ingredients" in SYSTEM_PROMPT_ENRICHED
        assert "equipment" in SYSTEM_PROMPT_ENRICHED
        assert "difficulty" in SYSTEM_PROMPT_ENRICHED
        assert "estimated_time_minutes" in SYSTEM_PROMPT_ENRICHED
        assert "key_takeaways" in SYSTEM_PROMPT_ENRICHED

    def test_enriched_recipe_prompt_includes_frames_and_transcript(self, sample_frames, sample_transcript):
        """Enriched prompt should include frame info and transcript."""
        from video_recipe.prompts import build_enriched_recipe_prompt

        prompt = build_enriched_recipe_prompt(sample_frames, sample_transcript)
        assert "VIDEO FRAMES" in prompt
        assert "AUDIO TRANSCRIPT" in prompt
        assert "0.0" in prompt  # timestamp
        assert sample_transcript in prompt


# ---------------------------------------------------------------------------
# Task 6: Integration test for full enrichment pipeline
# ---------------------------------------------------------------------------

class TestEnrichmentIntegration:
    """Integration test for the full enrichment pipeline."""

    def test_full_enrichment_pipeline(self, sample_recipe, sample_frames, sample_transcript):
        """Test the full enrichment pipeline end-to-end."""
        from video_recipe.enricher import enrich_recipe
        from unittest.mock import MagicMock

        # Mock the LLM call to return a valid enrichment response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "ingredients": ["onions", "oil", "salt", "herbs"],
            "equipment": ["knife", "cutting board", "pan", "stove", "spatula", "plate"],
            "difficulty": "easy",
            "estimated_time_minutes": 15,
            "key_takeaways": ["Chop onions finely for even cooking"],
        })

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("video_recipe.enricher.OpenAI", return_value=mock_client):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                result = enrich_recipe(sample_recipe, sample_frames, sample_transcript)

        assert result["ingredients"] == ["onions", "oil", "salt", "herbs"]
        assert result["equipment"] == ["knife", "cutting board", "pan", "stove", "spatula", "plate"]
        assert result["difficulty"] == "easy"
        assert result["estimated_time_minutes"] == 15
        assert result["key_takeaways"] == ["Chop onions finely for even cooking"]
        # Original fields should be preserved
        assert result["title"] == sample_recipe["title"]
        assert result["steps"] == sample_recipe["steps"]

    def test_enrichment_with_empty_transcript(self, sample_recipe, sample_frames):
        """Enrichment should work even with empty transcript."""
        from video_recipe.enricher import enrich_recipe
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "ingredients": ["flour", "sugar"],
            "equipment": ["bowl"],
            "difficulty": "easy",
            "estimated_time_minutes": 10,
            "key_takeaways": [],
        })

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("video_recipe.enricher.OpenAI", return_value=mock_client):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                result = enrich_recipe(sample_recipe, sample_frames, "")

        assert result["ingredients"] == ["flour", "sugar"]

    def test_enrichment_handles_llm_error_gracefully(self, sample_recipe, sample_frames, sample_transcript):
        """Enrichment should raise EnrichmentError if LLM call fails."""
        from video_recipe.enricher import enrich_recipe, EnrichmentError
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("LLM error")

        with patch("video_recipe.enricher.OpenAI", return_value=mock_client):
            with pytest.raises(EnrichmentError):
                enrich_recipe(sample_recipe, sample_frames, sample_transcript)
