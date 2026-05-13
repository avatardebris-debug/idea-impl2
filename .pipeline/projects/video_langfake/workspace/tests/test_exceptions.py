"""Tests for video_langfake.exceptions module."""

import pytest
from video_langfake.exceptions import (
    VideoLangFakeError,
    PipelineError,
    AudioError,
    TranscriptionError,
    TranslationError,
    SynthesisError,
    LipSyncError,
    VideoError,
    ConfigurationError,
)


class TestVideoLangFakeError:
    def test_base_error_message(self):
        err = VideoLangFakeError("test message")
        assert str(err) == "test message"
        assert err.message == "test message"
        assert err.details == {}

    def test_base_error_with_details(self):
        err = VideoLangFakeError("test message", {"key": "value"})
        assert err.details == {"key": "value"}

    def test_base_error_is_exception(self):
        err = VideoLangFakeError("test")
        assert isinstance(err, Exception)


class TestPipelineError:
    def test_pipeline_error_attributes(self):
        err = PipelineError("transcribe", "file not found")
        assert err.step == "transcribe"
        assert "transcribe" in str(err)
        assert "file not found" in str(err)

    def test_pipeline_error_with_details(self):
        err = PipelineError("translate", "error", {"code": 500})
        assert err.details == {"code": 500}


class TestAudioError:
    def test_audio_error_attributes(self):
        err = AudioError("extract", "codec not supported")
        assert err.operation == "extract"
        assert "extract" in str(err)
        assert "codec not supported" in str(err)


class TestTranscriptionError:
    def test_transcription_error_inherits_audio_error(self):
        err = TranscriptionError("model not found")
        assert err.operation == "transcription"
        assert isinstance(err, AudioError)


class TestTranslationError:
    def test_translation_error_attributes(self):
        err = TranslationError("en", "es", "api timeout")
        assert err.source_lang == "en"
        assert err.target_lang == "es"
        assert "en" in str(err)
        assert "es" in str(err)
        assert "api timeout" in str(err)


class TestSynthesisError:
    def test_synthesis_error_truncates_text(self):
        long_text = "a" * 100
        err = SynthesisError(long_text, "voice not available")
        assert "a" * 50 in str(err)
        assert "..." in str(err)

    def test_synthesis_error_short_text(self):
        err = SynthesisError("hi", "voice not available")
        assert "hi" in str(err)


class TestLipSyncError:
    def test_lipsync_error_attributes(self):
        err = LipSyncError("align", "timing mismatch")
        assert err.operation == "align"
        assert "align" in str(err)


class TestVideoError:
    def test_video_error_attributes(self):
        err = VideoError("encode", "format not supported")
        assert err.operation == "encode"
        assert "encode" in str(err)


class TestConfigurationError:
    def test_config_error_attributes(self):
        err = ConfigurationError("model_path", "not found")
        assert err.config_key == "model_path"
        assert "model_path" in str(err)
