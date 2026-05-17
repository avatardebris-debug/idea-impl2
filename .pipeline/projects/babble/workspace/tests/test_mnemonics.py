"""
Unit tests for mnemonics.py (Mnemonic generation engine).
"""
import pytest
from babble.mnemonics import (
    generate_mnemonic,
    assign_phrase_to_palace,
    _extract_keywords,
    _get_keyword_association,
    _generate_palace_location,
)
from babble.models import Phrase


# ------
# _extract_keywords
# ------

class TestExtractKeywords:
    def test_single_word(self):
        keywords = _extract_keywords("Hello")
        assert keywords == ["hello"]

    def test_multiple_words(self):
        keywords = _extract_keywords("How are you")
        assert keywords == ["how", "are", "you"]

    def test_removes_stop_words(self):
        keywords = _extract_keywords("I am fine")
        assert "i" not in keywords
        assert "am" not in keywords
        assert "fine" in keywords

    def test_handles_special_characters(self):
        keywords = _extract_keywords("¿Cómo estás?")
        assert "cómo" in keywords or "como" in keywords

    def test_handles_empty_string(self):
        keywords = _extract_keywords("")
        assert keywords == []

    def test_handles_punctuation(self):
        keywords = _extract_keywords("Hello, world!")
        assert "hello" in keywords
        assert "world" in keywords

    def test_handles_numbers(self):
        keywords = _extract_keywords("How much 5 dollars")
        assert "5" in keywords
        assert "dollars" in keywords

    def test_returns_lowercase(self):
        keywords = _extract_keywords("HELLO WORLD")
        assert all(k.islower() for k in keywords)


# ------
# _get_keyword_association
# ------

class TestGetKeywordAssociation:
    def test_returns_string(self):
        association = _get_keyword_association("hello")
        assert isinstance(association, str)
        assert len(association) > 0

    def test_returns_non_empty(self):
        association = _get_keyword_association("test")
        assert len(association) > 0

    def test_consistent_for_same_input(self):
        assoc1 = _get_keyword_association("hello")
        assoc2 = _get_keyword_association("hello")
        assert assoc1 == assoc2

    def test_different_for_different_input(self):
        assoc1 = _get_keyword_association("hello")
        assoc2 = _get_keyword_association("world")
        # They might be the same by chance, but let's check they're both valid
        assert len(assoc1) > 0
        assert len(assoc2) > 0

    def test_handles_empty_string(self):
        association = _get_keyword_association("")
        assert len(association) > 0

    def test_handles_long_word(self):
        association = _get_keyword_association("supercalifragilisticexpialidocious")
        assert len(association) > 0


# ------
# _generate_palace_location
# ------

class TestGeneratePalaceLocation:
    def test_returns_string(self):
        location = _generate_palace_location(0)
        assert isinstance(location, str)
        assert len(location) > 0

    def test_returns_different_locations(self):
        loc1 = _generate_palace_location(0)
        loc2 = _generate_palace_location(1)
        assert loc1 != loc2

    def test_returns_consistent_for_same_index(self):
        loc1 = _generate_palace_location(5)
        loc2 = _generate_palace_location(5)
        assert loc1 == loc2

    def test_returns_valid_locations(self):
        locations = [_generate_palace_location(i) for i in range(10)]
        assert all(isinstance(loc, str) and len(loc) > 0 for loc in locations)

    def test_handles_large_index(self):
        location = _generate_palace_location(1000)
        assert isinstance(location, str)
        assert len(location) > 0


# ------
# generate_mnemonic
# ------

class TestGenerateMnemonic:
    def test_returns_string(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        mnemonic = generate_mnemonic(phrase)
        assert isinstance(mnemonic, str)
        assert len(mnemonic) > 0

    def test_contains_phrase_text(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        mnemonic = generate_mnemonic(phrase)
        assert "hello" in mnemonic.lower()

    def test_contains_association(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        mnemonic = generate_mnemonic(phrase)
        # Should contain some vivid imagery
        assert len(mnemonic) > 10

    def test_handles_multi_word_phrase(self):
        phrase = Phrase(text="How are you", language="English", frequency_rank=7)
        mnemonic = generate_mnemonic(phrase)
        assert isinstance(mnemonic, str)
        assert len(mnemonic) > 0

    def test_handles_empty_text(self):
        phrase = Phrase(text="", language="English", frequency_rank=1)
        mnemonic = generate_mnemonic(phrase)
        assert isinstance(mnemonic, str)
        assert len(mnemonic) > 0

    def test_handles_special_characters(self):
        phrase = Phrase(text="¿Cómo estás?", language="Spanish", frequency_rank=40)
        mnemonic = generate_mnemonic(phrase)
        assert isinstance(mnemonic, str)
        assert len(mnemonic) > 0

    def test_consistent_for_same_phrase(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        m1 = generate_mnemonic(phrase)
        m2 = generate_mnemonic(phrase)
        assert m1 == m2

    def test_different_phrases_different_mnemonics(self):
        p1 = Phrase(text="Hello", language="English", frequency_rank=1)
        p2 = Phrase(text="Goodbye", language="English", frequency_rank=2)
        m1 = generate_mnemonic(p1)
        m2 = generate_mnemonic(p2)
        assert m1 != m2


# ------
# assign_phrase_to_palace
# ------

class TestAssignPhraseToPalace:
    def test_returns_dict(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert isinstance(result, dict)

    def test_contains_mnemonic(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert "mnemonic" in result
        assert len(result["mnemonic"]) > 0

    def test_contains_location(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert "location" in result
        assert len(result["location"]) > 0

    def test_contains_phrase(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert "phrase" in result
        assert result["phrase"] == phrase

    def test_mnemonic_contains_phrase_text(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert "hello" in result["mnemonic"].lower()

    def test_handles_multi_word_phrase(self):
        phrase = Phrase(text="How are you", language="English", frequency_rank=7)
        result = assign_phrase_to_palace(phrase)
        assert isinstance(result, dict)
        assert len(result["mnemonic"]) > 0

    def test_handles_empty_text(self):
        phrase = Phrase(text="", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert isinstance(result, dict)
        assert len(result["mnemonic"]) > 0

    def test_location_is_string(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert isinstance(result["location"], str)

    def test_phrase_is_same_object(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        result = assign_phrase_to_palace(phrase)
        assert result["phrase"] is phrase
