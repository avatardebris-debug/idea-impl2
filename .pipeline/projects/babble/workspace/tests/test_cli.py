"""
Unit tests for CLI (cli.py).
"""
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from babble.cli import main
from babble.data.default_phrases import DEFAULT_PHRASES


# ---------------------------------------------------------------------------
# main() function tests
# ---------------------------------------------------------------------------

class TestMain:
    def test_main_loads_phrases(self, capsys):
        """Test that main loads phrases and starts session."""
        with patch("builtins.input", return_value="quit"):
            main(language="English", num_phrases=2)
        captured = capsys.readouterr()
        assert "Welcome to Babble" in captured.out
        assert "2 phrases loaded" in captured.out

    def test_main_with_language_filter(self, capsys):
        """Test that main filters by language."""
        with patch("builtins.input", return_value="quit"):
            main(language="Spanish", num_phrases=2)
        captured = capsys.readouterr()
        assert "Language: Spanish" in captured.out

    def test_main_with_invalid_language(self, capsys):
        """Test that main exits with error for invalid language."""
        with pytest.raises(SystemExit) as exc_info:
            main(language="InvalidLanguage", num_phrases=2)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Language 'InvalidLanguage' not found" in captured.out

    def test_main_num_phrases_limit(self, capsys):
        """Test that num_phrases limits the number of phrases."""
        with patch("builtins.input", return_value="quit"):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "1 phrases loaded" in captured.out

    def test_main_known_response(self, capsys):
        """Test that 'known' response marks phrase as known."""
        inputs = iter(["known", "quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "Marked as known" in captured.out

    def test_main_partially_known_response(self, capsys):
        """Test that 'partially_known' response marks phrase as partially known."""
        inputs = iter(["partially_known", "quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "Marked as partially known" in captured.out

    def test_main_new_response(self, capsys):
        """Test that 'new' response resets phrase to new."""
        inputs = iter(["new", "quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "Reset to new" in captured.out

    def test_main_short_responses(self, capsys):
        """Test that short responses (k, p, n) work."""
        inputs = iter(["k", "p", "n", "quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=3)
        captured = capsys.readouterr()
        assert "Marked as known" in captured.out
        assert "Marked as partially known" in captured.out
        assert "Reset to new" in captured.out

    def test_main_quit_responses(self, capsys):
        """Test that quit, q, exit all end the session."""
        for response in ["quit", "q", "exit"]:
            inputs = iter([response])
            with patch("builtins.input", side_effect=lambda _: next(inputs)):
                main(language="English", num_phrases=1)
            captured = capsys.readouterr()
            assert "Thanks for using Babble" in captured.out

    def test_main_unrecognized_response(self, capsys):
        """Test that unrecognized responses are handled."""
        inputs = iter(["unknown_response", "quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "Unrecognized response" in captured.out

    def test_main_eof_error(self, capsys):
        """Test that EOFError ends the session gracefully."""
        with patch("builtins.input", side_effect=EOFError):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "Thanks for using Babble" in captured.out

    def test_main_keyboard_interrupt(self, capsys):
        """Test that KeyboardInterrupt ends the session gracefully."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "Thanks for using Babble" in captured.out

    def test_main_session_summary(self, capsys):
        """Test that session summary is displayed."""
        inputs = iter(["known", "quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        assert "Learning Session Summary" in captured.out

    def test_main_phrase_display(self, capsys):
        """Test that phrase is displayed correctly."""
        inputs = iter(["quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=1)
        captured = capsys.readouterr()
        # Should display the phrase text
        assert "Translation:" in captured.out or "Context:" in captured.out

    def test_main_no_language_all_phrases(self, capsys):
        """Test that without language filter, all phrases are loaded."""
        with patch("builtins.input", return_value="quit"):
            main(num_phrases=5)
        captured = capsys.readouterr()
        assert "Welcome to Babble" in captured.out
        assert "5 phrases loaded" in captured.out

    def test_main_empty_session(self, capsys):
        """Test that main handles empty phrase list."""
        # Use num_phrases=0 to get empty list
        with patch("builtins.input", return_value="quit"):
            main(language="English", num_phrases=0)
        captured = capsys.readouterr()
        assert "0 phrases loaded" in captured.out
        assert "Thanks for using Babble" in captured.out

    def test_main_multiple_phrases(self, capsys):
        """Test that main handles multiple phrases correctly."""
        inputs = iter(["known", "partially_known", "new", "quit"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main(language="English", num_phrases=3)
        captured = capsys.readouterr()
        assert "Learning Session Summary" in captured.out
        assert "Total phrases: 3" in captured.out
        assert "Known: 1" in captured.out
        assert "Partially known: 1" in captured.out
        assert "New: 1" in captured.out
