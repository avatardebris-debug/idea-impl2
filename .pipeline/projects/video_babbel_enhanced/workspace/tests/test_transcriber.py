"""
test_transcriber.py — Tests for Whisper transcription module.
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from transcriber import Transcriber


class TestTranscriber(unittest.TestCase):
    """Tests for the Transcriber class."""

    def setUp(self):
        """Set up test fixtures."""
        self.transcriber = Transcriber()

    def test_initialization(self):
        """Test that Transcriber initializes correctly."""
        self.assertIsNotNone(self.transcriber.model)
        self.assertEqual(self.transcriber.language, None)

    @patch('transcriber.whisper.load_model')
    def test_load_model(self, mock_load):
        """Test model loading."""
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        transcriber = Transcriber(model_name='tiny')
        mock_load.assert_called_once_with('tiny', device='cpu')

    @patch('transcriber.whisper.load_model')
    def test_transcribe(self, mock_load):
        """Test transcription returns segments."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': [
                {'text': 'Hello world', 'start': 0.0, 'end': 2.0},
                {'text': 'How are you?', 'start': 2.0, 'end': 4.0},
            ]
        }
        mock_load.return_value = mock_model

        with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
            f.write(b'fake video')
            f.flush()
            result = self.transcriber.transcribe(f.name)

        self.assertIn('segments', result)
        self.assertEqual(len(result['segments']), 2)
        self.assertEqual(result['segments'][0]['text'], 'Hello world')

    @patch('transcriber.whisper.load_model')
    def test_transcribe_with_language(self, mock_load):
        """Test transcription with specified language."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': [{'text': 'Hola mundo', 'start': 0.0, 'end': 2.0}]
        }
        mock_load.return_value = mock_model

        transcriber = Transcriber(language='es')
        with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
            f.write(b'fake video')
            f.flush()
            result = transcriber.transcribe(f.name)

        self.assertEqual(result['language'], 'es')

    @patch('transcriber.whisper.load_model')
    def test_transcribe_empty_video(self, mock_load):
        """Test transcription of empty/minimal video."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'segments': []}
        mock_load.return_value = mock_model

        with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
            f.write(b'')
            f.flush()
            result = self.transcriber.transcribe(f.name)

        self.assertEqual(result['segments'], [])

    @patch('transcriber.whisper.load_model')
    def test_transcribe_error_handling(self, mock_load):
        """Test error handling during transcription."""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception('Transcription failed')
        mock_load.return_value = mock_model

        with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
            f.write(b'fake video')
            f.flush()
            with self.assertRaises(Exception):
                self.transcriber.transcribe(f.name)


if __name__ == '__main__':
    unittest.main()
