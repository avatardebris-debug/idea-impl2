import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from transcript_extractor.audio_extractor import AudioExtractor

class TestAudioExtractor:
    def setup_method(self):
        self.path_patcher = patch("transcript_extractor.audio_extractor.Path.exists", return_value=True)
        self.path_patcher.start()
        
    def teardown_method(self):
        self.path_patcher.stop()

    def test_extract_audio_video_file(self):
        extractor = AudioExtractor(output_dir="/tmp/test")
        
        with patch("transcript_extractor.audio_extractor.get_handler_for_format") as mock_get_handler:
            mock_handler = MagicMock()
            mock_handler.extract_audio.return_value = "test.wav"
            mock_get_handler.return_value = mock_handler
            
            result = extractor.extract_audio("test.mp4")
            
            assert mock_get_handler.called
            mock_handler.extract_audio.assert_called_once()
            assert "test.wav" in result or "test" in result

    def test_extract_audio_audio_file(self):
        extractor = AudioExtractor(output_dir="/tmp/test")
        
        import sys
        mock_ffmpeg = MagicMock()
        mock_ffmpeg.input.return_value.output.return_value.overwrite_output.return_value.run.return_value = None
        
        with patch.dict(sys.modules, {"ffmpeg": mock_ffmpeg}):
            result = extractor.extract_audio("test.mp3")
            assert "test_extracted.wav" in result

    def test_extract_audio_unsupported_format(self):
        extractor = AudioExtractor(output_dir="/tmp/test")
        with pytest.raises(ValueError, match="Unsupported format: .xyz"):
            extractor.extract_audio("test.xyz")

    def test_cleanup_temp_files(self):
        extractor = AudioExtractor(output_dir="/tmp/test")
        
        with patch("transcript_extractor.audio_extractor.Path.glob") as mock_glob:
            mock_file = MagicMock()
            mock_glob.return_value = [mock_file]
            
            count = extractor.cleanup_temp_files()
            
            mock_file.unlink.assert_called_once()
            assert count == 1
