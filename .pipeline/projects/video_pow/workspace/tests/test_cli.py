"""Tests for CLI entry point."""

import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest
from videopow.cli import main


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    def test_required_arguments(self, capsys):
        """Test that required arguments are parsed correctly."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'slow zoom',
            '--input', '/tmp/input.mp4',
            '--output', '/tmp/output.mp4'
        ]):
            with patch('videopow.cli.generate_video', return_value='/tmp/output.mp4'):
                main()
        captured = capsys.readouterr()
        assert "Video generated successfully" in captured.out

    def test_optional_fps_argument(self, capsys):
        """Test that optional fps argument is parsed."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'slow zoom',
            '--input', '/tmp/input.mp4',
            '--output', '/tmp/output.mp4',
            '--fps', '24.0'
        ]):
            with patch('videopow.cli.generate_video', return_value='/tmp/output.mp4') as mock_gen:
                main()
                mock_gen.assert_called_once()
                # Check that fps was passed
                call_kwargs = mock_gen.call_args
                assert call_kwargs[1]['fps'] == 24.0

    def test_default_fps_is_none(self, capsys):
        """Test that fps defaults to None when not provided."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'slow zoom',
            '--input', '/tmp/input.mp4',
            '--output', '/tmp/output.mp4'
        ]):
            with patch('videopow.cli.generate_video', return_value='/tmp/output.mp4') as mock_gen:
                main()
                call_kwargs = mock_gen.call_args
                assert call_kwargs[1]['fps'] is None


class TestCLISuccessCase:
    """Test successful CLI execution."""

    def test_success_message(self, capsys):
        """Test that success message is printed."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'test',
            '--input', '/tmp/input.mp4',
            '--output', '/tmp/output.mp4'
        ]):
            with patch('videopow.cli.generate_video', return_value='/tmp/output.mp4'):
                main()
        captured = capsys.readouterr()
        assert "Video generated successfully" in captured.out
        assert "/tmp/output.mp4" in captured.out

    def test_generate_video_called_with_correct_args(self):
        """Test that generate_video is called with correct arguments."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'slow zoom',
            '--input', '/tmp/input.mp4',
            '--output', '/tmp/output.mp4',
            '--fps', '30.0'
        ]):
            with patch('videopow.cli.generate_video', return_value='/tmp/output.mp4') as mock_gen:
                main()
                mock_gen.assert_called_once_with(
                    description='slow zoom',
                    input_video_path='/tmp/input.mp4',
                    output_path='/tmp/output.mp4',
                    fps=30.0
                )


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_file_not_found_error(self, capsys):
        """Test that FileNotFoundError is handled."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'test',
            '--input', '/nonexistent.mp4',
            '--output', '/tmp/output.mp4'
        ]):
            with patch('videopow.cli.generate_video', side_effect=FileNotFoundError("File not found")):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_generic_error(self, capsys):
        """Test that generic exceptions are handled."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'test',
            '--input', '/tmp/input.mp4',
            '--output', '/tmp/output.mp4'
        ]):
            with patch('videopow.cli.generate_video', side_effect=Exception("Something went wrong")):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_error_output_to_stderr(self, capsys):
        """Test that errors go to stderr."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'test',
            '--input', '/nonexistent.mp4',
            '--output', '/tmp/output.mp4'
        ]):
            with patch('videopow.cli.generate_video', side_effect=FileNotFoundError("File not found")):
                with pytest.raises(SystemExit):
                    main()
        captured = capsys.readouterr()
        assert captured.err != ""  # stderr should not be empty


class TestCLIMissingArguments:
    """Test CLI behavior with missing arguments."""

    def test_missing_description(self, capsys):
        """Test that missing description raises error."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--input', '/tmp/input.mp4',
            '--output', '/tmp/output.mp4'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2  # argparse exit code for missing args

    def test_missing_input(self, capsys):
        """Test that missing input raises error."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'test',
            '--output', '/tmp/output.mp4'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_missing_output(self, capsys):
        """Test that missing output raises error."""
        with patch.object(sys, 'argv', [
            'videopow',
            '--description', 'test',
            '--input', '/tmp/input.mp4'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2
