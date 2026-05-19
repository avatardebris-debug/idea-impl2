"""
test_subtitle_overlay.py — Tests for subtitle_overlay module.
"""
from __future__ import annotations
import json
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from video_babbel_enhanced.subtitle_overlay import overlay_subtitles, overlay_clips


class TestOverlaySubtitles(unittest.TestCase):
    """Test the overlay_subtitles function."""

    def setUp(self):
        """Create temporary directory structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.video_path = pathlib.Path(self.temp_dir) / "test.mp4"
        self.output_path = pathlib.Path(self.temp_dir) / "output.mp4"

        # Create a minimal valid MP4 file (1 second of black video)
        # We'll use ffmpeg to create a real video
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "color=c=black:s=320x240:r=1:d=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(self.video_path)
        ], capture_output=True, check=True)

    def test_overlay_subtitles_creates_output(self):
        """Test that overlay_subtitles creates an output file."""
        meta = [{
            "clip_id": "test",
            "l1_text": "Hello world",
            "l2_text": "Hola mundo",
            "start_time": 0.0,
            "end_time": 1.0,
        }]

        result = overlay_subtitles(
            self.video_path,
            meta,
            self.output_path,
            font_size=24,
            font_color="white",
            border_color="black",
            border_width=2,
            position="bottom",
        )

        self.assertTrue(result.exists())
        self.assertTrue(result.stat().st_size > 0)

    def test_overlay_subtitles_with_multiple_segments(self):
        """Test overlaying multiple subtitle segments."""
        meta = [
            {
                "clip_id": "test",
                "l1_text": "First segment",
                "l2_text": "Primer segmento",
                "start_time": 0.0,
                "end_time": 0.5,
            },
            {
                "clip_id": "test",
                "l1_text": "Second segment",
                "l2_text": "Segundo segmento",
                "start_time": 0.5,
                "end_time": 1.0,
            },
        ]

        result = overlay_subtitles(
            self.video_path,
            meta,
            self.output_path,
        )

        self.assertTrue(result.exists())

    def test_overlay_subtitles_custom_position(self):
        """Test different subtitle positions."""
        meta = [{
            "clip_id": "test",
            "l1_text": "Test",
            "l2_text": "Prueba",
            "start_time": 0.0,
            "end_time": 1.0,
        }]

        for position in ["top", "middle", "bottom"]:
            output = self.output_path.parent / f"output_{position}.mp4"
            result = overlay_subtitles(
                self.video_path,
                meta,
                output,
                position=position,
            )
            self.assertTrue(result.exists())


class TestOverlayClips(unittest.TestCase):
    """Test the overlay_clips batch function."""

    def setUp(self):
        """Create temporary directory with clip JSON files."""
        self.temp_dir = tempfile.mkdtemp()
        self.clips_dir = pathlib.Path(self.temp_dir) / "clips"
        self.clips_dir.mkdir()
        self.output_dir = pathlib.Path(self.temp_dir) / "output"

        # Create a minimal video
        self.video_path = self.clips_dir / "clip_001.mp4"
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "color=c=black:s=320x240:r=1:d=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(self.video_path)
        ], capture_output=True, check=True)

        # Create clip JSON
        clip_meta = {
            "clip_id": "clip_001",
            "l1_text": "Hello",
            "l2_text": "Hola",
            "start_time": 0.0,
            "end_time": 1.0,
        }
        json_path = self.clips_dir / "clip_001.json"
        json_path.write_text(json.dumps(clip_meta, indent=2))

    def test_overlay_clips_processes_all(self):
        """Test that overlay_clips processes all clips."""
        results = overlay_clips(
            clips_dir=str(self.clips_dir),
            output_dir=str(self.output_dir),
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].exists())
        self.assertTrue("subtitled" in results[0].name)

    def test_overlay_clips_no_clips_dir(self):
        """Test handling of missing clips directory."""
        results = overlay_clips(
            clips_dir="/nonexistent/path",
            output_dir=str(self.output_dir),
        )
        self.assertEqual(results, [])

    def test_overlay_clips_no_json_files(self):
        """Test handling of directory with no JSON files."""
        empty_dir = pathlib.Path(self.temp_dir) / "empty"
        empty_dir.mkdir()

        results = overlay_clips(
            clips_dir=str(empty_dir),
            output_dir=str(self.output_dir),
        )
        self.assertEqual(results, [])

    def test_overlay_clips_missing_video(self):
        """Test handling of JSON without corresponding video."""
        json_path = self.clips_dir / "clip_002.json"
        json_path.write_text(json.dumps({
            "clip_id": "clip_002",
            "l1_text": "No video",
            "l2_text": "Sin video",
            "start_time": 0.0,
            "end_time": 1.0,
        }))

        results = overlay_clips(
            clips_dir=str(self.clips_dir),
            output_dir=str(self.output_dir),
        )

        # Should only process clip_001 (clip_002 has no video)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
