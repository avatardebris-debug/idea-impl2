"""
Comprehensive tests for AudioExtractor class.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from transcript_extractor.audio_extractor import AudioExtractor, SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_FORMATS


class TestAudioExtractorInit:
    """Tests for AudioExtractor initialization."""
    
    def test_init_default_output_dir(self):
        """Test default output directory initialization."""
        extractor = AudioExtractor()
        assert extractor.output_dir is not None
        assert Path(extractor.output_dir).exists()
    
    def test_init_custom_output_dir(self):
        """Test custom output directory initialization."""
        custom_dir = "/tmp/test_audio_output"
        extractor = AudioExtractor(output_dir=custom_dir)
        assert extractor.output_dir == custom_dir
        assert Path(custom_dir).exists()
    
    def test_init_creates_directory(self):
        """Test that initialization creates output directory."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_dir = Path(temp_dir) / "new_dir"
            extractor = AudioExtractor(output_dir=str(custom_dir))
            assert custom_dir.exists()


class TestIsSupportedFormat:
    """Tests for is_supported_format method."""
    
    def test_supported_audio_formats(self):
        """Test supported audio formats."""
        extractor = AudioExtractor()
        for fmt in SUPPORTED_AUDIO_FORMATS:
            assert extractor.is_supported_format(f"test{fmt}") is True
    
    def test_supported_video_formats(self):
        """Test supported video formats."""
        extractor = AudioExtractor()
        for fmt in SUPPORTED_VIDEO_FORMATS:
            assert extractor.is_supported_format(f"test{fmt}") is True
    
    def test_unsupported_format(self):
        """Test unsupported format."""
        extractor = AudioExtractor()
        assert extractor.is_supported_format("test.txt") is False
        assert extractor.is_supported_format("test.pdf") is False
        assert extractor.is_supported_format("test.exe") is False
    
    def test_case_insensitive(self):
        """Test case insensitive format checking."""
        extractor = AudioExtractor()
        assert extractor.is_supported_format("test.WAV") is True
        assert extractor.is_supported_format("test.MP4") is True
        assert extractor.is_supported_format("test.Mp3") is True


class TestExtractAudio:
    """Tests for extract_audio method."""
    
    def test_extract_audio_video_file(self):
        """Test extracting audio from video file."""
        with patch("transcript_extractor.audio_extractor.get_handler_for_format") as mock_get_handler:
            mock_handler = MagicMock()
            mock_handler.extract_audio.return_value = "/tmp/output.wav"
            mock_get_handler.return_value = mock_handler
            
            extractor = AudioExtractor(output_dir="/tmp")
            result = extractor.extract_audio("test.mp4")
            
            assert result == "/tmp/output.wav"
            mock_handler.extract_audio.assert_called_once()
    
    def test_extract_audio_audio_file(self):
        """Test extracting audio from audio file."""
        with patch("transcript_extractor.audio_extractor.ffmpeg") as mock_ffmpeg:
            mock_ffmpeg_input = MagicMock()
            mock_ffmpeg_input.output.return_value = MagicMock()
            mock_ffmpeg_input.output.return_value.overwrite_output.return_value = MagicMock()
            mock_ffmpeg_input.output.return_value.overwrite_output.return_value.run = MagicMock()
            mock_ffmpeg.input.return_value = mock_ffmpeg_input
            
            extractor = AudioExtractor(output_dir="/tmp")
            result = extractor.extract_audio("test.wav")
            
            assert result is not None
            mock_ffmpeg.input.assert_called_once()
    
    def test_extract_audio_with_custom_filename(self):
        """Test extracting audio with custom filename."""
        with patch("transcript_extractor.audio_extractor.get_handler_for_format") as mock_get_handler:
            mock_handler = MagicMock()
            mock_handler.extract_audio.return_value = "/tmp/custom_output.wav"
            mock_get_handler.return_value = mock_handler
            
            extractor = AudioExtractor(output_dir="/tmp")
            result = extractor.extract_audio("test.mp4", output_filename="custom_output.wav")
            
            assert "custom_output.wav" in result
    
    def test_extract_audio_with_sample_rate(self):
        """Test extracting audio with custom sample rate."""
        with patch("transcript_extractor.audio_extractor.ffmpeg") as mock_ffmpeg:
            mock_ffmpeg_input = MagicMock()
            mock_ffmpeg_input.output.return_value = MagicMock()
            mock_ffmpeg_input.output.return_value.overwrite_output.return_value = MagicMock()
            mock_ffmpeg_input.output.return_value.overwrite_output.return_value.run = MagicMock()
            mock_ffmpeg.input.return_value = mock_ffmpeg_input
            
            extractor = AudioExtractor(output_dir="/tmp")
            result = extractor.extract_audio("test.wav", sample_rate=44100)
            
            assert result is not None
    
    def test_extract_audio_file_not_found(self):
        """Test extracting audio from non-existent file."""
        extractor = AudioExtractor(output_dir="/tmp")
        with pytest.raises(FileNotFoundError):
            extractor.extract_audio("nonexistent.mp4")
    
    def test_extract_audio_unsupported_format(self):
        """Test extracting audio from unsupported format."""
        extractor = AudioExtractor(output_dir="/tmp")
        with pytest.raises(ValueError, match="Unsupported format"):
            extractor.extract_audio("test.txt")
    
    def test_extract_audio_auto_filename(self):
        """Test auto-generated filename."""
        with patch("transcript_extractor.audio_extractor.get_handler_for_format") as mock_get_handler:
            mock_handler = MagicMock()
            mock_handler.extract_audio.return_value = "/tmp/test_extracted.wav"
            mock_get_handler.return_value = mock_handler
            
            extractor = AudioExtractor(output_dir="/tmp")
            result = extractor.extract_audio("test.mp4")
            
            assert "test_extracted.wav" in result


