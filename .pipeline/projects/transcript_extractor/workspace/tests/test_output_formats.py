"""
Comprehensive tests for TranscriptFormatter class.
"""

import pytest
from unittest.mock import MagicMock, patch

from transcript_extractor.formatters.output_formats import TranscriptFormatter


class TestTranscriptFormatterInit:
    """Tests for TranscriptFormatter initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        formatter = TranscriptFormatter()
        assert formatter is not None


class TestFormatToTxt:
    """Tests for TXT format output."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock()
        self.mock_result.text = "Hello world. This is a test."
        self.mock_result.word_count = 6
        self.mock_result.duration = 10.5
        self.mock_result.language = "en"
        self.mock_result.segments = [
            MagicMock(text="Hello world.", start=0.0, end=2.0),
            MagicMock(text="This is a test.", start=2.0, end=5.0),
        ]
    
    def test_format_to_txt_basic(self):
        """Test basic TXT formatting."""
        result = self.formatter.format_to_txt(self.mock_result)
        assert result is not None
        assert isinstance(result, str)
        assert "Hello world" in result
    
    def test_format_to_txt_with_timestamps(self):
        """Test TXT formatting with timestamps."""
        result = self.formatter.format_to_txt(
            self.mock_result,
            include_timestamps=True
        )
        assert result is not None
        assert "00:00:00" in result or "0.0" in result
    
    def test_format_to_txt_without_timestamps(self):
        """Test TXT formatting without timestamps."""
        result = self.formatter.format_to_txt(
            self.mock_result,
            include_timestamps=False
        )
        assert result is not None
        # Should not contain timestamp patterns
        assert "00:00:00" not in result
    
    def test_format_to_txt_with_metadata(self):
        """Test TXT formatting with metadata."""
        result = self.formatter.format_to_txt(
            self.mock_result,
            include_metadata=True
        )
        assert result is not None
        assert "Word Count" in result or "word_count" in result.lower()
        assert "Duration" in result or "duration" in result.lower()
        assert "Language" in result or "language" in result.lower()
    
    def test_format_to_txt_without_metadata(self):
        """Test TXT formatting without metadata."""
        result = self.formatter.format_to_txt(
            self.mock_result,
            include_metadata=False
        )
        assert result is not None
        # Should not contain metadata headers
        assert "Word Count" not in result
        assert "Duration" not in result
    
    def test_format_to_txt_empty_text(self):
        """Test TXT formatting with empty text."""
        self.mock_result.text = ""
        result = self.formatter.format_to_txt(self.mock_result)
        assert result is not None
        assert result == ""
    
    def test_format_to_txt_none_result(self):
        """Test TXT formatting with None result."""
        result = self.formatter.format_to_txt(None)
        assert result is not None
        assert result == ""


