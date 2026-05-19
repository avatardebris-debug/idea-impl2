"""
test_scheduler.py — Tests for SM-2 spaced repetition scheduler.
"""
import unittest
import sys
sys.path.insert(0, '/workspace/idea impl/.pipeline/projects/video_babbel_enhanced/workspace')

from scheduler import Scheduler


class TestScheduler(unittest.TestCase):
    """Tests for the SM-2 scheduler."""

    def setUp(self):
        self.scheduler = Scheduler()

    def test_initialization(self):
        self.assertIsNotNone(self.scheduler)

    def test_schedule_new_card(self):
        card = {'clip_id': '1', 'interval': 0, 'repetition': 0, 'ease': 2.5}
        result = self.scheduler.schedule(card, quality=5)
        self.assertEqual(result['interval'], 1)
        self.assertEqual(result['repetition'], 1)
        self.assertEqual(result['ease'], 2.5)

    def test_schedule_good_review(self):
        card = {'clip_id': '1', 'interval': 1, 'repetition': 1, 'ease': 2.5}
        result = self.scheduler.schedule(card, quality=4)
        self.assertEqual(result['interval'], 6)
        self.assertEqual(result['repetition'], 2)

    def test_schedule_bad_review(self):
        card = {'clip_id': '1', 'interval': 6, 'repetition': 2, 'ease': 2.5}
        result = self.scheduler.schedule(card, quality=2)
        self.assertEqual(result['interval'], 0)
        self.assertEqual(result['repetition'], 0)

    def test_schedule_very_bad_review(self):
        card = {'clip_id': '1', 'interval': 6, 'repetition': 2, 'ease': 2.5}
        result = self.scheduler.schedule(card, quality=0)
        self.assertEqual(result['interval'], 0)
        self.assertEqual(result['repetition'], 0)

    def test_schedule_edge_quality(self):
        card = {'clip_id': '1', 'interval': 0, 'repetition': 0, 'ease': 2.5}
        result = self.scheduler.schedule(card, quality=1)
        self.assertEqual(result['interval'], 0)
        self.assertEqual(result['repetition'], 0)

    def test_schedule_max_ease(self):
        card = {'clip_id': '1', 'interval': 10, 'repetition': 5, 'ease': 2.5}
        result = self.scheduler.schedule(card, quality=5)
        self.assertGreater(result['ease'], 2.5)


if __name__ == '__main__':
    unittest.main()
