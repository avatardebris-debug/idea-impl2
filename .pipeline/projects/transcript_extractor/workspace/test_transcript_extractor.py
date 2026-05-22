"""
Comprehensive test suite for the transcript_extractor package.

Tests cover all modules: config, constants, audio_extractor, transcriber,
parser, summarizer, formatters, pipeline, and the top-level package.
"""

import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add the workspace to the path
sys.path.insert(0, str(Path(__file__).parent))

from transcript_extractor import (
    Config,
    SUPPORTED_FORMATS,
    OUTPUT_FORMATS,
    MODEL_SIZES,
    DEFAULT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_SUMMARY_LENGTH,
    SAMPLE_RATE,
    AudioExtractor,
    WhisperTranscriber,
    TranscriptParser,
    TranscriptFormatter,
    TranscriptionSegment,
    TranscriptionResultData,
    SummaryGenerator,
    TranscriptionPipeline,
    TranscriptionOutput,
)
from transcript_extractor.constants import (
    SUPPORTED_FORMATS as CONSTANTS_FORMATS,
    OUTPUT_FORMATS as CONSTANTS_OUTPUT_FORMATS,
    MODEL_SIZES as CONSTANTS_MODEL_SIZES,
    DEFAULT_MODEL as CONSTANTS_DEFAULT_MODEL,
    DEFAULT_LANGUAGE as CONSTANTS_DEFAULT_LANGUAGE,
    DEFAULT_SUMMARY_LENGTH as CONSTANTS_DEFAULT_SUMMARY_LENGTH,
    SAMPLE_RATE as CONSTANTS_SAMPLE_RATE,
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
from transcript_extractor.formats.video_handlers import (
    VideoHandler,
    MP4Handler,
    AVIHandler,
    MOVHandler,
    MKVHandler,
    get_handler_for_format,
)
from transcript_extractor.formatters.output_formats import (
    format_to_txt,
    format_to_srt,
    format_to_vtt,
    format_to_json,
)
from transcript_extractor.summarizers.summary_strategies import (
    SummaryStrategy,
    ExtractiveSummarizer,
    AbstractiveSummarizer,
    SimpleLengthBasedSummarizer,
    get_summarizer,
)


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_transcription_result(
    text: str = "This is a test transcript for the video file.",
    language: str = "en",
    duration: float = 120.5,
    word_count: int = 10,
    segments_count: int = 3,
) -> TranscriptionResultData:
    """Create a mock TranscriptionResultData for testing."""
    segments = []
    for i in range(segments_count):
        segments.append(
            TranscriptionSegment(
                text=f"Segment {i+1} text here.",
                start=i * 40.0,
                end=(i + 1) * 40.0,
                language=language,
            )
        )
    return TranscriptionResultData(
        text=text,
        segments=segments,
        language=language,
        duration=duration,
        word_count=word_count,
    )


def create_temp_file(suffix: str, content: bytes = b"fake audio/video data") -> str:
    """Create a temporary file with the given suffix and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, 'wb') as f:
        f.write(content)
    return path


# ============================================================================
# Test: Config
# ============================================================================

class TestConfig(unittest.TestCase):
    """Tests for the Config class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_config(self):
        """Test that default config creates valid paths."""
        config = Config()
        self.assertIsNotNone(config.model_path)
        self.assertIsNotNone(config.output_dir)
        self.assertIsNotNone(config.temp_dir)
        self.assertEqual(config.api_endpoint, "local")

    def test_custom_config(self):
        """Test that custom config values are set correctly."""
        config = Config(
            model_path="/custom/model",
            output_dir=self.temp_dir,
            temp_dir=self.temp_dir,
            api_endpoint="https://api.example.com",
        )
        self.assertEqual(config.model_path, "/custom/model")
        self.assertEqual(config.output_dir, self.temp_dir)
        self.assertEqual(config.temp_dir, self.temp_dir)
        self.assertEqual(config.api_endpoint, "https://api.example.com")

    def test_get_output_path(self):
        """Test get_output_path returns correct path."""
        config = Config(output_dir=self.temp_dir)
        path = config.get_output_path("output.txt")
        self.assertTrue(path.endswith("output.txt"))
        self.assertIn(self.temp_dir, path)

    def test_get_temp_path(self):
        """Test get_temp_path returns correct path."""
        config = Config(temp_dir=self.temp_dir)
        path = config.get_temp_path("temp.wav")
        self.assertTrue(path.endswith("temp.wav"))
        self.assertIn(self.temp_dir, path)

    def test_from_env(self):
        """Test Config.from_env creates config from environment variables."""
        with patch.dict(os.environ, {
            "TRANSCRIPT_EXTRACTOR_MODEL_PATH": "/env/model",
            "TRANSCRIPT_EXTRACTOR_OUTPUT_DIR": "/env/output",
            "TRANSCRIPT_EXTRACTOR_TEMP_DIR": "/env/temp",
            "TRANSCRIPT_EXTRACTOR_API_ENDPOINT": "https://env.api.com",
        }):
            config = Config.from_env()
            self.assertEqual(config.model_path, "/env/model")
            self.assertEqual(config.output_dir, "/env/output")
            self.assertEqual(config.temp_dir, "/env/temp")
            self.assertEqual(config.api_endpoint, "https://env.api.com")

    def test_directories_created(self):
        """Test that config creates directories if they don't exist."""
        new_dir = os.path.join(self.temp_dir, "new_output")
        config = Config(output_dir=new_dir)
        self.assertTrue(os.path.isdir(new_dir))


# ============================================================================
# Test: Constants
# ============================================================================

class TestConstants(unittest.TestCase):
    """Tests for module-level constants."""

    def test_supported_formats(self):
        """Test SUPPORTED_FORMATS contains expected formats."""
        self.assertIn("mp4", SUPPORTED_FORMATS)
        self.assertIn("avi", SUPPORTED_FORMATS)
        self.assertIn("mov", SUPPORTED_FORMATS)
        self.assertIn("mkv", SUPPORTED_FORMATS)
        self.assertIn("mp3", SUPPORTED_FORMATS)
        self.assertIn("wav", SUPPORTED_FORMATS)

    def test_output_formats(self):
        """Test OUTPUT_FORMATS contains expected formats."""
        self.assertIn("txt", OUTPUT_FORMATS)
        self.assertIn("srt", OUTPUT_FORMATS)
        self.assertIn("vtt", OUTPUT_FORMATS)
        self.assertIn("json", OUTPUT_FORMATS)

    def test_model_sizes(self):
        """Test MODEL_SIZES contains expected sizes."""
        self.assertIn("tiny", MODEL_SIZES)
        self.assertIn("small", MODEL_SIZES)
        self.assertIn("medium", MODEL_SIZES)
        self.assertIn("large-v2", MODEL_SIZES)
        self.assertIn("large-v3", MODEL_SIZES)

    def test_default_values(self):
        """Test default values are correct."""
        self.assertEqual(DEFAULT_MODEL, "small")
        self.assertEqual(DEFAULT_LANGUAGE, "en")
        self.assertEqual(DEFAULT_SUMMARY_LENGTH, "medium")
        self.assertEqual(SAMPLE_RATE, 16000)

    def test_constants_module_consistency(self):
        """Test that constants module values match package-level constants."""
        self.assertEqual(CONSTANTS_FORMATS, SUPPORTED_FORMATS)
        self.assertEqual(CONSTANTS_OUTPUT_FORMATS, OUTPUT_FORMATS)
        self.assertEqual(CONSTANTS_MODEL_SIZES, MODEL_SIZES)
        self.assertEqual(CONSTANTS_DEFAULT_MODEL, DEFAULT_MODEL)
        self.assertEqual(CONSTANTS_DEFAULT_LANGUAGE, DEFAULT_LANGUAGE)
        self.assertEqual(CONSTANTS_DEFAULT_SUMMARY_LENGTH, DEFAULT_SUMMARY_LENGTH)
        self.assertEqual(CONSTANTS_SAMPLE_RATE, SAMPLE_RATE)

    def test_additional_constants(self):
        """Test additional constants are defined."""
        self.assertEqual(AUDIO_BITRATE, "128k")
        self.assertEqual(MAX_TRANSCRIPT_LENGTH, 1000000)
        self.assertEqual(MAX_SUMMARY_LENGTH, 500)
        self.assertEqual(MIN_WORD_COUNT_FOR_SUMMARY, 50)
        self.assertEqual(MAX_INPUT_FILE_SIZE, 2 * 1024 * 1024 * 1024)
        self.assertEqual(TIMESTAMP_PRECISION, "milliseconds")
        self.assertEqual(KEY_POINTS_COUNT, 5)
        self.assertEqual(RETRY_COUNT, 3)
        self.assertEqual(RETRY_DELAY, 1.0)
        self.assertEqual(PROGRESS_INTERVAL, 10)


# ============================================================================
# Test: AudioExtractor
# ============================================================================

class TestAudioExtractor(unittest.TestCase):
    """Tests for the AudioExtractor class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = AudioExtractor(output_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_supported_format_video(self):
        """Test is_supported_format returns True for video formats."""
        for ext in ['.mp4', '.avi', '.mov', '.mkv', '.m4v']:
            self.assertTrue(self.extractor.is_supported_format(f"test{ext}"))

    def test_is_supported_format_audio(self):
        """Test is_supported_format returns True for audio formats."""
        for ext in ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac', '.wma']:
            self.assertTrue(self.extractor.is_supported_format(f"test{ext}"))

    def test_is_supported_format_unsupported(self):
        """Test is_supported_format returns False for unsupported formats."""
        self.assertFalse(self.extractor.is_supported_format("test.txt"))
        self.assertFalse(self.extractor.is_supported_format("test.pdf"))

    def test_extract_audio_from_video(self):
        """Test extracting audio from a video file."""
        video_path = create_temp_file(".mp4")
        try:
            # Mock the handler
            with patch('transcript_extractor.audio_extractor.get_handler_for_format') as mock_handler:
                mock_handler_instance = MagicMock()
                mock_handler_instance.extract_audio.return_value = os.path.join(self.temp_dir, "test_extracted.wav")
                mock_handler.return_value = mock_handler_instance

                result = self.extractor.extract_audio(video_path)
                self.assertTrue(result.endswith(".wav"))
                mock_handler.assert_called_once()
        finally:
            os.unlink(video_path)

    def test_extract_audio_from_audio_file(self):
        """Test extracting/converting audio from an audio file."""
        audio_path = create_temp_file(".wav")
        try:
            with patch('transcript_extractor.audio_extractor.ffmpeg') as mock_ffmpeg:
                mock_ffmpeg.input.return_value.output.return_value.overwrite_output.return_value.run.return_value = None

                result = self.extractor.extract_audio(audio_path)
                self.assertTrue(result.endswith(".wav"))
        finally:
            os.unlink(audio_path)

    def test_extract_audio_unsupported_format(self):
        """Test extract_audio raises ValueError for unsupported format."""
        txt_path = create_temp_file(".txt")
        try:
            with self.assertRaises(ValueError):
                self.extractor.extract_audio(txt_path)
        finally:
            os.unlink(txt_path)

    def test_extract_audio_file_not_found(self):
        """Test extract_audio raises FileNotFoundError for non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_audio("/nonexistent/file.mp4")

    def test_cleanup_temp_files(self):
        """Test cleanup_temp_files removes temporary files."""
        # Create some temp files
        temp_file1 = os.path.join(self.temp_dir, "test1_extracted.wav")
        temp_file2 = os.path.join(self.temp_dir, "test2_extracted.wav")
        with open(temp_file1, 'w') as f:
            f.write("temp")
        with open(temp_file2, 'w') as f:
            f.write("temp")

        count = self.extractor.cleanup_temp_files()
        self.assertEqual(count, 2)
        self.assertFalse(os.path.exists(temp_file1))
        self.assertFalse(os.path.exists(temp_file2))

    def test_cleanup_temp_files_no_files(self):
        """Test cleanup_temp_files returns 0 when no temp files exist."""
        count = self.extractor.cleanup_temp_files()
        self.assertEqual(count, 0)


# ============================================================================
# Test: Video Handlers
# ============================================================================

class TestVideoHandlers(unittest.TestCase):
    """Tests for video handler classes."""

    def test_get_handler_for_format_mp4(self):
        """Test get_handler_for_format returns MP4Handler for mp4."""
        handler = get_handler_for_format("test.mp4")
        self.assertIsInstance(handler, MP4Handler)

    def test_get_handler_for_format_avi(self):
        """Test get_handler_for_format returns AVIHandler for avi."""
        handler = get_handler_for_format("test.avi")
        self.assertIsInstance(handler, AVIHandler)

    def test_get_handler_for_format_mov(self):
        """Test get_handler_for_format returns MOVHandler for mov."""
        handler = get_handler_for_format("test.mov")
        self.assertIsInstance(handler, MOVHandler)

    def test_get_handler_for_format_mkv(self):
        """Test get_handler_for_format returns MKVHandler for mkv."""
        handler = get_handler_for_format("test.mkv")
        self.assertIsInstance(handler, MKVHandler)

    def test_get_handler_for_format_unsupported(self):
        """Test get_handler_for_format returns None for unsupported format."""
        handler = get_handler_for_format("test.txt")
        self.assertIsNone(handler)

    def test_mp4_handler_extract_audio(self):
        """Test MP4Handler.extract_audio works."""
        handler = MP4Handler()
        with patch.object(handler, '_extract_with_ffmpeg') as mock_ffmpeg:
            mock_ffmpeg.return_value = "/output/path.wav"
            result = handler.extract_audio("/input.mp4", "/output.wav")
            self.assertEqual(result, "/output/path.wav")
            mock_ffmpeg.assert_called_once()

    def test_avi_handler_extract_audio(self):
        """Test AVIHandler.extract_audio works."""
        handler = AVIHandler()
        with patch.object(handler, '_extract_with_ffmpeg') as mock_ffmpeg:
            mock_ffmpeg.return_value = "/output/path.wav"
            result = handler.extract_audio("/input.avi", "/output.wav")
            self.assertEqual(result, "/output/path.wav")

    def test_mov_handler_extract_audio(self):
        """Test MOVHandler.extract_audio works."""
        handler = MOVHandler()
        with patch.object(handler, '_extract_with_ffmpeg') as mock_ffmpeg:
            mock_ffmpeg.return_value = "/output/path.wav"
            result = handler.extract_audio("/input.mov", "/output.wav")
            self.assertEqual(result, "/output/path.wav")

    def test_mkv_handler_extract_audio(self):
        """Test MKVHandler.extract_audio works."""
        handler = MKVHandler()
        with patch.object(handler, '_extract_with_ffmpeg') as mock_ffmpeg:
            mock_ffmpeg.return_value = "/output/path.wav"
            result = handler.extract_audio("/input.mkv", "/output.wav")
            self.assertEqual(result, "/output/path.wav")


# ============================================================================
# Test: TranscriptionSegment
# ============================================================================

class TestTranscriptionSegment(unittest.TestCase):
    """Tests for the TranscriptionSegment dataclass."""

    def test_create_segment(self):
        """Test creating a TranscriptionSegment."""
        segment = TranscriptionSegment(
            text="Test segment",
            start=0.0,
            end=5.0,
            language="en",
        )
        self.assertEqual(segment.text, "Test segment")
        self.assertEqual(segment.start, 0.0)
        self.assertEqual(segment.end, 5.0)
        self.assertEqual(segment.language, "en")

    def test_segment_duration(self):
        """Test segment duration calculation."""
        segment = TranscriptionSegment(
            text="Test",
            start=10.0,
            end=15.5,
            language="en",
        )
        self.assertAlmostEqual(segment.duration, 5.5)

    def test_segment_to_dict(self):
        """Test segment to_dict method."""
        segment = TranscriptionSegment(
            text="Test",
            start=0.0,
            end=5.0,
            language="en",
        )
        d = segment.to_dict()
        self.assertEqual(d["text"], "Test")
        self.assertEqual(d["start"], 0.0)
        self.assertEqual(d["end"], 5.0)
        self.assertEqual(d["language"], "en")
        self.assertIn("duration", d)

    def test_segment_to_json(self):
        """Test segment to_json method."""
        segment = TranscriptionSegment(
            text="Test",
            start=0.0,
            end=5.0,
            language="en",
        )
        json_str = segment.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["text"], "Test")