class TestFormatToSrt:
    """Tests for SRT format output."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock()
        self.mock_result.text = "Hello world. This is a test."
        self.mock_result.word_count = 6
        self.mock_result.duration = 10.5
        self.mock_result.language = "en"
        self.mock_result.segments = [
            MagicMock(text="Hello world.", start=0.0, end=2.0),
            MagicMock(text="This is a test.", start=2.0, end=5.0),
        ]
    
    def test_format_to_srt_basic(self):
        """Test basic SRT formatting."""
        result = self.formatter.format_to_srt(self.mock_result)
        assert result is not None
        assert isinstance(result, str)
        assert "Hello world" in result
        # SRT format should have sequence numbers
        assert "1" in result
        assert "2" in result
    
    def test_format_to_srt_timestamps(self):
        """Test SRT formatting with proper timestamps."""
        result = self.formatter.format_to_srt(self.mock_result)
        assert result is not None
        # SRT timestamps should be in HH:MM:SS,mmm format
        assert "00:00:00" in result or "00:00:02" in result
    
    def test_format_to_srt_empty_text(self):
        """Test SRT formatting with empty text."""
        self.mock_result.text = ""
        result = self.formatter.format_to_srt(self.mock_result)
        assert result is not None
        assert result == ""
    
    def test_format_to_srt_none_result(self):
        """Test SRT formatting with None result."""
        result = self.formatter.format_to_srt(None)
        assert result is not None
        assert result == ""


class TestFormatToVtt:
    """Tests for VTT format output."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock()
        self.mock_result.text = "Hello world. This is a test."
        self.mock_result.word_count = 6
        self.mock_result.duration = 10.5
        self.mock_result.language = "en"
        self.mock_result.segments = [
            MagicMock(text="Hello world.", start=0.0, end=2.0),
            MagicMock(text="This is a test.", start=2.0, end=5.0),
        ]
    
    def test_format_to_vtt_basic(self):
        """Test basic VTT formatting."""
        result = self.formatter.format_to_vtt(self.mock_result)
        assert result is not None
        assert isinstance(result, str)
        assert "WEBVTT" in result
        assert "Hello world" in result
    
    def test_format_to_vtt_timestamps(self):
        """Test VTT formatting with proper timestamps."""
        result = self.formatter.format_to_vtt(self.mock_result)
        assert result is not None
        # VTT timestamps should be in HH:MM:SS.mmm format
        assert "00:00:00.000" in result or "00:00:02.000" in result
    
    def test_format_to_vtt_empty_text(self):
        """Test VTT formatting with empty text."""
        self.mock_result.text = ""
        result = self.formatter.format_to_vtt(self.mock_result)
        assert result is not None
        assert "WEBVTT" in result
        assert result.strip() == "WEBVTT"
    
    def test_format_to_vtt_none_result(self):
        """Test VTT formatting with None result."""
        result = self.formatter.format_to_vtt(None)
        assert result is not None
        assert result == ""


