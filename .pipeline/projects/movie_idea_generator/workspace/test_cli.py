"""CLI integration tests for the movie_idea_generator CLI."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from movie_idea_generator.cli import main


# ── Helpers ────────────────────────────────────────────────────────────────

def capture_main(argv):
    """Run main() with given argv and capture stdout."""
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = captured = StringIO()
    try:
        main(argv)
    except SystemExit as e:
        output = captured.getvalue()
        sys.stdout = old_stdout
        raise e  # re-raise so tests can inspect the exit code
    output = captured.getvalue()
    sys.stdout = old_stdout
    return output


# ── Test: default output (text format) ─────────────────────────────────────

def test_default_output_is_text():
    """Default output is text format."""
    output = capture_main([])
    assert "🎬" in output
    assert "Genre:" in output
    assert "Logline:" in output
    assert "Characters:" in output


def test_default_output_has_title():
    """Default output contains a title."""
    output = capture_main([])
    lines = output.strip().split("\n")
    assert lines[0].startswith("🎬")


def test_default_output_has_genre():
    """Default output contains a genre line."""
    output = capture_main([])
    assert "Genre:" in output


def test_default_output_has_logline():
    """Default output contains a logline line."""
    output = capture_main([])
    assert "Logline:" in output


# ── Test: JSON output format ───────────────────────────────────────────────

def test_json_output_single_idea():
    """--format json outputs valid JSON for a single idea."""
    output = capture_main(["--format", "json"])
    data = json.loads(output)
    assert isinstance(data, dict)
    assert "title" in data
    assert "genre" in data
    assert "logline" in data
    assert "characters" in data


def test_json_output_multiple_ideas():
    """--format json with count > 1 outputs a JSON array."""
    output = capture_main(["--count", "3", "--format", "json"])
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 3
    for idea in data:
        assert "title" in idea
        assert "genre" in idea


# ── Test: --genre flag ─────────────────────────────────────────────────────

def test_genre_flag_text_output():
    """--genre flag constrains text output to the given genre."""
    output = capture_main(["--genre", "Horror"])
    assert "Genre: Horror" in output


def test_genre_flag_json_output():
    """--genre flag constrains JSON output to the given genre."""
    output = capture_main(["--genre", "Sci-Fi", "--format", "json"])
    data = json.loads(output)
    assert data["genre"] == "Sci-Fi"


def test_genre_flag_all_valid_genres():
    """All valid genres work with --genre flag."""
    valid_genres = ["Action", "Comedy", "Drama", "Horror", "Sci-Fi",
                    "Romance", "Thriller", "Fantasy", "Mystery", "Adventure"]
    for genre in valid_genres:
        output = capture_main(["--genre", genre])
        assert f"Genre: {genre}" in output


# ── Test: --count flag ──────────────────────────────────────────────────────

def test_count_flag_text_output():
    """--count flag produces the correct number of ideas in text output."""
    output = capture_main(["--count", "3"])
    # Each idea starts with 🎬
    emoji_count = output.count("🎬")
    assert emoji_count == 3


def test_count_flag_json_output():
    """--count flag produces the correct number of ideas in JSON output."""
    output = capture_main(["--count", "5", "--format", "json"])
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 5


def test_count_flag_zero():
    """--count 0 produces no output."""
    output = capture_main(["--count", "0"])
    assert output.strip() == ""


# ── Test: --seed flag ───────────────────────────────────────────────────────

def test_seed_flag_reproducibility():
    """--seed flag produces reproducible output."""
    output1 = capture_main(["--seed", "42"])
    output2 = capture_main(["--seed", "42"])
    assert output1 == output2


def test_seed_flag_different_seed_different_output():
    """Different --seed values produce different output."""
    output1 = capture_main(["--seed", "42"])
    output2 = capture_main(["--seed", "43"])
    assert output1 != output2


# ── Test: invalid argument handling ─────────────────────────────────────────

def test_invalid_genre_rejected():
    """Invalid genre raises an error."""
    with pytest.raises(ValueError, match="Invalid genre"):
        capture_main(["--genre", "NonexistentGenre"])


def test_invalid_count_rejected():
    """Negative count raises an error."""
    with pytest.raises(ValueError, match="count must be >= 0"):
        capture_main(["--count", "-1"])


def test_invalid_format_rejected():
    """Invalid format raises an error."""
    with pytest.raises(SystemExit):
        capture_main(["--format", "xml"])


def test_help_flag_exits_cleanly():
    """--help flag exits cleanly."""
    with pytest.raises(SystemExit) as exc_info:
        capture_main(["--help"])
    assert exc_info.value.code == 0
