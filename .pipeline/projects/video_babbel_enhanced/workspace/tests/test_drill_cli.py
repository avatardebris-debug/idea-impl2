"""
test_drill_cli.py — Tests for the drill CLI module.
"""
import unittest
import sys
import os
import tempfile
sys.path.insert(0, '/workspace/idea impl/.pipeline/projects/video_babbel_enhanced/workspace')

from drill_cli import DrillCLI


class TestDrillCLI(unittest.TestCase):
    """Tests for the DrillCLI class."""

    def setUp(self):
        self.cli = DrillCLI()

    def test_initialization(self):
        self.assertIsNotNone(self.cli)

    def test_get_mode(self):
        modes = self.cli.get_modes()
        self.assertIn('translate', modes)
        self.assertIn('reverse', modes)
        self.assertIn('shadow', modes)
        self.assertIn('mixed', modes)

    def test_validate_mode(self):
        self.assertTrue(self.cli.validate_mode('translate'))
        self.assertTrue(self.cli.validate_mode('reverse'))
        self.assertTrue(self.cli.validate_mode('shadow'))
        self.assertTrue(self.cli.validate_mode('mixed'))
        self.assertFalse(self.cli.validate_mode('invalid'))

    def test_get_input(self):
        # Test with mocked input
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: 'translate'
        result = self.cli.get_input('Mode? ')
        builtins.input = original_input
        self.assertEqual(result, 'translate')

    def test_display_card(self):
        card = {'source_text': 'Hello', 'target_text': 'Hola'}
        # Should not raise
        self.cli.display_card(card, 'translate')

    def test_display_review_buttons(self):
        # Should not raise
        self.cli.display_review_buttons()

    def test_get_quality(self):
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: '4'
        result = self.cli.get_quality()
        builtins.input = original_input
        self.assertEqual(result, 4)

    def test_get_quality_invalid(self):
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: 'invalid'
        result = self.cli.get_quality()
        builtins.input = original_input
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