# ============================================================================
# Test: TranscriptionResultData
# ============================================================================

class TestTranscriptionResultData(unittest.TestCase):
    """Tests for the TranscriptionResultData dataclass."""

    def test_create_result(self):
        """Test creating a TranscriptionResultData."""
        segments = [
            TranscriptionSegment(text="Seg1", start=0.0, end=5.0, language="en"),
            TranscriptionSegment(text="Seg2", start=5.0, end=10.0, language="en"),
        ]
        result = TranscriptionResultData(
            text="Seg1 Seg2",
            segments=segments,
            language="en",
            duration=10.0,
            word_count=2,
        )
        self.assertEqual(result.text, "Seg1 Seg2")
        self.assertEqual(len(result.segments), 2)
        self.assertEqual(result.language, "en")
        self.assertEqual(result.duration, 10.0)
        self.assertEqual(result.word_count, 2)

    def test_result_to_dict(self):
        """Test result to_dict method."""
        result = create_mock_transcription_result()
        d = result.to_dict()
        self.assertIn("text", d)
        self.assertIn("segments", d)
        self.assertIn("language", d)
        self.assertIn("duration", d)
        self.assertIn("word_count", d)

    def test_result_to_json(self):
        """Test result to_json method."""
        result = create_mock_transcription_result()
        json_str = result.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["text"], result.text)
        self.assertEqual(parsed["language"], result.language)


