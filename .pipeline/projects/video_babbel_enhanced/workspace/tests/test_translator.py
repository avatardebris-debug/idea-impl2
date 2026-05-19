"""
test_translator.py — Tests for LLM translation module.
"""
import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from translator import Translator


class TestTranslator(unittest.TestCase):
    """Tests for the Translator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.translator = Translator(api_key='test-key')

    def test_initialization(self):
        """Test that Translator initializes correctly."""
        self.assertIsNotNone(self.translator.client)

    def test_translate_single_segment(self):
        """Test translating a single text segment."""
        result = self.translator.translate(
            text='Hello world',
            source_lang='en',
            target_lang='es'
        )
        self.assertIn('translation', result)
        self.assertIn('source_text', result)
        self.assertEqual(result['source_text'], 'Hello world')
        self.assertEqual(result['target_lang'], 'es')

    def test_translate_batch(self):
        """Test translating multiple segments."""
        segments = [
            {'text': 'Hello', 'start': 0.0, 'end': 1.0},
            {'text': 'World', 'start': 1.0, 'end': 2.0},
        ]
        results = self.translator.translate_batch(
            segments,
            source_lang='en',
            target_lang='fr'
        )
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIn('translation', r)
            self.assertEqual(r['target_lang'], 'fr')

    def test_translate_empty_text(self):
        """Test translating empty text."""
        result = self.translator.translate(
            text='',
            source_lang='en',
            target_lang='es'
        )
        self.assertEqual(result['translation'], '')

    def test_translate_preserves_formatting(self):
        """Test that translation preserves basic formatting."""
        result = self.translator.translate(
            text='Hello\nWorld',
            source_lang='en',
            target_lang='es'
        )
        self.assertIn('translation', result)

    def test_translate_with_special_chars(self):
        """Test translation with special characters."""
        result = self.translator.translate(
            text='Hello! How are you? I\'m fine.',
            source_lang='en',
            target_lang='de'
        )
        self.assertIn('translation', result)
        self.assertIn('source_text', result)


if __name__ == '__main__':
    unittest.main()
