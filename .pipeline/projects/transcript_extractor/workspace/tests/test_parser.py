"""
Comprehensive tests for TranscriptParser class.
"""

import pytest
from unittest.mock import MagicMock

from transcript_extractor.parser import TranscriptParser
from transcript_extractor.formatters.output_formats import TranscriptionResultData


class TestTranscriptParserInit:
    """Tests for TranscriptParser initialization."""
    
    def test_init_default_format(self):
        """Test default output format."""
        parser = TranscriptParser()
        assert parser.output_format == "json"
    
    def test_init_custom_format(self):
        """Test custom output format."""
        parser = TranscriptParser(output_format="txt")
        assert parser.output_format == "txt"


class TestParse:
    """Tests for parse method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TranscriptParser()
    
    def test_parse_default_format(self):
        """Test parse with default format."""
        mock_result = MagicMock(spec=TranscriptionResultData)
        mock_result.text = "Test transcript"
        mock_result.language = "en"
        mock_result.duration = 1.0
        mock_result.word_count = 1
        mock_result.segments_count = 1
        mock_result.segments = []
        
        result = self.parser.parse(mock_result)
        assert result is not None
    
    def test_parse_with_indent(self):
        """Test parse with custom indent."""
        mock_result = MagicMock(spec=TranscriptionResultData)
        mock_result.text = "Test transcript"
        mock_result.language = "en"
        mock_result.duration = 1.0
        mock_result.word_count = 1
        mock_result.segments_count = 1
        mock_result.segments = []
        
        result = self.parser.parse(mock_result, indent=4)
        assert result is not None


class TestParseToTxt:
    """Tests for parse_to_txt method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TranscriptParser()
    
    def test_parse_to_txt(self):
        """Test parsing to TXT format."""
        mock_result = MagicMock(spec=TranscriptionResultData)
        mock_result.text = "Test transcript"
        mock_result.language = "en"
        mock_result.duration = 1.0
        mock_result.word_count = 1
        mock_result.segments_count = 1
        mock_result.segments = []
        
        result = self.parser.parse_to_txt(mock_result)
        assert result is not None
        assert "Test transcript" in result


class TestParseToSrt:
    """Tests for parse_to_srt method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TranscriptParser()
    
    def test_parse_to_srt(self):
        """Test parsing to SRT format."""
        mock_result = MagicMock(spec=TranscriptionResultData)
        mock_result.text = "Test transcript"
        mock_result.language = "en"
        mock_result.duration = 1.0
        mock_result.word_count = 1
        mock_result.segments_count = 1
        mock_result.segments = [{"text": "Test", "start": 0, "end": 1}]
        
        result = self.parser.parse_to_srt(mock_result)
        assert result is not None
        assert "Test" in result


class TestParseToVtt:
    """Tests for parse_to_vtt method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TranscriptParser()
    
    def test_parse_to_vtt(self):
        """Test parsing to VTT format."""
        mock_result = MagicMock(spec=TranscriptionResultData)
        mock_result.text = "Test transcript"
        mock_result.language = "en"
        mock_result.duration = 1.0
        mock_result.word_count = 1
        mock_result.segments_count = 1
        mock_result.segments = [{"text": "Test", "start": 0, "end": 1}]
        
        result = self.parser.parse_to_vtt(mock_result)
        assert result is not None
        assert "Test" in result


class TestParseToJson:
    """Tests for parse_to_json method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TranscriptParser()
    
    def test_parse_to_json(self):
        """Test parsing to JSON format."""
        mock_result = MagicMock(spec=TranscriptionResultData)
        mock_result.text = "Test transcript"
        mock_result.language = "en"
        mock_result.duration = 1.0
        mock_result.word_count = 1
        mock_result.segments_count = 1
        mock_result.segments = []
        
        result = self.parser.parse_to_json(mock_result)
        assert result is not None
        assert "Test transcript" in result
    
    def test_parse_to_json_with_indent(self):
        """Test parsing to JSON with custom indent."""
        mock_result = MagicMock(spec=TranscriptionResultData)
        mock_result.text = "Test transcript"
        mock_result.language = "en"
        mock_result.duration = 1.0
        mock_result.word_count = 1
        mock_result.segments_count = 1
        mock_result.segments = []
        
        result = self.parser.parse_to_json(mock_result, indent=4)
        assert result is not None


class TestUpdateFormat:
    """Tests for update_format method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TranscriptParser()
    
    def test_update_format_to_txt(self):
        """Test updating format to TXT."""
        self.parser.update_format("txt")
        assert self.parser.output_format == "txt"
    
    def test_update_format_to_srt(self):
        """Test updating format to SRT."""
        self.parser.update_format("srt")
        assert self.parser.output_format == "srt"
    
    def test_update_format_to_vtt(self):
        """Test updating format to VTT."""
        self.parser.update_format("vtt")
        assert self.parser.output_format == "vtt"
    
    def test_update_format_to_json(self):
        """Test updating format to JSON."""
        self.parser.update_format("json")
        assert self.parser.output_format == "json"