# ============================================================================
# Test: TranscriptFormatter
# ============================================================================

class TestTranscriptFormatter(unittest.TestCase):
    """Tests for the TranscriptFormatter class."""

    def setUp(self):
        self.formatter = TranscriptFormatter()
        self.result = create_mock_transcription_result()

    def test_format_to_txt(self):
        """Test format_to_txt produces valid text output."""
        txt = self.formatter.format_to_txt(self.result, include_timestamps=True)
        self.assertIsInstance(txt, str)
        self.assertIn("Test transcript", txt)
        # Check for timestamp format
        self.assertIn("00:00:00", txt)

    def test_format_to_txt_no_timestamps(self):
        """Test format_to_txt without timestamps."""
        txt = self.formatter.format_to_txt(self.result, include_timestamps=False)
        self.assertIsInstance(txt, str)
        self.assertIn("Test transcript", txt)
        # Should not have timestamp brackets
        self.assertNotIn("[00:00:00", txt)

    def test_format_to_txt_with_metadata(self):
        """Test format_to_txt with metadata."""
        txt = self.formatter.format_to_txt(self.result, include_timestamps=False, include_metadata=True)
        self.assertIn("Language:", txt)
        self.assertIn("Duration:", txt)
        self.assertIn("Word Count:", txt)

    def test_format_to_srt(self):
        """Test format_to_srt produces valid SRT output."""
        srt = self.formatter.format_to_srt(self.result)
        self.assertIsInstance(srt, str)
        # SRT format: index, timestamps, text
        self.assertIn("00:00:00,000", srt)
        self.assertIn("00:00:40,000", srt)

    def test_format_to_vtt(self):
        """Test format_to_vtt produces valid VTT output."""
        vtt = self.formatter.format_to_vtt(self.result)
        self.assertIsInstance(vtt, str)
        self.assertIn("WEBVTT", vtt)
        self.assertIn("00:00:00.000", vtt)

    def test_format_to_json(self):
        """Test format_to_json produces valid JSON output."""
        json_str = self.formatter.format_to_json(self.result, indent=2)
        parsed = json.loads(json_str)
        self.assertIn("text", parsed)
        self.assertIn("segments", parsed)
        self.assertIn("language", parsed)

    def test_format_to_json_indent(self):
        """Test format_to_json with different indent levels."""
        json_str_2 = self.formatter.format_to_json(self.result, indent=2)
        json_str_4 = self.formatter.format_to_json(self.result, indent=4)
        # Both should be valid JSON
        json.loads(json_str_2)
        json.loads(json_str_4)


