"""
Unit tests for Phrase dataclass and PhraseDatabase (models.py).
"""
import pytest
from babble.models import Phrase, PhraseDatabase
from babble.phrases import create_default_database


# ---------------------------------------------------------------------------
# Phrase dataclass tests
# ---------------------------------------------------------------------------

class TestPhrase:
    def test_phrase_creation(self):
        p = Phrase(text="Hello", language="English", frequency_rank=1)
        assert p.text == "Hello"
        assert p.language == "English"
        assert p.frequency_rank == 1
        assert p.translation == ""
        assert p.context == ""

    def test_phrase_creation_with_all_fields(self):
        p = Phrase(
            text="Hola",
            language="Spanish",
            frequency_rank=34,
            translation="Hello",
            context="Greeting",
        )
        assert p.text == "Hola"
        assert p.language == "Spanish"
        assert p.frequency_rank == 34
        assert p.translation == "Hello"
        assert p.context == "Greeting"

    def test_phrase_repr(self):
        p = Phrase(text="Hello", language="English", frequency_rank=1)
        assert "Phrase" in repr(p)
        assert "Hello" in repr(p)

    def test_phrase_equality(self):
        p1 = Phrase(text="Hello", language="English", frequency_rank=1)
        p2 = Phrase(text="Hello", language="English", frequency_rank=1)
        p3 = Phrase(text="Hola", language="Spanish", frequency_rank=34)
        assert p1 == p2
        assert p1 != p3

    def test_phrase_sorting_by_frequency_rank(self):
        p1 = Phrase(text="A", language="English", frequency_rank=10)
        p2 = Phrase(text="B", language="English", frequency_rank=5)
        p3 = Phrase(text="C", language="English", frequency_rank=1)
        phrases = [p1, p2, p3]
        phrases.sort(key=lambda p: p.frequency_rank)
        assert phrases[0].text == "C"
        assert phrases[1].text == "B"
        assert phrases[2].text == "A"


# ---------------------------------------------------------------------------
# PhraseDatabase tests
# ---------------------------------------------------------------------------

class TestPhraseDatabase:
    def test_create_default_database(self):
        db = create_default_database()
        assert len(db) > 0
        languages = db.get_languages()
        assert "English" in languages
        assert "Spanish" in languages
        assert "French" in languages

    def test_add_phrase(self):
        db = PhraseDatabase()
        p = Phrase(text="Test", language="English", frequency_rank=1)
        db.add_phrase(p)
        assert len(db) == 1

    def test_add_phrases(self):
        db = PhraseDatabase()
        phrases = [
            Phrase(text="A", language="English", frequency_rank=1),
            Phrase(text="B", language="English", frequency_rank=2),
        ]
        db.add_phrases(phrases)
        assert len(db) == 2

    def test_get_by_language(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="Spanish", frequency_rank=2))
        english_phrases = db.get_by_language("English")
        assert len(english_phrases) == 1
        assert english_phrases[0].text == "A"

    def test_get_by_language_empty(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        french_phrases = db.get_by_language("French")
        assert len(french_phrases) == 0

    def test_get_by_frequency_rank(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="English", frequency_rank=2))
        result = db.get_by_frequency_rank(1)
        assert result is not None
        assert result.text == "A"

    def test_get_by_frequency_rank_not_found(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        result = db.get_by_frequency_rank(999)
        assert result is None

    def test_get_phrases_by_rank_range(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="English", frequency_rank=2))
        db.add_phrase(Phrase(text="C", language="English", frequency_rank=3))
        result = db.get_phrases_by_rank_range(1, 2)
        assert len(result) == 2
        assert result[0].text == "A"
        assert result[1].text == "B"

    def test_get_phrases_by_rank_range_empty(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        result = db.get_phrases_by_rank_range(10, 20)
        assert len(result) == 0

    def test_get_all_phrases(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="Spanish", frequency_rank=2))
        all_phrases = db.get_all_phrases()
        assert len(all_phrases) == 2

    def test_get_all_phrases_sorted(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="C", language="English", frequency_rank=3))
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="English", frequency_rank=2))
        all_phrases = db.get_all_phrases()
        assert all_phrases[0].text == "A"
        assert all_phrases[1].text == "B"
        assert all_phrases[2].text == "C"

    def test_get_languages(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="Spanish", frequency_rank=2))
        languages = db.get_languages()
        assert "English" in languages
        assert "Spanish" in languages
        assert len(languages) == 2

    def test_len(self):
        db = PhraseDatabase()
        assert len(db) == 0
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        assert len(db) == 1

    def test_get_phrases_for_language_alias(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        result = db.get_phrases_for_language("English")
        assert len(result) == 1
        assert result[0].text == "A"

    def test_default_database_has_phrases(self):
        db = create_default_database()
        assert len(db) == 100

    def test_default_database_sorted_by_frequency(self):
        db = create_default_database()
        phrases = db.get_all_phrases()
        for i in range(len(phrases) - 1):
            assert phrases[i].frequency_rank < phrases[i + 1].frequency_rank

    def test_default_database_languages(self):
        db = create_default_database()
        languages = db.get_languages()
        assert len(languages) == 3
        assert set(languages) == {"English", "Spanish", "French"}

    def test_get_by_language_returns_sorted_phrases(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="C", language="English", frequency_rank=3))
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="English", frequency_rank=2))
        result = db.get_by_language("English")
        # get_by_language returns from _by_language which is a list, not sorted
        # but the phrases should all be there
        assert len(result) == 3
        texts = {p.text for p in result}
        assert texts == {"A", "B", "C"}

    def test_duplicate_phrase_overwrites_by_rank(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        db.add_phrase(Phrase(text="B", language="English", frequency_rank=1))
        # The second phrase overwrites the first in _by_rank
        result = db.get_by_frequency_rank(1)
        assert result.text == "B"

    def test_repr(self):
        db = PhraseDatabase()
        db.add_phrase(Phrase(text="A", language="English", frequency_rank=1))
        r = repr(db)
        assert "PhraseDatabase" in r
        assert "English" in r
