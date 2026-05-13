"""Comprehensive unit tests for the movie_idea_generator generator module."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from movie_idea_generator.generator import (
    MovieIdeaGenerator,
    GENRES,
    GENRE_TEMPLATES,
    _generate_characters,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def generator():
    """A fresh MovieIdeaGenerator with no seed."""
    return MovieIdeaGenerator()


@pytest.fixture
def seeded_generator():
    """A MovieIdeaGenerator with a fixed seed."""
    return MovieIdeaGenerator(seed=42)


@pytest.fixture
def all_genres():
    """List of all valid genres."""
    return GENRES


# ── Test: valid genre generation ─────────────────────────────────────────────

def test_generate_returns_dict(generator):
    """generate() returns a dict with expected keys."""
    idea = generator.generate()
    assert isinstance(idea, dict)
    assert "title" in idea
    assert "genre" in idea
    assert "logline" in idea
    assert "characters" in idea


def test_generate_title_is_string(generator):
    """Generated title is a non-empty string."""
    idea = generator.generate()
    assert isinstance(idea["title"], str)
    assert len(idea["title"]) > 0


def test_generate_genre_is_string(generator):
    """Generated genre is a non-empty string."""
    idea = generator.generate()
    assert isinstance(idea["genre"], str)
    assert len(idea["genre"]) > 0


def test_generate_logline_is_string(generator):
    """Generated logline is a non-empty string."""
    idea = generator.generate()
    assert isinstance(idea["logline"], str)
    assert len(idea["logline"]) > 0


def test_generate_characters_is_list(generator):
    """Generated characters is a non-empty list."""
    idea = generator.generate()
    assert isinstance(idea["characters"], list)
    assert len(idea["characters"]) > 0


# ── Test: all 10 genres ─────────────────────────────────────────────────────

def test_generate_all_genres_work(all_genres, generator):
    """Every valid genre produces a valid idea."""
    for genre in all_genres:
        idea = generator.generate(genre=genre)
        assert idea["genre"] == genre
        assert isinstance(idea["title"], str) and len(idea["title"]) > 0
        assert isinstance(idea["logline"], str) and len(idea["logline"]) > 0
        assert isinstance(idea["characters"], list) and len(idea["characters"]) > 0


def test_generate_all_genres_count(all_genres):
    """All 10 genres are present in GENRES."""
    assert len(all_genres) == 10


# ── Test: invalid genre rejection ────────────────────────────────────────────

def test_generate_invalid_genre_raises_valueerror(generator):
    """generate(genre='InvalidGenre') raises ValueError."""
    with pytest.raises(ValueError, match="Invalid genre"):
        generator.generate(genre="InvalidGenre")


def test_generate_invalid_genre_message_contains_valid_genres(generator):
    """Error message lists valid genres."""
    with pytest.raises(ValueError) as exc_info:
        generator.generate(genre="ZombiePunk")
    for genre in GENRES:
        assert genre in str(exc_info.value)


def test_generate_batch_invalid_genre_raises_valueerror(generator):
    """generate_batch with invalid genre raises ValueError."""
    with pytest.raises(ValueError, match="Invalid genre"):
        generator.generate_batch(count=1, genre="Nonexistent")


def test_generate_batch_count_negative_raises_valueerror(generator):
    """generate_batch with count < 0 raises ValueError."""
    with pytest.raises(ValueError, match="count must be >= 0"):
        generator.generate_batch(count=-1)


# ── Test: batch generation edge cases ────────────────────────────────────────

def test_generate_batch_count_zero_returns_empty_list(generator):
    """generate_batch(count=0) returns an empty list."""
    result = generator.generate_batch(count=0)
    assert result == []


def test_generate_batch_count_one_returns_single_idea(generator):
    """generate_batch(count=1) returns a list with one idea."""
    result = generator.generate_batch(count=1)
    assert isinstance(result, list)
    assert len(result) == 1
    assert "title" in result[0]
    assert "genre" in result[0]
    assert "logline" in result[0]
    assert "characters" in result[0]


def test_generate_batch_count_five_returns_five_ideas(generator):
    """generate_batch(count=5) returns exactly 5 ideas."""
    result = generator.generate_batch(count=5)
    assert len(result) == 5


def test_generate_batch_count_large_returns_correct_count(generator):
    """generate_batch with large count returns correct number."""
    result = generator.generate_batch(count=100)
    assert len(result) == 100


def test_generate_batch_with_genre_constrains_all(generator):
    """generate_batch with genre constrains all ideas to that genre."""
    result = generator.generate_batch(count=10, genre="Horror")
    for idea in result:
        assert idea["genre"] == "Horror"


# ── Test: seed reproducibility ───────────────────────────────────────────────

def test_reproducibility_same_seed_same_output():
    """Same seed produces identical output."""
    gen1 = MovieIdeaGenerator(seed=42)
    gen2 = MovieIdeaGenerator(seed=42)
    assert gen1.generate() == gen2.generate()


def test_reproducibility_batch_same_seed_same_output():
    """Same seed produces identical batch output."""
    gen1 = MovieIdeaGenerator(seed=99)
    gen2 = MovieIdeaGenerator(seed=99)
    assert gen1.generate_batch(count=5) == gen2.generate_batch(count=5)


def test_different_seed_different_output():
    """Different seeds produce different output."""
    gen1 = MovieIdeaGenerator(seed=42)
    gen2 = MovieIdeaGenerator(seed=43)
    assert gen1.generate() != gen2.generate()


# ── Test: character generation structure ─────────────────────────────────────

def test_characters_have_required_keys():
    """Each character dict has name, description, role."""
    chars = _generate_characters(3)
    for ch in chars:
        assert "name" in ch
        assert "description" in ch
        assert "role" in ch


def test_characters_are_unique_names():
    """Character names are unique within a batch."""
    chars = _generate_characters(10)
    names = [ch["name"] for ch in chars]
    assert len(names) == len(set(names))


def test_characters_count_matches_request():
    """_generate_characters returns the requested count."""
    for count in [1, 3, 5, 10]:
        chars = _generate_characters(count)
        assert len(chars) == count


def test_character_role_is_valid():
    """Each character role is one of the expected roles."""
    valid_roles = {"protagonist", "antagonist", "ally", "mentor", "comic relief", "mysterious stranger"}
    chars = _generate_characters(20)
    for ch in chars:
        assert ch["role"] in valid_roles


# ── Test: no seed produces varied output ─────────────────────────────────────

def test_no_seed_produces_varied_output():
    """Generator without seed produces varied output across calls."""
    gen = MovieIdeaGenerator()
    ideas = [gen.generate() for _ in range(20)]
    titles = [i["title"] for i in ideas]
    # With 20 ideas from a large pool, expect some variety
    assert len(set(titles)) > 1


# ── Test: genre constraint in batch ──────────────────────────────────────────

def test_batch_with_specific_genre():
    """Batch generation with a specific genre constrains all results."""
    gen = MovieIdeaGenerator(seed=123)
    for genre in GENRES:
        batch = gen.generate_batch(count=3, genre=genre)
        for idea in batch:
            assert idea["genre"] == genre