# ============================================================================
# Test: format_to_txt function
# ============================================================================

class TestFormatFunctions(unittest.TestCase):
    """Tests for standalone format functions."""

    def setUp(self):
        self.result = create_mock_transcription_result()

    def test_format_to_txt_function(self):
        """Test standalone format_to_txt function."""
        txt = format_to_txt(self.result)
        self.assertIsInstance(txt, str)
        self.assertIn("Test transcript", txt)

    def test_format_to_srt_function(self):
        """Test standalone format_to_srt function."""
        srt = format_to_srt(self.result)
        self.assertIsInstance(srt, str)
        self.assertIn("WEBVTT" if "vtt" in srt.lower() else "00:00:00", srt)

    def test_format_to_vtt_function(self):
        """Test standalone format_to_vtt function."""
        vtt = format_to_vtt(self.result)
        self.assertIsInstance(vtt, str)
        self.assertIn("WEBVTT", vtt)

    def test_format_to_json_function(self):
        """Test standalone format_to_json function."""
        json_str = format_to_json(self.result)
        parsed = json.loads(json_str)
        self.assertIn("text", parsed)


# ============================================================================
# Test: WhisperTranscriber
# ============================================================================

class TestWhisperTranscriber(unittest.TestCase):
    """Tests for the WhisperTranscriber class."""

    def setUp(self):
        self.transcriber = WhisperTranscriber(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )

    def test_init(self):
        """Test transcriber initialization."""
        self.assertIsNotNone(self.transcriber.wrapper)

    @patch('transcript_extractor.transcriber.WhisperWrapper')
    def test_transcribe(self, mock_wrapper_class):
        """Test transcribe method."""
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper
        mock_wrapper.transcribe.return_value = create_mock_transcription_result()

        result = self.transcriber.transcribe(
            audio_path="/test/audio.wav",
            language="en",
            include_timestamps=True,
        )
        self.assertIsInstance(result, TranscriptionResultData)
        mock_wrapper.transcribe.assert_called_once()

    @patch('transcript_extractor.transcriber.WhisperWrapper')
    def test_transcribe_with_progress(self, mock_wrapper_class):
        """Test transcribe_with_progress method."""
        mock_wrapper = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper
        mock_wrapper.transcribe.return_value = create_mock_transcription_result()

        result = self.transcriber.transcribe_with_progress(
            audio_path="/test/audio.wav",
            language="en",
            progress_callback=lambda x: None,
        )
        self.assertIsInstance(result, TranscriptionResultData)


