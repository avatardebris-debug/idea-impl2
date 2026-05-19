"""
test_session_db.py — Tests for session database module.
"""
import unittest
import sys
import os
import tempfile
sys.path.insert(0, '/workspace/idea impl/.pipeline/projects/video_babbel_enhanced/workspace')

from session_db import SessionDB


class TestSessionDB(unittest.TestCase):
    """Tests for the SessionDB class."""

    def setUp(self):
        self.db_path = tempfile.mktemp(suffix='.db')
        self.db = SessionDB(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_initialization(self):
        self.assertIsNotNone(self.db)

    def test_create_session(self):
        session = self.db.create_session('test', 'desc')
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.name, 'test')

    def test_get_session(self):
        session = self.db.create_session('test', 'desc')
        retrieved = self.db.get_session(session.session_id)
        self.assertEqual(retrieved.name, 'test')

    def test_get_nonexistent_session(self):
        result = self.db.get_session('nonexistent')
        self.assertIsNone(result)

    def test_add_review(self):
        session = self.db.create_session('test', 'desc')
        review = self.db.add_review(session.session_id, 'clip1', 4)
        self.assertIsNotNone(review.review_id)

    def test_get_session_reviews(self):
        session = self.db.create_session('test', 'desc')
        self.db.add_review(session.session_id, 'clip1', 4)
        self.db.add_review(session.session_id, 'clip2', 3)
        reviews = self.db.get_session_reviews(session.session_id)
        self.assertEqual(len(reviews), 2)

    def test_update_card(self):
        session = self.db.create_session('test', 'desc')
        self.db.update_card(session.session_id, 'clip1', interval=5, repetition=2, ease=2.5)
        card = self.db.get_card(session.session_id, 'clip1')
        self.assertEqual(card.interval, 5)
        self.assertEqual(card.repetition, 2)

    def test_get_due_cards(self):
        session = self.db.create_session('test', 'desc')
        # Add a card that's due
        self.db.update_card(session.session_id, 'clip1', interval=0, repetition=0, ease=2.5)
        due = self.db.get_due_cards(session.session_id)
        self.assertEqual(len(due), 1)

    def test_get_due_cards_empty(self):
        session = self.db.create_session('test', 'desc')
        due = self.db.get_due_cards(session.session_id)
        self.assertEqual(len(due), 0)


if __name__ == '__main__':
    unittest.main()
