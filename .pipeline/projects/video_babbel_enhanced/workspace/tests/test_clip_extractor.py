"""
test_clip_extractor.py — Tests for clip extraction module.
"""
import unittest
import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from clip_extractor import ClipExtractor


class TestClipExtractor(unittest.TestCase):
    """Tests for the ClipExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = ClipExtractor(output_dir=self.temp_dir)

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test that ClipExtractor initializes correctly."""
        self.assertEqual(self.extractor.output_dir, self.temp_dir)

    def test_extract_clip(self):
        """Test extracting a single clip."""
        # Create a minimal valid MP4 file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # Write a minimal MP4 header (ftyp box)
            f.write(b'\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41')
            f.flush()
            clip_path = f.name

        segments = [
            {'text': 'Hello', 'start': 0.0, 'end': 2.0},
        ]

        result = self.extractor.extract_clip(clip_path, segments[0], clip_id='test1')
        self.assertIsNotNone(result)
        self.assertIn('clip_id', result)
        self.assertEqual(result['clip_id'], 'test1')

    def test_extract_multiple_clips(self):
        """Test extracting multiple clips."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41')
            f.flush()
            clip_path = f.name

        segments = [
            {'text': 'Hello', 'start': 0.0, 'end': 2.0},
            {'text': 'World', 'start': 2.0, 'end': 4.0},
        ]

        results = self.extractor.extract_multiple(clip_path, segments)
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIn('clip_id', r)
            self.assertIn('clip_path', r)

    def test_extract_clip_invalid_duration(self):
        """Test extracting clip with invalid duration."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41')
            f.flush()
            clip_path = f.name

        segments = [
            {'text': 'Hello', 'start': 0.0, 'end': 0.0},  # Zero duration
        ]

        result = self.extractor.extract_clip(clip_path, segments[0], clip_id='test2')
        self.assertIsNone(result)

    def test_extract_clip_overlapping(self):
        """Test extracting overlapping clips."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41')
            f.flush()
            clip_path = f.name

        segments = [
            {'text': 'Hello', 'start': 0.0, 'end': 3.0},
            {'text': 'World', 'start': 2.0, 'end': 4.0},
        ]

        results = self.extractor.extract_multiple(clip_path, segments)
        self.assertEqual(len(results), 2)


if __name__ == '__main__':
    unittest.main()