# ============================================================================
# Test: TranscriptParser
# ============================================================================

class TestTranscriptParser(unittest.TestCase):
    """Tests for the TranscriptParser class."""

    def setUp(self):
        self.parser = TranscriptParser(output_format="json")
        self.result = create_mock_transcription_result()

    def test_parse(self):
        """Test parse method."""
        output = self.parser.parse(self.result)
        self.assertIsInstance(output, str)
        parsed = json.loads(output)
        self.assertIn("text", parsed)

    def test_parse_to_txt(self):
        """Test parse_to_txt method."""
        output = self.parser.parse_to_txt(self.result)
        self.assertIsInstance(output, str)
        self.assertIn("Test transcript", output)

    def test_parse_to_srt(self):
        """Test parse_to_srt method."""
        output = self.parser.parse_to_srt(self.result)
        self.assertIsInstance(output, str)
        self.assertIn("00:00:00", output)

    def test_parse_to_vtt(self):
        """Test parse_to_vtt method."""
        output = self.parser.parse_to_vtt(self.result)
        self.assertIsInstance(output, str)
        self.assertIn("WEBVTT", output)

    def test_parse_to_json(self):
        """Test parse_to_json method."""
        output = self.parser.parse_to_json(self.result)
        parsed = json.loads(output)
        self.assertIn("text", parsed)

    def test_update_format(self):
        """Test update_format method."""
        self.parser.update_format("srt")
        self.assertEqual(self.parser.output_format, "srt")