class TestCleanupTempFiles:
    """Tests for cleanup_temp_files method."""
    
    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some temp files
            Path(temp_dir, "test1_extracted.wav").touch()
            Path(temp_dir, "test2_extracted.wav").touch()
            Path(temp_dir, "test3_extracted.wav").touch()
            
            extractor = AudioExtractor(output_dir=temp_dir)
            count = extractor.cleanup_temp_files()
            
            assert count == 3
            assert not Path(temp_dir, "test1_extracted.wav").exists()
            assert not Path(temp_dir, "test2_extracted.wav").exists()
            assert not Path(temp_dir, "test3_extracted.wav").exists()
    
    def test_cleanup_no_temp_files(self):
        """Test cleanup when no temp files exist."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            extractor = AudioExtractor(output_dir=temp_dir)
            count = extractor.cleanup_temp_files()
            
            assert count == 0
    
    def test_cleanup_custom_dir(self):
        """Test cleanup with custom directory."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temp file in custom dir
            Path(temp_dir, "test_extracted.wav").touch()
            
            extractor = AudioExtractor(output_dir="/tmp")
            count = extractor.cleanup_temp_files(temp_dir=temp_dir)
            
            assert count == 1
            assert not Path(temp_dir, "test_extracted.wav").exists()


class TestAudioExtractorIntegration:
    """Integration tests for AudioExtractor."""
    
    def test_extract_and_cleanup_workflow(self):
        """Test complete extract and cleanup workflow."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy audio file
            dummy_file = Path(temp_dir, "test.wav")
            dummy_file.touch()
            
            extractor = AudioExtractor(output_dir=temp_dir)
            
            # Mock ffmpeg for audio extraction
            with patch("transcript_extractor.audio_extractor.ffmpeg") as mock_ffmpeg:
                mock_ffmpeg_input = MagicMock()
                mock_ffmpeg_input.output.return_value = MagicMock()
                mock_ffmpeg_input.output.return_value.overwrite_output.return_value = MagicMock()
                mock_ffmpeg_input.output.return_value.overwrite_output.return_value.run = MagicMock()
                mock_ffmpeg.input.return_value = mock_ffmpeg_input
                
                result = extractor.extract_audio(str(dummy_file))
                assert result is not None
            
            # Cleanup
            count = extractor.cleanup_temp_files()
            assert count >= 0
