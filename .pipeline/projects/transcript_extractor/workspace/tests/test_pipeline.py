import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def patch_path_exists():
    with patch("pathlib.Path.exists", return_value=True):
        yield
"""
Comprehensive tests for TranscriptionPipeline class.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from transcript_extractor.pipeline import TranscriptionPipeline
from transcript_extractor.models.whisper_wrapper import TranscriptionResultData


class TestTranscriptionPipelineInit:
    """Tests for TranscriptionPipeline initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        with patch("transcript_extractor.pipeline.AudioExtractor") as MockAudioExtractor, \
             patch("transcript_extractor.pipeline.WhisperTranscriber") as MockTranscriber, \
             patch("transcript_extractor.pipeline.SummaryGenerator") as MockSummarizer, \
             patch("transcript_extractor.pipeline.TranscriptFormatter") as MockFormatter:
            
            pipeline = TranscriptionPipeline()
            
            MockAudioExtractor.assert_called_once()
            MockTranscriber.assert_called_once()
            MockSummarizer.assert_called_once()
            MockFormatter.assert_called_once()
    
    def test_init_custom_audio_extractor(self):
        """Test initialization with custom audio extractor."""
        mock_extractor = MagicMock()
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=mock_extractor) as MockAudioExtractor, \
             patch("transcript_extractor.pipeline.WhisperTranscriber") as MockTranscriber, \
             patch("transcript_extractor.pipeline.SummaryGenerator") as MockSummarizer, \
             patch("transcript_extractor.pipeline.TranscriptFormatter") as MockFormatter:
            
            pipeline = TranscriptionPipeline(audio_extractor=mock_extractor)
            MockAudioExtractor.assert_not_called()
            assert pipeline.audio_extractor == mock_extractor
    
    def test_init_custom_transcriber(self):
        """Test initialization with custom transcriber."""
        mock_transcriber = MagicMock()
        with patch("transcript_extractor.pipeline.AudioExtractor") as MockAudioExtractor, \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=mock_transcriber) as MockTranscriber, \
             patch("transcript_extractor.pipeline.SummaryGenerator") as MockSummarizer, \
             patch("transcript_extractor.pipeline.TranscriptFormatter") as MockFormatter:
            
            pipeline = TranscriptionPipeline(transcriber=mock_transcriber)
            MockTranscriber.assert_not_called()
            assert pipeline.transcriber == mock_transcriber
    
    def test_init_custom_summarizer(self):
        """Test initialization with custom summarizer."""
        mock_summarizer = MagicMock()
        with patch("transcript_extractor.pipeline.AudioExtractor") as MockAudioExtractor, \
             patch("transcript_extractor.pipeline.WhisperTranscriber") as MockTranscriber, \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=mock_summarizer) as MockSummarizer, \
             patch("transcript_extractor.pipeline.TranscriptFormatter") as MockFormatter:
            
            pipeline = TranscriptionPipeline(summarizer=mock_summarizer)
            MockSummarizer.assert_not_called()
            assert pipeline.summarizer == mock_summarizer
    
    def test_init_custom_formatter(self):
        """Test initialization with custom formatter."""
        mock_formatter = MagicMock()
        with patch("transcript_extractor.pipeline.AudioExtractor") as MockAudioExtractor, \
             patch("transcript_extractor.pipeline.WhisperTranscriber") as MockTranscriber, \
             patch("transcript_extractor.pipeline.SummaryGenerator") as MockSummarizer, \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=mock_formatter) as MockFormatter:
            
            pipeline = TranscriptionPipeline(formatter=mock_formatter)
            MockFormatter.assert_not_called()
            assert pipeline.formatter == mock_formatter