# ============================================================================
# Test: SummaryGenerator
# ============================================================================

class TestSummaryGenerator(unittest.TestCase):
    """Tests for the SummaryGenerator class."""

    def setUp(self):
        self.generator = SummaryGenerator(
            length="medium",
            strategy="extractive",
        )

    def test_init(self):
        """Test generator initialization."""
        self.assertEqual(self.generator.length, "medium")
        self.assertEqual(self.generator.strategy, "extractive")
        self.assertIsNotNone(self.generator._summarizer)

    def test_generate(self):
        """Test generate method."""
        text = "This is a test transcript for summarization. It contains multiple sentences. Each sentence should be considered for the summary."
        result = self.generator.generate(text, language="en")
        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("length", result)
        self.assertIn("strategy", result)

    def test_get_key_points(self):
        """Test get_key_points method."""
        text = "First point. Second point. Third point. Fourth point. Fifth point."
        points = self.generator.get_key_points(text, num_points=3)
        self.assertIsInstance(points, list)
        self.assertLessEqual(len(points), 3)

    def test_update_strategy(self):
        """Test update_strategy method."""
        self.generator.update_strategy("abstractive")
        self.assertEqual(self.generator.strategy, "abstractive")
        self.assertIsNotNone(self.generator._summarizer)

    def test_update_length(self):
        """Test update_length method."""
        self.generator.update_length("short")
        self.assertEqual(self.generator.length, "short")
        self.assertIsNotNone(self.generator._summarizer)


# ============================================================================
# Test: Summary Strategies
# ============================================================================

class TestSummaryStrategies(unittest.TestCase):
    """Tests for summary strategy classes."""

    def test_get_summarizer_extractive(self):
        """Test get_summarizer returns ExtractiveSummarizer."""
        summarizer = get_summarizer("extractive", length="medium")
        self.assertIsInstance(summarizer, ExtractiveSummarizer)

    def test_get_summarizer_abstractive(self):
        """Test get_summarizer returns AbstractiveSummarizer."""
        summarizer = get_summarizer("abstractive", length="medium")
        self.assertIsInstance(summarizer, AbstractiveSummarizer)

    def test_get_summarizer_simple(self):
        """Test get_summarizer returns SimpleLengthBasedSummarizer."""
        summarizer = get_summarizer("simple", length="medium")
        self.assertIsInstance(summarizer, SimpleLengthBasedSummarizer)

    def test_get_summarizer_invalid(self):
        """Test get_summarizer raises ValueError for invalid strategy."""
        with self.assertRaises(ValueError):
            get_summarizer("invalid", length="medium")

    def test_extractive_summarizer(self):
        """Test ExtractiveSummarizer."""
        summarizer = ExtractiveSummarizer(length="medium")
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        result = summarizer.summarize(text, language="en")
        self.assertIn("summary", result)
        self.assertIsInstance(result["summary"], str)

    def test_abstractive_summarizer(self):
        """Test AbstractiveSummarizer."""
        summarizer = AbstractiveSummarizer(length="medium")
        text = "This is a test. It should work. Let's see. What happens? Nothing special."
        result = summarizer.summarize(text, language="en")
        self.assertIn("summary", result)
        self.assertIsInstance(result["summary"], str)

    def test_simple_summarizer(self):
        """Test SimpleLengthBasedSummarizer."""
        summarizer = SimpleLengthBasedSummarizer(length="medium")
        text = "Word1 word2 word3 word4 word5 word6 word7 word8 word9 word10."
        result = summarizer.summarize(text, language="en")
        self.assertIn("summary", result)
        self.assertIsInstance(result["summary"], str)

    def test_extractive_get_key_points(self):
        """Test ExtractiveSummarizer.get_key_points."""
        summarizer = ExtractiveSummarizer(length="medium")
        text = "Point one. Point two. Point three. Point four. Point five."
        points = summarizer.get_key_points(text, num_points=3)
        self.assertIsInstance(points, list)
        self.assertLessEqual(len(points), 3)

    def test_abstractive_get_key_points(self):
        """Test AbstractiveSummarizer.get_key_points."""
        summarizer = AbstractiveSummarizer(length="medium")
        text = "Point one. Point two. Point three. Point four. Point five."
        points = summarizer.get_key_points(text, num_points=3)
        self.assertIsInstance(points, list)

    def test_simple_get_key_points(self):
        """Test SimpleLengthBasedSummarizer.get_key_points."""
        summarizer = SimpleLengthBasedSummarizer(length="medium")
        text = "Point one. Point two. Point three. Point four. Point five."
        points = summarizer.get_key_points(text, num_points=3)
        self.assertIsInstance(points, list)


# ============================================================================
# Test: TranscriptionPipeline
# ============================================================================

