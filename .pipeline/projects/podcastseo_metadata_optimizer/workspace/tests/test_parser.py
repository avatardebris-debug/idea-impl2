"""Tests for transcript_parser.py."""

import pytest
from podcastseo.transcript_parser import TranscriptParser


class TestTranscriptParserDetectFormat:
    """Tests for format detection."""

    def test_detect_srt(self, srt_file):
        parser = TranscriptParser()
        fmt = parser._detect_format(srt_file)
        assert fmt == "srt"

    def test_detect_vtt(self, vtt_file):
        parser = TranscriptParser()
        fmt = parser._detect_vtt(vtt_file)
        assert fmt == "vtt"

    def test_detect_txt(self, txt_file):
        parser = TranscriptParser()
        fmt = parser._detect_txt(txt_file)
        assert fmt == "txt"

    def test_detect_unsupported(self, tmp_path):
        parser = TranscriptParser()
        f = tmp_path / "test.pdf"
        f.write_text("test")
        with pytest.raises(ValueError, match="Unsupported format"):
            parser._detect_format(str(f))


class TestTranscriptParserParseSRT:
    """Tests for SRT parsing."""

    def test_parse_srt_basic(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        assert result["format"] == "srt"
        assert "text" in result
        assert len(result["text"]) > 0
        assert result["word_count"] > 0

    def test_parse_srt_no_captions(self, tmp_path):
        parser = TranscriptParser()
        f = tmp_path / "empty.srt"
        f.write_text("1\n00:00:01,000 --> 00:00:02,000\n\n")
        result = parser.parse_raw(str(f))
        assert result["text"] == ""
        assert result["word_count"] == 0


class TestTranscriptParserParseVTT:
    """Tests for VTT parsing."""

    def test_parse_vtt_basic(self, vtt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(vtt_file)
        assert result["format"] == "vtt"
        assert "text" in result
        assert len(result["text"]) > 0

    def test_parse_vtt_no_captions(self, tmp_path):
        parser = TranscriptParser()
        f = tmp_path / "empty.vtt"
        f.write_text("WEBVTT\n\n")
        result = parser.parse_raw(str(f))
        assert result["text"] == ""


class TestTranscriptParserParseTXT:
    """Tests for TXT parsing."""

    def test_parse_txt_basic(self, txt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(txt_file)
        assert result["format"] == "txt"
        assert "text" in result
        assert len(result["text"]) > 0

    def test_parse_txt_empty(self, empty_file):
        parser = TranscriptParser()
        result = parser.parse_raw(empty_file)
        assert result["text"] == ""
        assert result["word_count"] == 0


class TestTranscriptParserCleanText:
    """Tests for text cleaning."""

    def test_clean_text_removes_newlines(self):
        parser = TranscriptParser()
        text = "Hello\n\nWorld\n\nTest"
        cleaned = parser._clean_text(text)
        assert "Hello World Test" in cleaned

    def test_clean_text_removes_speaker_tags(self):
        parser = TranscriptParser()
        text = "Host: Hello Guest: Hi"
        cleaned = parser._clean_text(text)
        assert "Host:" not in cleaned
        assert "Guest:" not in cleaned

    def test_clean_text_removes_music_tags(self):
        parser = TranscriptParser()
        text = "[Music] Hello [Music]"
        cleaned = parser._clean_text(text)
        assert "[Music]" not in cleaned

    def test_clean_text_removes_apostrophes(self):
        parser = TranscriptParser()
        text = "It's a test"
        cleaned = parser._clean_text(text)
        assert "It's" not in cleaned
        assert "Its" in cleaned


class TestTranscriptParserIntegration:
    """Integration tests for full parsing pipeline."""

    def test_full_pipeline_srt(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        assert result["format"] == "srt"
        assert len(result["text"]) > 100
        assert result["word_count"] > 50

    def test_full_pipeline_vtt(self, vtt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(vtt_file)
        assert result["format"] == "vtt"
        assert len(result["text"]) > 100

    def test_full_pipeline_txt(self, txt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(txt_file)
        assert result["format"] == "txt"
        assert len(result["text"]) > 100

    def test_nonexistent_file(self):
        parser = TranscriptParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_raw("/nonexistent/file.srt")

    def test_single_word(self, single_word_file):
        parser = TranscriptParser()
        result = parser.parse_raw(single_word_file)
        assert result["word_count"] == 2
