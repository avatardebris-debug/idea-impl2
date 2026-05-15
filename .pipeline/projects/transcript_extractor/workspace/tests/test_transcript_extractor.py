# Transcript Extractor - Unit Tests

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from transcript_extractor import (
    Config,
    SUPPORTED_FORMATS,
    OUTPUT_FORMATS,
    MODEL_SIZES,
    AudioExtractor,
    WhisperTranscriber,
    TranscriptParser,
    TranscriptFormatter,
    SummaryGenerator,
    TranscriptionPipeline,
    TranscriptionOutput,
    TranscriptionSegment,
    TranscriptionResultData,
)


class TestConfig:
    """Tests for the Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.model_path is not None
        assert config.output_dir is not None
        assert config.temp_dir is not None

    def test_config_creates_directories(self):
        """Test that config creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, 'output')
            config = Config(output_dir=output_dir)
            assert os.path.exists(output_dir)


class TestAudioExtractor:
    """Tests for the AudioExtractor class."""

    def test_is_supported_format(self):
        """Test format validation."""
        extractor = AudioExtractor()
        assert extractor.is_supported_format('test.mp4') is True
        assert extractor.is_supported_format('test.avi') is True
        assert extractor.is_supported_format('test.mov') is True
        assert extractor.is_supported_format('test.mkv') is True
        assert extractor.is_supported_format('test.mp3') is True
        assert extractor.is_supported_format('test.wav') is True
        assert extractor.is_supported_format('test.flac') is True
        assert extractor.is_supported_format('test.aac') is True
        assert extractor.is_supported_format('test.m4a') is True
        assert extractor.is_supported_format('test.movi') is False

    @patch('transcript_extractor.audio_extractor.get_handler_for_format')
    def test_extract_audio_success(self, mock_handler):
        """Test successful audio extraction."""
        mock_handler_instance = Mock()
        mock_handler_instance.extract_audio = Mock(return_value='/path/to/audio.wav')
        mock_handler.return_value = mock_handler_instance
        
        extractor = AudioExtractor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock video file
            video_path = os.path.join(tmpdir, 'test.mp4')
            Path(video_path).touch()
            
            output_path = os.path.join(tmpdir, 'audio.wav')
            result = extractor.extract_audio(video_path, output_path)
            
            assert result == '/path/to/audio.wav'

    def test_cleanup_temp_files(self):
        """Test temp file cleanup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = AudioExtractor(output_dir=tmpdir)
            # Create some temp files
            Path(os.path.join(tmpdir, 'test_extracted.wav')).touch()
            count = extractor.cleanup_temp_files()
            assert count == 1


class TestWhisperTranscriber:
    """Tests for the WhisperTranscriber class."""

    @patch('transcript_extractor.transcriber.WhisperWrapper')
    def test_transcribe(self, mock_wrapper_class):
        """Test transcription process."""
        # Create mock result data
        mock_result = TranscriptionResultData(
            text='test text',
            segments=[],
            language='en',
            duration=10,
            word_count=5
        )
        mock_wrapper_class.return_value.transcribe = Mock(return_value=mock_result)
        
        transcriber = WhisperTranscriber(model_size='tiny')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, 'test.wav')
            Path(audio_path).touch()
            
            result = transcriber.transcribe(audio_path, language='en')
            
            assert result.text == 'test text'
            assert result.language == 'en'
            assert result.duration == 10
            assert result.word_count == 5

    def test_transcribe_fails_gracefully(self):
        """Test transcription failure handling."""
        transcriber = WhisperTranscriber(model_size='tiny')
        
        # Try to transcribe non-existent file
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                transcriber.transcribe('/nonexistent/path.wav', language='en')


class TestTranscriptParser:
    """Tests for the TranscriptParser class."""

    def test_parse_text(self):
        """Test text parsing."""
        parser = TranscriptParser()
        text = "This is a test transcript.\nAnother line."
        
        result = parser.parse_text(text)
        
        assert result.text == text
        # Count words: "This is a test transcript. Another line." = 7 words
        assert result.word_count == 7

    def test_parse_segments(self):
        """Test segment parsing."""
        parser = TranscriptParser()
        segments_data = [
            {'text': 'first segment', 'start': 0, 'end': 10, 'language': 'en'},
            {'text': 'second segment', 'start': 10, 'end': 20, 'language': 'en'},
        ]
        
        result = parser.parse_segments(segments_data, duration=20)
        
        assert len(result.segments) == 2
        assert result.text == 'first segment second segment'
        assert result.word_count == 4

    def test_validate_result(self):
        """Test result validation."""
        parser = TranscriptParser()
        
        # Valid result
        valid_result = TranscriptionResultData(
            text='test text',
            segments=[],
            language='en',
            duration=100,
            word_count=50
        )
        assert parser.validate_result(valid_result) is True
        
        # Invalid result - empty text
        invalid_result = TranscriptionResultData(
            text='',
            segments=[],
            language='en',
            duration=100,
            word_count=0
        )
        assert parser.validate_result(invalid_result) is False


class TestTranscriptFormatter:
    """Tests for the TranscriptFormatter class."""

    def test_format_to_txt(self):
        """Test TXT format output."""
        formatter = TranscriptFormatter()
        
        result = TranscriptionResultData(
            text='test transcript text',
            language='en',
            duration=100,
            word_count=10,
            segments=[
                TranscriptionSegment(text='first segment', start=0, end=10, language='en'),
                TranscriptionSegment(text='second segment', start=10, end=20, language='en'),
            ]
        )
        
        txt_output = formatter.format_to_txt(result, include_timestamps=False)
        
        assert 'first segment' in txt_output
        assert 'second segment' in txt_output
        assert 'Language: en' in txt_output

    def test_format_to_srt(self):
        """Test SRT format output."""
        formatter = TranscriptFormatter()
        
        result = TranscriptionResultData(
            text='test transcript',
            language='en',
            duration=100,
            word_count=10,
            segments=[
                TranscriptionSegment(text='first segment', start=0, end=10, language='en'),
                TranscriptionSegment(text='second segment', start=10, end=20, language='en'),
            ]
        )
        
        srt_output = formatter.format_to_srt(result)
        
        assert '00:00:00,000' in srt_output
        assert '00:00:10,000' in srt_output
        assert '00:00:20,000' in srt_output

    def test_format_to_vtt(self):
        """Test VTT format output."""
        formatter = TranscriptFormatter()
        
        result = TranscriptionResultData(
            text='test transcript',
            language='en',
            duration=100,
            word_count=10,
            segments=[
                TranscriptionSegment(text='first segment', start=0, end=10, language='en'),
                TranscriptionSegment(text='second segment', start=10, end=20, language='en'),
            ]
        )
        
        vtt_output = formatter.format_to_vtt(result)
        
        assert 'WEBVTT' in vtt_output
        # VTT uses commas for milliseconds in this implementation
        assert '00:00:00,000' in vtt_output

    def test_format_to_json(self):
        """Test JSON format output."""
        formatter = TranscriptFormatter()
        
        result = TranscriptionResultData(
            text='test transcript',
            language='en',
            duration=100,
            word_count=10,
            segments=[
                TranscriptionSegment(text='first segment', start=0, end=10, language='en'),
                TranscriptionSegment(text='second segment', start=10, end=20, language='en'),
            ]
        )
        
        json_output = formatter.format_to_json(result)
        
        import json
        parsed = json.loads(json_output)
        
        assert parsed['metadata']['language'] == 'en'
        assert parsed['metadata']['duration'] == 100
        assert len(parsed['segments']) == 2


class TestSummaryGenerator:
    """Tests for the SummaryGenerator class."""

    def test_generate_summary(self):
        """Test summary generation."""
        generator = SummaryGenerator(strategy='extractive', length='medium')
        
        text = 'This is a test transcript. ' * 20
        
        summary = generator.generate(text, language='en')
        
        assert 'summary' in summary
        assert len(summary['summary']) > 0

    def test_get_key_points(self):
        """Test key point extraction."""
        generator = SummaryGenerator(strategy='extractive')
        
        text = 'Important point one. Important point two. Other text here.'
        
        key_points = generator.get_key_points(text, num_points=2)
        
        assert len(key_points) <= 2
        assert len(key_points) > 0

    def test_update_strategy(self):
        """Test strategy update."""
        generator = SummaryGenerator(strategy='extractive')
        generator.update_strategy('abstractive')
        assert generator.strategy == 'abstractive'
        generator.update_strategy('simple')
        assert generator.strategy == 'simple'

    def test_update_length(self):
        """Test summary length update."""
        generator = SummaryGenerator(length='short')
        generator.update_length('long')
        assert generator.length == 'long'
        generator.update_length('medium')
        assert generator.length == 'medium'


class TestTranscriptionPipeline:
    """Tests for the TranscriptionPipeline class."""

    @patch('transcript_extractor.pipeline.AudioExtractor')
    @patch('transcript_extractor.pipeline.WhisperTranscriber')
    @patch('transcript_extractor.pipeline.SummaryGenerator')
    def test_process_single_file(self, mock_summary, mock_transcriber, mock_extractor):
        """Test single file processing."""
        
        
        # Mock audio extraction
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_audio = Mock(return_value='/path/to/audio.wav')
        mock_extractor_instance.is_supported_format = Mock(return_value=True)
        mock_extractor.return_value = mock_extractor_instance
        
        # Mock transcription
        mock_result = TranscriptionResultData(
            text='test transcript',
            segments=[],
            language='en',
            duration=100,
            word_count=10
        )
        mock_transcriber_instance = Mock()
        mock_transcriber_instance.transcribe = Mock(return_value=mock_result)
        mock_transcriber.return_value = mock_transcriber_instance
        
        # Mock summary generation - return a dict, not a string
        mock_summary_instance = Mock()
        mock_summary_instance.generate = Mock(return_value={'summary': 'test summary'})
        mock_summary.return_value = mock_summary_instance
        pipeline = TranscriptionPipeline(model_size='tiny')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock input file
            input_path = os.path.join(tmpdir, 'test.mp4')
            Path(input_path).touch()
            
            output = pipeline.process(input_path, output_dir=tmpdir)
            
            assert isinstance(output, TranscriptionOutput)
            assert output.success is True
            assert 'Language: en' in output.transcript
            assert output.summary == 'test summary'

    @patch('transcript_extractor.pipeline.AudioExtractor')
    @patch('transcript_extractor.pipeline.WhisperTranscriber')
    @patch('transcript_extractor.pipeline.SummaryGenerator')
    def test_process_batch(self, mock_summary, mock_transcriber, mock_extractor):
        """Test batch processing."""
        
        
        # Mock audio extraction
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_audio = Mock(return_value='/path/to/audio.wav')
        mock_extractor_instance.is_supported_format = Mock(return_value=True)
        mock_extractor.return_value = mock_extractor_instance
        
        # Mock transcription
        mock_result = TranscriptionResultData(
            text='test transcript',
            segments=[],
            language='en',
            duration=100,
            word_count=10
        )
        mock_transcriber_instance = Mock()
        mock_transcriber_instance.transcribe = Mock(return_value=mock_result)
        mock_transcriber.return_value = mock_transcriber_instance
        
        # Mock summary generation - return a dict, not a string
        mock_summary_instance = Mock()
        mock_summary_instance.generate = Mock(return_value={'summary': 'test summary'})
        mock_summary.return_value = mock_summary_instance
        pipeline = TranscriptionPipeline(model_size='tiny')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, 'test1.mp4')
            file2 = os.path.join(tmpdir, 'test2.mp4')
            Path(file1).touch()
            Path(file2).touch()
            
            results = pipeline.process_batch([file1, file2], output_dir=tmpdir)
            
            assert len(results) == 2
            assert all(r.success for r in results)
            assert all(isinstance(r, TranscriptionOutput) for r in results)