class TestTranscriptionPipeline(unittest.TestCase):
    """Tests for the TranscriptionPipeline class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.pipeline = TranscriptionPipeline(
            model_size="tiny",
            language="en",
            output_format="txt",
            summary_length="medium",
            summary_strategy="extractive",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test pipeline initialization."""
        self.assertEqual(self.pipeline.model_size, "tiny")
        self.assertEqual(self.pipeline.language, "en")
        self.assertEqual(self.pipeline.output_format, "txt")
        self.assertEqual(self.pipeline.summary_length, "medium")
        self.assertEqual(self.pipeline.summary_strategy, "extractive")
        self.assertIsNotNone(self.pipeline.audio_extractor)
        self.assertIsNotNone(self.pipeline.transcriber)
        self.assertIsNotNone(self.pipeline.summarizer)

    @patch('transcript_extractor.pipeline.AudioExtractor')
    @patch('transcript_extractor.pipeline.WhisperTranscriber')
    @patch('transcript_extractor.pipeline.SummaryGenerator')
    def test_process_success(self, mock_summarizer, mock_transcriber, mock_extractor):
        """Test successful pipeline processing."""
        # Setup mocks
        mock_audio_path = os.path.join(self.temp_dir, "audio.wav")
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_audio.return_value = mock_audio_path
        mock_extractor_instance.is_supported_format.return_value = True
        mock_extractor.return_value = mock_extractor_instance

        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = create_mock_transcription_result()
        mock_transcriber.return_value = mock_transcriber_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.generate.return_value = {"summary": "Test summary", "length": "medium", "strategy": "extractive"}
        mock_summarizer.return_value = mock_summarizer_instance

        # Create a temporary input file
        input_path = create_temp_file(".mp4")
        try:
            output = self.pipeline.process(input_path)
            self.assertIsInstance(output, TranscriptionOutput)
            self.assertTrue(output.success)
            self.assertIsNotNone(output.transcript)
            self.assertIsNotNone(output.summary)
        finally:
            os.unlink(input_path)

    @patch('transcript_extractor.pipeline.AudioExtractor')
    def test_process_file_not_found(self, mock_extractor):
        """Test pipeline handles file not found."""
        mock_extractor_instance = MagicMock()
        mock_extractor.return_value = mock_extractor_instance

        output = self.pipeline.process("/nonexistent/file.mp4")
        self.assertIsInstance(output, TranscriptionOutput)
        self.assertFalse(output.success)
        self.assertIsNotNone(output.error_message)

    @patch('transcript_extractor.pipeline.AudioExtractor')
    def test_process_unsupported_format(self, mock_extractor):
        """Test pipeline handles unsupported format."""
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.is_supported_format.return_value = False
        mock_extractor.return_value = mock_extractor_instance

        input_path = create_temp_file(".txt")
        try:
            output = self.pipeline.process(input_path)
            self.assertIsInstance(output, TranscriptionOutput)
            self.assertFalse(output.success)
        finally:
            os.unlink(input_path)

    @patch('transcript_extractor.pipeline.AudioExtractor')
    @patch('transcript_extractor.pipeline.WhisperTranscriber')
    @patch('transcript_extractor.pipeline.SummaryGenerator')
    def test_process_with_output_dir(self, mock_summarizer, mock_transcriber, mock_extractor):
        """Test pipeline saves output to directory."""
        mock_audio_path = os.path.join(self.temp_dir, "audio.wav")
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_audio.return_value = mock_audio_path
        mock_extractor_instance.is_supported_format.return_value = True
        mock_extractor.return_value = mock_extractor_instance

        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = create_mock_transcription_result()
        mock_transcriber.return_value = mock_transcriber_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.generate.return_value = {"summary": "Test summary", "length": "medium", "strategy": "extractive"}
        mock_summarizer.return_value = mock_summarizer_instance

        input_path = create_temp_file(".mp4")
        output_dir = os.path.join(self.temp_dir, "output")
        try:
            output = self.pipeline.process(input_path, output_dir=output_dir)
            self.assertTrue(output.success)
            self.assertTrue(os.path.exists(output_dir))
        finally:
            os.unlink(input_path)

    def test_process_batch(self):
        """Test process_batch method."""
        # Create temporary files
        files = [create_temp_file(".mp4") for _ in range(2)]
        try:
            with patch('transcript_extractor.pipeline.AudioExtractor') as mock_extractor:
                mock_extractor_instance = MagicMock()
                mock_extractor_instance.extract_audio.return_value = "/audio.wav"
                mock_extractor_instance.is_supported_format.return_value = True
                mock_extractor.return_value = mock_extractor_instance

                with patch('transcript_extractor.pipeline.WhisperTranscriber') as mock_transcriber:
                    mock_transcriber_instance = MagicMock()
                    mock_transcriber_instance.transcribe.return_value = create_mock_transcription_result()
                    mock_transcriber.return_value = mock_transcriber_instance

                    with patch('transcript_extractor.pipeline.SummaryGenerator') as mock_summarizer:
                        mock_summarizer_instance = MagicMock()
                        mock_summarizer_instance.generate.return_value = {"summary": "Test", "length": "medium", "strategy": "extractive"}
                        mock_summarizer.return_value = mock_summarizer_instance

                        results = self.pipeline.process_batch(files)
                        self.assertEqual(len(results), 2)
                        for result in results:
                            self.assertIsInstance(result, TranscriptionOutput)
        finally:
            for f in files:
                os.unlink(f)

    def test_transcription_output_to_dict(self):
        """Test TranscriptionOutput.to_dict method."""
        output = TranscriptionOutput(
            input_file="test.mp4",
            transcript="Test transcript",
            transcript_format="txt",
            summary="Test summary",
            summary_length="medium",
            language="en",
            duration=120.5,
            word_count=10,
            segments_count=3,
            success=True,
        )
        d = output.to_dict()
        self.assertEqual(d["input_file"], "test.mp4")
        self.assertEqual(d["transcript"], "Test transcript")
        self.assertTrue(d["success"])

    def test_transcription_output_to_json(self):
        """Test TranscriptionOutput.to_json method."""
        output = TranscriptionOutput(
            input_file="test.mp4",
            transcript="Test transcript",
            transcript_format="txt",
            summary="Test summary",
            summary_length="medium",
            language="en",
            duration=120.5,
            word_count=10,
            segments_count=3,
            success=True,
        )
        json_str = output.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["input_file"], "test.mp4")


