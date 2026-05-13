"""
Tests for constants module.
"""

import pytest
from transcript_extractor.constants import (
    SUPPORTED_FORMATS,
    OUTPUT_FORMATS,
    MODEL_SIZES,
    DEFAULT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_SUMMARY_LENGTH,
    DEFAULT_OUTPUT_FORMAT,
    SAMPLE_RATE,
    AUDIO_BITRATE,
    MAX_TRANSCRIPT_LENGTH,
    MAX_SUMMARY_LENGTH,
    MIN_WORD_COUNT_FOR_SUMMARY,
    MAX_INPUT_FILE_SIZE,
    TIMESTAMP_PRECISION,
    KEY_POINTS_COUNT,
    RETRY_COUNT,
    RETRY_DELAY,
    PROGRESS_INTERVAL,
)


class TestConstants:
    """Tests for constants module."""
    
    def test_supported_formats(self):
        """Test that SUPPORTED_FORMATS contains expected formats."""
        assert "mp4" in SUPPORTED_FORMATS
        assert "avi" in SUPPORTED_FORMATS
        assert "mov" in SUPPORTED_FORMATS
        assert "mkv" in SUPPORTED_FORMATS
        assert "mp3" in SUPPORTED_FORMATS
        assert "wav" in SUPPORTED_FORMATS
        assert "flac" in SUPPORTED_FORMATS
        assert "aac" in SUPPORTED_FORMATS
        assert "m4a" in SUPPORTED_FORMATS
    
    def test_output_formats(self):
        """Test that OUTPUT_FORMATS contains expected formats."""
        assert "txt" in OUTPUT_FORMATS
        assert "srt" in OUTPUT_FORMATS
        assert "vtt" in OUTPUT_FORMATS
        assert "json" in OUTPUT_FORMATS
    
    def test_model_sizes(self):
        """Test that MODEL_SIZES contains expected sizes."""
        assert "tiny" in MODEL_SIZES
        assert "small" in MODEL_SIZES
        assert "medium" in MODEL_SIZES
        assert "large" in MODEL_SIZES
        assert "large-v2" in MODEL_SIZES
        assert "large-v3" in MODEL_SIZES
    
    def test_default_model(self):
        """Test that DEFAULT_MODEL is 'small'."""
        assert DEFAULT_MODEL == "small"
    
    def test_default_language(self):
        """Test that DEFAULT_LANGUAGE is 'en'."""
        assert DEFAULT_LANGUAGE == "en"
    
    def test_default_summary_length(self):
        """Test that DEFAULT_SUMMARY_LENGTH is 'medium'."""
        assert DEFAULT_SUMMARY_LENGTH == "medium"
    
    def test_default_output_format(self):
        """Test that DEFAULT_OUTPUT_FORMAT is 'txt'."""
        assert DEFAULT_OUTPUT_FORMAT == "txt"
    
    def test_sample_rate(self):
        """Test that SAMPLE_RATE is 16000."""
        assert SAMPLE_RATE == 16000
    
    def test_audio_bitrate(self):
        """Test that AUDIO_BITRATE is '128k'."""
        assert AUDIO_BITRATE == "128k"
    
    def test_max_transcript_length(self):
        """Test that MAX_TRANSCRIPT_LENGTH is 1000000."""
        assert MAX_TRANSCRIPT_LENGTH == 1000000
    
    def test_max_summary_length(self):
        """Test that MAX_SUMMARY_LENGTH is 500."""
        assert MAX_SUMMARY_LENGTH == 500
    
    def test_min_word_count_for_summary(self):
        """Test that MIN_WORD_COUNT_FOR_SUMMARY is 50."""
        assert MIN_WORD_COUNT_FOR_SUMMARY == 50
    
    def test_max_input_file_size(self):
        """Test that MAX_INPUT_FILE_SIZE is 2GB."""
        assert MAX_INPUT_FILE_SIZE == 2 * 1024 * 1024 * 1024
    
    def test_timestamp_precision(self):
        """Test that TIMESTAMP_PRECISION is 'milliseconds'."""
        assert TIMESTAMP_PRECISION == "milliseconds"
    
    def test_key_points_count(self):
        """Test that KEY_POINTS_COUNT is 5."""
        assert KEY_POINTS_COUNT == 5
    
    def test_retry_count(self):
        """Test that RETRY_COUNT is 3."""
        assert RETRY_COUNT == 3
    
    def test_retry_delay(self):
        """Test that RETRY_DELAY is 1.0."""
        assert RETRY_DELAY == 1.0
    
    def test_progress_interval(self):
        """Test that PROGRESS_INTERVAL is 10."""
        assert PROGRESS_INTERVAL == 10
