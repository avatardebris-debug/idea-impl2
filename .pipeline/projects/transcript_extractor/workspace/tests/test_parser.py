import pytest
from transcript_extractor.parser import TranscriptParser
from transcript_extractor.models.whisper_wrapper import TranscriptionResultData

class TestTranscriptParser:
    def test_parse_text(self):
        result = TranscriptParser.parse_text("Hello world test", language="en", duration=1.5)
        assert result.__class__.__name__ == "TranscriptionResultData"
        assert result.text == "Hello world test"
        assert result.word_count == 3
        assert result.language == "en"
        assert result.duration == 1.5

    def test_parse_segments(self):
        segments_data = [
            {"text": "Hello", "start": 0.0, "end": 1.0, "language": "en"},
            {"text": "world", "start": 1.0, "end": 2.0, "language": "en"}
        ]
        result = TranscriptParser.parse_segments(segments_data, language="en", duration=2.0)
        assert result.__class__.__name__ == "TranscriptionResultData"
        assert result.text == "Hello world"
        assert result.word_count == 2
        assert len(result.segments) == 2
        assert result.segments[0].text == "Hello"
        assert result.duration == 2.0

    def test_validate_result(self):
        valid = TranscriptionResultData(text="Test", segments=[], language="en", duration=1.0, word_count=1)
        assert TranscriptParser.validate_result(valid) is True

        invalid_text = TranscriptionResultData(text="", segments=[], language="en", duration=1.0, word_count=1)
        assert TranscriptParser.validate_result(invalid_text) is False

        invalid_duration = TranscriptionResultData(text="Test", segments=[], language="en", duration=-1.0, word_count=1)
        assert TranscriptParser.validate_result(invalid_duration) is False
