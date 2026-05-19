"""
test_frequency_scorer.py — Tests for frequency scoring module.
"""
import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from frequency_scorer import FrequencyScorer


class TestFrequencyScorer(unittest.TestCase):
    """Tests for the FrequencyScorer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.scorer = FrequencyScorer()

    def test_initialization(self):
        """Test that FrequencyScorer initializes correctly."""
        self.assertIsNotNone(self.scorer.word_list)

    def test_score_segment(self):
        """Test scoring a text segment."""
        score = self.scorer.score_segment('Hello world')
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)

    def test_score_segment_empty(self):
        """Test scoring empty text."""
        score = self.scorer.score_segment('')
        self.assertEqual(score, 0)

    def test_score_segment_single_word(self):
        """Test scoring single word."""
        score = self.scorer.score_segment('hello')
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)

    def test_score_segment_high_freq_words(self):
        """Test that high frequency words score higher."""
        high_freq = self.scorer.score_segment('the')
        low_freq = self.scorer.score_segment('xylophone')
        # 'the' should score higher than 'xylophone'
        self.assertGreater(high_freq, low_freq)

    def test_score_segment_multiple_words(self):
        """Test scoring multi-word segment."""
        score = self.scorer.score_segment('the quick brown fox')
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)

    def test_score_segment_with_punctuation(self):
        """Test scoring with punctuation."""
        score = self.scorer.score_segment('Hello, world!')
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)

    def test_get_word_scores(self):
        """Test getting individual word scores."""
        scores = self.scorer.get_word_scores('hello world')
        self.assertIsInstance(scores, dict)
        self.assertIn('hello', scores)
        self.assertIn('world', scores)


if __name__ == '__main__':
    unittest.main()
