"""
Unit tests for phrases.py (PhraseDatabase utilities).
"""
import pytest
from babble.phrases import (
    create_default_database,
    load_phrases_from_list,
    filter_phrases,
    get_top_phrases,
)
from babble.models import Phrase


# ------
# create_default_database
# ------

class TestCreateDefaultDatabase:
    def test_returns_database(self):
        db = create_default_database()
        assert len(db) > 0

    def test_contains_all_languages(self):
        db = create_default_database()
        languages = db.get_languages()
        assert "English" in languages
        assert "Spanish" in languages
        assert "French" in languages

    def test_contains_expected_phrase_count(self):
        db = create_default_database()
        # DEFAULT_PHRASES has 100 entries
        assert len(db) == 100

    def test_phrases_have_required_fields(self):
        db = create_default_database()
        for phrase in db.get_all_phrases():
            assert phrase.text
            assert phrase.language
            assert phrase.frequency_rank > 0


# ------
# load_phrases_from_list
# ------

class TestLoadPhrasesFromList:
    def test_loads_empty_list(self):
        db = load_phrases_from_list([])
        assert len(db) == 0

    def test_loads_single_phrase(self):
        phrases = [Phrase(text="Hello", language="English", frequency_rank=1)]
        db = load_phrases_from_list(phrases)
        assert len(db) == 1

    def test_loads_multiple_phrases(self):
        phrases = [
            Phrase(text="Hello", language="English", frequency_rank=1),
            Phrase(text="Hola", language="Spanish", frequency_rank=2),
        ]
        db = load_phrases_from_list(phrases)
        assert len(db) == 2

    def test_loaded_phrases_are_retrievable(self):
        phrases = [Phrase(text="Test", language="English", frequency_rank=5)]
        db = load_phrases_from_list(phrases)
        retrieved = db.get_by_language("English")
        assert len(retrieved) == 1
        assert retrieved[0].text == "Test"


# ------
# filter_phrases
# ------

class TestFilterPhrases:
    def test_filter_by_language(self):
        db = create_default_database()
        english = filter_phrases(db, language="English")
        assert all(p.language == "English" for p in english)
        assert len(english) == 33

    def test_filter_by_max_rank(self):
        db = create_default_database()
        top = filter_phrases(db, max_rank=10)
        assert all(p.frequency_rank <= 10 for p in top)
        assert len(top) == 10

    def test_filter_by_min_rank(self):
        db = create_default_database()
        high = filter_phrases(db, min_rank=90)
        assert all(p.frequency_rank >= 90 for p in high)

    def test_filter_by_language_and_max_rank(self):
        db = create_default_database()
        result = filter_phrases(db, language="Spanish", max_rank=40)
        assert all(p.language == "Spanish" for p in result)
        assert all(p.frequency_rank <= 40 for p in result)

    def test_filter_by_language_and_min_rank(self):
        db = create_default_database()
        result = filter_phrases(db, language="French", min_rank=80)
        assert all(p.language == "French" for p in result)
        assert all(p.frequency_rank >= 80 for p in result)

    def test_filter_no_criteria_returns_all(self):
        db = create_default_database()
        result = filter_phrases(db)
        assert len(result) == 100

    def test_filter_by_nonexistent_language(self):
        db = create_default_database()
        result = filter_phrases(db, language="German")
        assert len(result) == 0

    def test_filter_by_invalid_rank_range(self):
        db = create_default_database()
        result = filter_phrases(db, min_rank=200, max_rank=100)
        assert len(result) == 0


# ------
# get_top_phrases
# ------

class TestGetTopPhrases:
    def test_gets_top_n(self):
        db = create_default_database()
        top = get_top_phrases(db, n=5)
        assert len(top) == 5
        assert top[0].frequency_rank == 1
        assert top[4].frequency_rank == 5

    def test_gets_all_when_n_exceeds_total(self):
        db = create_default_database()
        top = get_top_phrases(db, n=200)
        assert len(top) == 100

    def test_gets_top_for_language(self):
        db = create_default_database()
        top = get_top_phrases(db, language="Spanish", n=3)
        assert len(top) == 3
        assert all(p.language == "Spanish" for p in top)
        assert top[0].frequency_rank == 34  # Spanish starts at rank 34

    def test_gets_top_for_nonexistent_language(self):
        db = create_default_database()
        top = get_top_phrases(db, language="German", n=5)
        assert len(top) == 0

    def test_gets_top_n_equals_one(self):
        db = create_default_database()
        top = get_top_phrases(db, n=1)
        assert len(top) == 1
        assert top[0].frequency_rank == 1

    def test_returns_sorted_by_frequency(self):
        db = create_default_database()
        top = get_top_phrases(db, n=10)
        for i in range(len(top) - 1):
            assert top[i].frequency_rank <= top[i + 1].frequency_rank