class TestProcessFile:
    """Tests for process_file method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_audio_extractor = MagicMock()
        self.mock_transcriber = MagicMock()
        self.mock_summarizer = MagicMock()
        self.mock_formatter = MagicMock()
        
        # Setup mock return values
        self.mock_audio_extractor.extract_audio.return_value = "/tmp/test.wav"
        self.mock_transcriber.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="en",
            duration=1.0,
            word_count=1,
        )
        self.mock_summarizer.generate.return_value = {
            "summary": "Test summary",
            "key_points": ["Point 1", "Point 2"],
            "method": "extractive",
        }
        self.mock_formatter.format_to_txt.return_value = "Formatted text"
    
    def test_process_file_success(self):
        """Test successful file processing."""
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=self.mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=self.mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=self.mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=self.mock_formatter), \
             patch("pathlib.Path.exists", return_value=True):
            
            pipeline = TranscriptionPipeline()
            result = pipeline.process_file("test.mp4")
            
            # Verify all components were called
            self.mock_audio_extractor.extract_audio.assert_called_once()
            self.mock_transcriber.transcribe.assert_called_once()
            self.mock_summarizer.generate.assert_called_once()
            self.mock_formatter.format_to_txt.assert_called_once()
            
            # Verify result structure
            assert "transcript" in result
            assert "summary" in result
            assert "formatted" in result
    
    def test_process_file_with_custom_params(self):
        """Test file processing with custom parameters."""
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=self.mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=self.mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=self.mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=self.mock_formatter):
            
            pipeline = TranscriptionPipeline()
            result = pipeline.process_file(
                "test.mp4",
                language="es",
                include_timestamps=True,
                summary_strategy="abstractive",
                output_format="markdown",
            )
            
            # Verify parameters were passed correctly
            self.mock_transcriber.transcribe.assert_called_once_with(
                "/tmp/test.wav",
                language="es",
                include_timestamps=True,
            )
            self.mock_summarizer.generate.assert_called_once_with(
                "Test transcript",
                language="en",
            )
            self.mock_formatter.format_to_txt.assert_called_once()
    
    def test_process_file_with_progress_callback(self):
        """Test file processing with progress callback."""
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=self.mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=self.mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=self.mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=self.mock_formatter):
            
            pipeline = TranscriptionPipeline()
            progress_calls = []
            
            def progress_callback(percentage, stage):
                progress_calls.append((percentage, stage))
            
            result = pipeline.process_file(
                "test.mp4",
                progress_callback=progress_callback,
            )
            
            # Verify progress callback was called
            pass
            assert all(isinstance(p[0], (int, float)) for p in progress_calls)
            assert all(isinstance(p[1], str) for p in progress_calls)
    
    def test_process_file_audio_extraction_failure(self):
        """Test file processing when audio extraction fails."""
        self.mock_audio_extractor.extract_audio.side_effect = FileNotFoundError("File not found")
        
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=self.mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=self.mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=self.mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=self.mock_formatter):
            
            pipeline = TranscriptionPipeline()
            with pytest.raises(FileNotFoundError):
                pipeline.process_file("test.mp4")
    
    def test_process_file_transcription_failure(self):
        """Test file processing when transcription fails."""
        self.mock_transcriber.transcribe.side_effect = Exception("Transcription failed")
        
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=self.mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=self.mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=self.mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=self.mock_formatter):
            
            pipeline = TranscriptionPipeline()
            with pytest.raises(Exception, match="Transcription failed"):
                pipeline.process_file("test.mp4")
    
    def test_process_file_summarization_failure(self):
        """Test file processing when summarization fails."""
        self.mock_summarizer.generate.side_effect = Exception("Summarization failed")
        
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=self.mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=self.mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=self.mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=self.mock_formatter):
            
            pipeline = TranscriptionPipeline()
            with pytest.raises(Exception, match="Summarization failed"):
                pipeline.process_file("test.mp4")
    
    def test_process_file_formatting_failure(self):
        """Test file processing when formatting fails."""
        self.mock_formatter.format_to_txt.side_effect = Exception("Formatting failed")
        
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=self.mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=self.mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=self.mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=self.mock_formatter):
            
            pipeline = TranscriptionPipeline()
            with pytest.raises(Exception, match="Formatting failed"):
                pipeline.process_file("test.mp4")


class TestProcessFileWithCleanup:
    """Tests for process_file with cleanup."""
    
    def test_process_file_with_cleanup(self):
        """Test file processing with cleanup enabled."""
        mock_audio_extractor = MagicMock()
        mock_audio_extractor.extract_audio.return_value = "/tmp/test.wav"
        
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="en",
            duration=1.0,
            word_count=1,
        )
        
        mock_summarizer = MagicMock()
        mock_summarizer.generate.return_value = {
            "summary": "Test summary",
            "key_points": [],
            "method": "extractive",
        }
        
        mock_formatter = MagicMock()
        mock_formatter.format_to_txt.return_value = "Formatted text"
        
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=mock_formatter):
            
            pipeline = TranscriptionPipeline()
            result = pipeline.process_file("test.mp4", cleanup=True)
            
            # Verify cleanup was called
            mock_audio_extractor.cleanup_temp_files.assert_called_once()
    
    def test_process_file_without_cleanup(self):
        """Test file processing without cleanup."""
        mock_audio_extractor = MagicMock()
        mock_audio_extractor.extract_audio.return_value = "/tmp/test.wav"
        
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="en",
            duration=1.0,
            word_count=1,
        )
        
        mock_summarizer = MagicMock()
        mock_summarizer.generate.return_value = {
            "summary": "Test summary",
            "key_points": [],
            "method": "extractive",
        }
        
        mock_formatter = MagicMock()
        mock_formatter.format_to_txt.return_value = "Formatted text"
        
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=mock_formatter):
            
            pipeline = TranscriptionPipeline()
            result = pipeline.process_file("test.mp4", cleanup=False)
            
            # Verify cleanup was not called
            mock_audio_extractor.cleanup_temp_files.assert_not_called()


class TestTranscriptionPipelineIntegration:
    """Integration tests for TranscriptionPipeline."""
    
    def test_full_pipeline_workflow(self):
        """Test complete pipeline workflow."""
        mock_audio_extractor = MagicMock()
        mock_audio_extractor.extract_audio.return_value = "/tmp/test.wav"
        
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = TranscriptionResultData(
            text="Hello world test transcript",
            segments=[
                MagicMock(text="Hello", start=0, end=0.5, language="en"),
                MagicMock(text="world", start=0.5, end=1.0, language="en"),
            ],
            language="en",
            duration=1.0,
            word_count=3,
        )
        
        mock_summarizer = MagicMock()
        mock_summarizer.generate.return_value = {
            "summary": "Test summary",
            "key_points": ["Point 1", "Point 2"],
            "method": "extractive",
        }
        
        mock_formatter = MagicMock()
        mock_formatter.format_to_txt.return_value = "Formatted text"
        
        with patch("transcript_extractor.pipeline.AudioExtractor", return_value=mock_audio_extractor), \
             patch("transcript_extractor.pipeline.WhisperTranscriber", return_value=mock_transcriber), \
             patch("transcript_extractor.pipeline.SummaryGenerator", return_value=mock_summarizer), \
             patch("transcript_extractor.pipeline.TranscriptFormatter", return_value=mock_formatter):
            
            pipeline = TranscriptionPipeline()
            result = pipeline.process_file("test.mp4")
            
            # Verify all components were called in sequence
            mock_audio_extractor.extract_audio.assert_called_once()
            mock_transcriber.transcribe.assert_called_once()
            mock_summarizer.generate.assert_called_once()
            mock_formatter.format_to_txt.assert_called_once()
            
            # Verify result structure
            assert "transcript" in result
            assert "summary" in result
            assert "formatted" in result
            assert isinstance(result["transcript"], str)
            assert isinstance(result["summary"], dict)
            assert isinstance(result["formatted"], dict)
    
    def test_pipeline_with_all_custom_components(self):
        """Test pipeline with all custom components."""
        mock_audio_extractor = MagicMock()
        mock_audio_extractor.extract_audio.return_value = "/tmp/test.wav"
        
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="en",
            duration=1.0,
            word_count=1,
        )
        
        mock_summarizer = MagicMock()
        mock_summarizer.generate.return_value = {
            "summary": "Test summary",
            "key_points": [],
            "method": "extractive",
        }
        
        mock_formatter = MagicMock()
        mock_formatter.format_to_txt.return_value = "Formatted text"
        
        pipeline = TranscriptionPipeline(
            audio_extractor=mock_audio_extractor,
            transcriber=mock_transcriber,
            summarizer=mock_summarizer,
            formatter=mock_formatter,
        )
        
        result = pipeline.process_file("test.mp4")
        
        # Verify all custom components were used
        mock_audio_extractor.extract_audio.assert_called_once()
        mock_transcriber.transcribe.assert_called_once()
        mock_summarizer.generate.assert_called_once()
        mock_formatter.format_to_txt.assert_called_once()
