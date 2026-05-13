"""
Comprehensive tests for TranscriptFormatter class.
"""

import pytest
from unittest.mock import MagicMock

from transcript_extractor.formatters.output_formats import (
    TranscriptFormatter,
    TranscriptionResultData,
    TranscriptionSegment,
)


class TestTranscriptFormatterInit:
    """Tests for TranscriptFormatter initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        formatter = TranscriptFormatter()
        assert formatter is not None


class TestFormatToJson:
    """Tests for format_to_json method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock(spec=TranscriptionResultData)
        self.mock_result.text = "Test transcript"
        self.mock_result.language = "en"
        self.mock_result.duration = 1.0
        self.mock_result.word_count = 1
        self.mock_result.segments_count = 1
        self.mock_result.segments = []
    
    def test_format_to_json_default(self):
        """Test JSON formatting with default indent."""
        result = self.formatter.format_to_json(self.mock_result)
        assert result is not None
        assert "Test transcript" in result
    
    def test_format_to_json_with_indent(self):
        """Test JSON formatting with custom indent."""
        result = self.formatter.format_to_json(self.mock_result, indent=4)
        assert result is not None
        assert "Test transcript" in result
    
    def test_format_to_json_empty_result(self):
        """Test JSON formatting with empty result."""
        empty_result = MagicMock(spec=TranscriptionResultData)
        empty_result.text = ""
        empty_result.language = ""
        empty_result.duration = 0.0
        empty_result.word_count = 0
        empty_result.segments_count = 0
        empty_result.segments = []
        
        result = self.formatter.format_to_json(empty_result)
        assert result is not None


class TestFormatToTxt:
    """Tests for format_to_txt method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock(spec=TranscriptionResultData)
        self.mock_result.text = "Test transcript"
        self.mock_result.language = "en"
        self.mock_result.duration = 1.0
        self.mock_result.word_count = 1
        self.mock_result.segments_count = 1
        self.mock_result.segments = []
    
    def test_format_to_txt_default(self):
        """Test TXT formatting with default options."""
        result = self.formatter.format_to_txt(self.mock_result)
        assert result is not None
        assert "Test transcript" in result
    
    def test_format_to_txt_with_timestamps(self):
        """Test TXT formatting with timestamps."""
        self.mock_result.segments = [
            TranscriptionSegment(
                text="Test",
                start=0.0,
                end=1.0,
                speaker=None
            )
        ]
        
        result = self.formatter.format_to_txt(
            self.mock_result,
            include_timestamps=True
        )
        assert result is not None
        assert "Test" in result
    
    def test_format_to_txt_without_timestamps(self):
        """Test TXT formatting without timestamps."""
        result = self.formatter.format_to_txt(
            self.mock_result,
            include_timestamps=False
        )
        assert result is not None
        assert "Test transcript" in result
    
    def test_format_to_txt_with_metadata(self):
        """Test TXT formatting with metadata."""
        result = self.formatter.format_to_txt(
            self.mock_result,
            include_metadata=True
        )
        assert result is not None
        assert "Language" in result or "language" in result.lower()
    
    def test_format_to_txt_empty_result(self):
        """Test TXT formatting with empty result."""
        empty_result = MagicMock(spec=TranscriptionResultData)
        empty_result.text = ""
        empty_result.language = ""
        empty_result.duration = 0.0
        empty_result.word_count = 0
        empty_result.segments_count = 0
        empty_result.segments = []
        
        result = self.formatter.format_to_txt(empty_result)
        assert result is not None


class TestFormatToSrt:
    """Tests for format_to_srt method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock(spec=TranscriptionResultData)
        self.mock_result.text = "Test transcript"
        self.mock_result.language = "en"
        self.mock_result.duration = 1.0
        self.mock_result.word_count = 1
        self.mock_result.segments_count = 1
        self.mock_result.segments = [
            TranscriptionSegment(
                text="Test",
                start=0.0,
                end=1.0,
                speaker=None
            )
        ]
    
    def test_format_to_srt(self):
        """Test SRT formatting."""
        result = self.formatter.format_to_srt(self.mock_result)
        assert result is not None
        assert "Test" in result
    
    def test_format_to_srt_empty_result(self):
        """Test SRT formatting with empty result."""
        empty_result = MagicMock(spec=TranscriptionResultData)
        empty_result.text = ""
        empty_result.language = ""
        empty_result.duration = 0.0
        empty_result.word_count = 0
        empty_result.segments_count = 0
        empty_result.segments = []
        
        result = self.formatter.format_to_srt(empty_result)
        assert result is not None


class TestFormatToVtt:
    """Tests for format_to_vtt method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = TranscriptFormatter()
        self.mock_result = MagicMock(spec=TranscriptionResultData)
        self.mock_result.text = "Test transcript"
        self.mock_result.language = "en"
        self.mock_result.duration = 1.0
        self.mock_result.word_count = 1
        self.mock_result.segments_count = 1
        self.mock_result.segments = [
            TranscriptionSegment(
                text="Test",
                start=0.0,
                end=1.0,
                speaker=None
            )
        ]
    
    def test_format_to_vtt(self):
        """Test VTT formatting."""
        result = self.formatter.format_to_vtt(self.mock_result)
        assert result is not None
        assert "Test" in result
    
    def test_format_to_vtt_empty_result(self):
        """Test VTT formatting with empty result."""
        empty_result = MagicMock(spec=TranscriptionResultData)
        empty_result.text = ""
        empty_result.language = ""
        empty_result.duration = 0.0
        empty_result.word_count = 0
        empty_result.segments_count = 0
        empty_result.segments = []
        
        result = self.formatter.format_to_vtt(empty_result)
        assert result is not None