# ============================================================================
# Test: Package __init__.py
# ============================================================================

class TestPackageInit(unittest.TestCase):
    """Tests for the package __init__.py exports."""

    def test_all_exports(self):
        """Test that all expected exports are available."""
        import transcript_extractor as pkg
        expected_exports = [
            "Config",
            "SUPPORTED_FORMATS",
            "OUTPUT_FORMATS",
            "MODEL_SIZES",
            "DEFAULT_MODEL",
            "DEFAULT_LANGUAGE",
            "DEFAULT_SUMMARY_LENGTH",
            "SAMPLE_RATE",
            "AudioExtractor",
            "WhisperTranscriber",
            "TranscriptParser",
            "TranscriptFormatter",
            "TranscriptionSegment",
            "TranscriptionResultData",
            "SummaryGenerator",
            "TranscriptionPipeline",
            "TranscriptionOutput",
        ]
        for export in expected_exports:
            self.assertTrue(hasattr(pkg, export), f"Missing export: {export}")

    def test_version(self):
        """Test package version is defined."""
        import transcript_extractor as pkg
        self.assertTrue(hasattr(pkg, "__version__"))
        self.assertIsInstance(pkg.__version__, str)

    def test_all_list(self):
        """Test __all__ is defined and matches exports."""
        import transcript_extractor as pkg
        self.assertTrue(hasattr(pkg, "__all__"))
        self.assertIsInstance(pkg.__all__, list)


# ============================================================================
# Test: Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling."""

    def test_empty_text_summarization(self):
        """Test summarization with empty text."""
        generator = SummaryGenerator()
        result = generator.generate("", language="en")
        self.assertIn("summary", result)

    def test_very_long_text_summarization(self):
        """Test summarization with very long text."""
        generator = SummaryGenerator()
        long_text = "This is a test. " * 10000
        result = generator.generate(long_text, language="en")
        self.assertIn("summary", result)
        self.assertIsInstance(result["summary"], str)

    def test_special_characters_in_transcript(self):
        """Test handling of special characters in transcript."""
        result = create_mock_transcription_result(text="Hello 世界! 🌍 Привет мир!")
        txt = TranscriptFormatter().format_to_txt(result)
        self.assertIn("Hello", txt)
        self.assertIn("世界", txt)

    def test_unicode_in_output(self):
        """Test unicode characters in output formats."""
        result = create_mock_transcription_result(text="Unicode test: αβγδ")
        json_str = TranscriptFormatter().format_to_json(result)
        parsed = json.loads(json_str)
        self.assertIn("αβγδ", parsed["text"])

    def test_config_with_none_values(self):
        """Test Config with all None values uses defaults."""
        config = Config()
        self.assertIsNotNone(config.model_path)
        self.assertIsNotNone(config.output_dir)
        self.assertIsNotNone(config.temp_dir)

    def test_audio_extractor_with_custom_output_filename(self):
        """Test AudioExtractor with custom output filename."""
        extractor = AudioExtractor(output_dir=self.temp_dir)
        with patch('transcript_extractor.audio_extractor.get_handler_for_format') as mock_handler:
            mock_handler_instance = MagicMock()
            mock_handler_instance.extract_audio.return_value = os.path.join(self.temp_dir, "custom_name.wav")
            mock_handler.return_value = mock_handler_instance

            video_path = create_temp_file(".mp4")
            try:
                result = extractor.extract_audio(video_path, output_filename="custom_name.wav")
                self.assertTrue(result.endswith("custom_name.wav"))
            finally:
                os.unlink(video_path)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    unittest.main()
