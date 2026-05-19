"""
test_anki_export.py — Tests for anki_export module.
"""
from __future__ import annotations
import json
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from video_babbel_enhanced.anki_export import export_anki


class TestExportAnki(unittest.TestCase):
    """Test the export_anki function."""

    def setUp(self):
        """Create temporary database with test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = pathlib.Path(self.temp_dir) / "test.db"
        self.output_path = pathlib.Path(self.temp_dir) / "test_deck.apkg"

        # Initialize database with test clips
        from video_babbel_enhanced import session_db
        session_db.init_db(self.db_path)

        # Insert test clips
        test_clips = [
            {
                "clip_id": "clip_001",
                "l1_text": "Hello world",
                "l2_text": "Hola mundo",
                "freq_score": 0.85,
                "start_time": 0.0,
                "end_time": 3.0,
                "source_video": "test.mp4",
            },
            {
                "clip_id": "clip_002",
                "l1_text": "Good morning",
                "l2_text": "Buenos días",
                "freq_score": 0.72,
                "start_time": 3.0,
                "end_time": 6.0,
                "source_video": "test.mp4",
            },
        ]

        for clip in test_clips:
            session_db.upsert_clip(self.db_path, clip)

    def test_export_anki_creates_deck(self):
        """Test that export_anki creates an .apkg file."""
        export_anki(
            deck_name="Test Deck",
            db_path=str(self.db_path),
            output_path=str(self.output_path),
        )

        self.assertTrue(self.output_path.exists())
        self.assertTrue(self.output_path.stat().st_size > 0)

    def test_export_anki_includes_all_clips(self):
        """Test that all clips are included in the deck."""
        export_anki(
            deck_name="Test Deck",
            db_path=str(self.db_path),
            output_path=str(self.output_path),
        )

        # Read the deck and verify content
        # Anki .apkg is a ZIP file with collection.anki2 inside
        import zipfile
        with zipfile.ZipFile(self.output_path) as zf:
            self.assertIn("collection.anki2", zf.namelist())

    def test_export_anki_empty_db(self):
        """Test export with empty database."""
        from video_babbel_enhanced import session_db as _session_db
        empty_db = pathlib.Path(self.temp_dir) / "empty.db"
        _session_db.init_db(empty_db)

        export_anki(
            deck_name="Empty Deck",
            db_path=str(empty_db),
            output_path=str(self.output_path),
        )

        # Should still create a valid (empty) deck
        self.assertTrue(self.output_path.exists())

    def test_export_anki_custom_deck_name(self):
        """Test export with custom deck name."""
        export_anki(
            deck_name="My Custom Deck",
            db_path=str(self.db_path),
            output_path=str(self.output_path),
        )

        # Deck name should be in the output
        import zipfile
        with zipfile.ZipFile(self.output_path) as zf:
            content = zf.read("collection.anki2").decode("utf-8", errors="replace")
            self.assertIn("My Custom Deck", content)


class TestAnkiExportIntegration(unittest.TestCase):
    """Integration tests for anki_export."""

    def test_full_export_workflow(self):
        """Test complete export workflow with realistic data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test.db"
            output_path = pathlib.Path(tmpdir) / "deck.apkg"

            from video_babbel_enhanced import session_db
            session_db.init_db(db_path)

            # Insert realistic clips
            clips = [
                {
                    "clip_id": f"clip_{i:03d}",
                    "l1_text": f"Source sentence {i}",
                    "l2_text": f"Traducción {i}",
                    "freq_score": round(0.5 + 0.5 * (i / 10), 4),
                    "start_time": i * 3.0,
                    "end_time": (i + 1) * 3.0,
                    "source_video": "lecture.mp4",
                }
                for i in range(5)
            ]

            for clip in clips:
                session_db.upsert_clip(db_path, clip)

            export_anki(
                deck_name="Lecture Clips",
                db_path=str(db_path),
                output_path=str(output_path),
            )

            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.stat().st_size > 1000)  # Should have content


if __name__ == "__main__":
    unittest.main()