class TestFormatToJson:
    """Tests for JSON format output."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock()
        self.mock_result.text = "Hello world. This is a test."
        self.mock_result.word_count = 6
        self.mock_result.duration = 10.5
        self.mock_result.language = "en"
        self.mock_result.segments = [
            MagicMock(text="Hello world.", start=0.0, end=2.0),
            MagicMock(text="This is a test.", start=2.0, end=5.0),
        ]
    
    def test_format_to_json_basic(self):
        """Test basic JSON formatting."""
        result = self.formatter.format_to_json(self.mock_result)
        assert result is not None
        assert isinstance(result, str)
        assert "Hello world" in result
        assert "word_count" in result
        assert "duration" in result
    
    def test_format_to_json_valid_json(self):
        """Test that JSON output is valid JSON."""
        import json
        result = self.formatter.format_to_json(self.mock_result)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert "text" in parsed
        assert "word_count" in parsed
        assert "duration" in parsed
        assert "language" in parsed
        assert "segments" in parsed
    
    def test_format_to_json_with_metadata(self):
        """Test JSON formatting with metadata."""
        result = self.formatter.format_to_json(
            self.mock_result,
            include_metadata=True
        )
        assert result is not None
        assert "metadata" in result
    
    def test_format_to_json_without_metadata(self):
        """Test JSON formatting without metadata."""
        result = self.formatter.format_to_json(
            self.mock_result,
            include_metadata=False
        )
        assert result is not None
        # Should not contain metadata key if not included
        parsed = __import__('json').loads(result)
        assert "metadata" not in parsed
    
    def test_format_to_json_empty_text(self):
        """Test JSON formatting with empty text."""
        self.mock_result.text = ""
        result = self.formatter.format_to_json(self.mock_result)
        assert result is not None
        parsed = __import__('json').loads(result)
        assert parsed["text"] == ""
    
    def test_format_to_json_none_result(self):
        """Test JSON formatting with None result."""
        result = self.formatter.format_to_json(None)
        assert result is not None
        assert result == ""


class TestFormatToAudio:
    """Tests for audio format output."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock()
        self.mock_result.text = "Hello world."
        self.mock_result.word_count = 2
        self.mock_result.duration = 2.0
        self.mock_result.language = "en"
        self.mock_result.segments = [
            MagicMock(text="Hello world.", start=0.0, end=2.0),
        ]
    
    def test_format_to_audio_wav(self):
        """Test WAV audio formatting."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.formatter.format_to_audio(
                self.mock_result,
                output_format="wav"
            )
            assert result is not None
            assert result["status"] == "success"
            assert "audio_path" in result
    
    def test_format_to_audio_flac(self):
        """Test FLAC audio formatting."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.formatter.format_to_audio(
                self.mock_result,
                output_format="flac"
            )
            assert result is not None
            assert result["status"] == "success"
            assert "audio_path" in result
    
    def test_format_to_audio_aac(self):
        """Test AAC audio formatting."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.formatter.format_to_audio(
                self.mock_result,
                output_format="aac"
            )
            assert result is not None
            assert result["status"] == "success"
            assert "audio_path" in result
    
    def test_format_to_audio_m4a(self):
        """Test M4A audio formatting."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.formatter.format_to_audio(
                self.mock_result,
                output_format="m4a"
            )
            assert result is not None
            assert result["status"] == "success"
            assert "audio_path" in result
    
    def test_format_to_audio_invalid_format(self):
        """Test audio formatting with invalid format."""
        result = self.formatter.format_to_audio(
            self.mock_result,
            output_format="invalid"
        )
        assert result is not None
        assert result["status"] == "error"
        assert "error" in result
    
    def test_format_to_audio_ffmpeg_failure(self):
        """Test audio formatting when ffmpeg fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = self.formatter.format_to_audio(
                self.mock_result,
                output_format="wav"
            )
            assert result is not None
            assert result["status"] == "error"
            assert "error" in result
    
    def test_format_to_audio_empty_text(self):
        """Test audio formatting with empty text."""
        self.mock_result.text = ""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.formatter.format_to_audio(
                self.mock_result,
                output_format="wav"
            )
            assert result is not None
            assert result["status"] == "success"
    
    def test_format_to_audio_none_result(self):
        """Test audio formatting with None result."""
        result = self.formatter.format_to_audio(None, output_format="wav")
        assert result is not None
        assert result["status"] == "error"


class TestFormatToAll:
    """Tests for formatting to all formats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock()
        self.mock_result.text = "Hello world."
        self.mock_result.word_count = 2
        self.mock_result.duration = 2.0
        self.mock_result.language = "en"
        self.mock_result.segments = [
            MagicMock(text="Hello world.", start=0.0, end=2.0),
        ]
    
    def test_format_to_all_txt(self):
        """Test formatting to TXT."""
        result = self.formatter.format_to_all(self.mock_result, "txt")
        assert result is not None
        assert isinstance(result, str)
        assert "Hello world" in result
    
    def test_format_to_all_srt(self):
        """Test formatting to SRT."""
        result = self.formatter.format_to_all(self.mock_result, "srt")
        assert result is not None
        assert isinstance(result, str)
        assert "Hello world" in result
    
    def test_format_to_all_vtt(self):
        """Test formatting to VTT."""
        result = self.formatter.format_to_all(self.mock_result, "vtt")
        assert result is not None
        assert isinstance(result, str)
        assert "WEBVTT" in result
    
    def test_format_to_all_json(self):
        """Test formatting to JSON."""
        result = self.formatter.format_to_all(self.mock_result, "json")
        assert result is not None
        assert isinstance(result, str)
        assert "Hello world" in result
    
    def test_format_to_all_invalid_format(self):
        """Test formatting with invalid format."""
        result = self.formatter.format_to_all(self.mock_result, "invalid")
        assert result is not None
        assert result == ""
    
    def test_format_to_all_none_result(self):
        """Test formatting with None result."""
        result = self.formatter.format_to_all(None, "txt")
        assert result is not None
        assert result == ""
