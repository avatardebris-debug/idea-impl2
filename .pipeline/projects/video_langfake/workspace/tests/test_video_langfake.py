"""Tests for video_langfake package."""

import json
import os
import tempfile
import shutil
import struct
import numpy as np
import pytest
from unittest.mock import patch

from video_langfake.audio import (
    extract_audio,
    transcribe_audio,
    save_transcription,
    load_transcription,
)
from video_langfake.translate import (
    translate_text,
    save_translation,
    load_translation,
    _mock_translate_string,
)
from video_langfake.synthesize import (
    synthesize_speech,
    generate_lip_params,
    apply_lip_sync,
    _write_wav,
)
from video_langfake.pipeline import VideoLangFake
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


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test files."""
    d = tempfile.mkdtemp(prefix="vlf_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_wav_path(tmp_dir):
    """Create a sample WAV file for testing."""
    path = os.path.join(tmp_dir, "sample.wav")
    sample_rate = 16000
    duration = 1.0
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    waveform = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    _write_wav(path, waveform, sample_rate)
    return path


@pytest.fixture
def sample_video_path(tmp_dir):
    """Create a minimal MP4 video file for testing."""
    path = os.path.join(tmp_dir, "sample.mp4")
    # Create a minimal valid MP4 using moviepy if available
    try:
        from moviepy import VideoFileClip, ColorClip, AudioClip
        import subprocess
        import numpy as np

        # Create a simple color clip
        clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1.0)
        
        # Create a dummy audio clip
        make_frame = lambda t: [np.sin(440 * 2 * np.pi * t)]
        audio = AudioClip(make_frame, duration=1.0)
        clip = clip.with_audio(audio)
        
        clip.write_videofile(path, fps=10, codec="libx264", audio_codec="aac", logger=None)
        clip.close()
    except Exception:
        # Fallback: create a dummy file
        with open(path, "wb") as f:
            f.write(b"dummy video file")
    return path


@pytest.fixture
def sample_transcription():
    """Create a sample transcription dict."""
    return {
        "text": "Hello world, this is a test.",
        "segments": [
            {"start": 0.0, "end": 1.5, "text": "Hello world,"},
            {"start": 1.5, "end": 3.0, "text": "this is a test."},
        ],
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world,", "start": 0.5, "end": 1.0},
            {"word": "this", "start": 1.5, "end": 2.0},
            {"word": "is", "start": 2.0, "end": 2.5},
            {"word": "a", "start": 2.5, "end": 2.7},
            {"word": "test.", "start": 2.7, "end": 3.0},
        ],
    }


@pytest.fixture
def sample_translation():
    """Create a sample translation dict."""
    return {
        "translated_text": "Hola mundo, esta es una prueba.",
        "segments": [
            {"start": 0.0, "end": 1.5, "text": "Hola mundo,"},
            {"start": 1.5, "end": 3.0, "text": "esta es una prueba."},
        ],
        "source_lang": "en",
        "target_lang": "es",
    }


# ============================================================
# Exception Tests
# ============================================================

class TestExceptions:
    """Test exception classes."""

    def test_base_error(self):
        """Test VideoLangFakeError base class."""
        err = VideoLangFakeError("test message")
        assert "test message" in str(err)
        assert err.details == {}

    def test_base_error_with_details(self):
        """Test VideoLangFakeError with details."""
        details = {"key": "value"}
        err = VideoLangFakeError("test message", details)
        assert err.details == details

    def test_pipeline_error(self):
        """Test PipelineError."""
        err = PipelineError("step1", "failed")
        assert err.step == "step1"
        assert "step1" in str(err)
        assert "failed" in str(err)

    def test_audio_error(self):
        """Test AudioError."""
        err = AudioError("extract", "file not found")
        assert err.operation == "extract"
        assert "extract" in str(err)

    def test_transcription_error(self):
        """Test TranscriptionError."""
        err = TranscriptionError("whisper failed")
        assert err.operation == "transcription"
        assert "transcription" in str(err)

    def test_translation_error(self):
        """Test TranslationError."""
        err = TranslationError("en", "es", "api error")
        assert err.source_lang == "en"
        assert err.target_lang == "es"
        assert "en" in str(err)
        assert "es" in str(err)

    def test_synthesis_error(self):
        """Test SynthesisError."""
        err = SynthesisError("hello world", "tts failed")
        assert "hello world" in str(err)
        assert "tts failed" in str(err)

    def test_lip_sync_error(self):
        """Test LipSyncError."""
        err = LipSyncError("generate", "model error")
        assert err.operation == "generate"
        assert "generate" in str(err)

    def test_video_error(self):
        """Test VideoError."""
        err = VideoError("merge", "codec error")
        assert err.operation == "merge"
        assert "merge" in str(err)

    def test_configuration_error(self):
        """Test ConfigurationError."""
        err = ConfigurationError("api_key", "invalid")
        assert err.config_key == "api_key"
        assert "api_key" in str(err)


# ============================================================
# Audio Module Tests
# ============================================================

class TestAudio:
    """Test audio module functions."""
    
    @pytest.fixture(autouse=True)
    def mock_whisper(self):
        with patch("video_langfake.audio.WHISPER_AVAILABLE", False):
            yield

    def test_extract_audio_nonexistent(self, tmp_dir):
        """Test extract_audio with nonexistent file."""
        with pytest.raises(AudioError, match="not found"):
            extract_audio(os.path.join(tmp_dir, "nonexistent.mp4"))

    def test_transcribe_audio_nonexistent(self, tmp_dir):
        """Test transcribe_audio with nonexistent file."""
        with pytest.raises(TranscriptionError, match="not found"):
            transcribe_audio(os.path.join(tmp_dir, "nonexistent.wav"))

    def test_save_load_transcription(self, tmp_dir, sample_transcription):
        """Test saving and loading transcription."""
        output_path = os.path.join(tmp_dir, "transcription.json")
        saved = save_transcription(sample_transcription, output_path)
        assert saved == output_path
        assert os.path.exists(output_path)

        loaded = load_transcription(output_path)
        assert loaded["text"] == sample_transcription["text"]
        assert len(loaded["segments"]) == len(sample_transcription["segments"])
        assert len(loaded["words"]) == len(sample_transcription["words"])

    def test_load_transcription_nonexistent(self, tmp_dir):
        """Test loading nonexistent transcription."""
        with pytest.raises(TranscriptionError, match="not found"):
            load_transcription(os.path.join(tmp_dir, "nonexistent.json"))

    def test_load_transcription_invalid_json(self, tmp_dir):
        """Test loading invalid JSON transcription."""
        path = os.path.join(tmp_dir, "invalid.json")
        with open(path, "w") as f:
            f.write("{invalid json}")
        with pytest.raises(TranscriptionError, match="Invalid JSON"):
            load_transcription(path)

    def test_transcribe_audio_mock(self, sample_wav_path):
        """Test mock transcription."""
        result = transcribe_audio(sample_wav_path)
        assert "text" in result
        assert "segments" in result
        assert "words" in result
        assert len(result["segments"]) > 0
        assert len(result["words"]) > 0


# ============================================================
# Translation Module Tests
# ============================================================

class TestTranslate:
    """Test translation module functions."""

    def test_translate_text_empty(self):
        """Test translation with empty text."""
        with pytest.raises(TranslationError, match="Empty text"):
            translate_text("", "en", "es")

    def test_translate_text_no_segments(self):
        """Test translation without segments."""
        result = translate_text("Hello world", "en", "es")
        assert "translated_text" in result
        assert "segments" in result
        assert result["source_lang"] == "en"
        assert result["target_lang"] == "es"
        assert len(result["segments"]) == 1

    def test_translate_text_with_segments(self, sample_transcription):
        """Test translation with segments."""
        result = translate_text(
            sample_transcription["text"],
            "en",
            "es",
            segments=sample_transcription["segments"],
        )
        assert "translated_text" in result
        assert "segments" in result
        assert len(result["segments"]) == len(sample_transcription["segments"])
        # Check timing is preserved
        for orig, trans in zip(sample_transcription["segments"], result["segments"]):
            assert orig["start"] == trans["start"]
            assert orig["end"] == trans["end"]

    def test_mock_translate_string(self):
        """Test mock translation string function."""
        result = _mock_translate_string("Hello", "en", "es")
        assert result != "Hello"  # Should be shifted
        assert len(result) == len("Hello")

    def test_save_load_translation(self, tmp_dir, sample_translation):
        """Test saving and loading translation."""
        output_path = os.path.join(tmp_dir, "translation.json")
        saved = save_translation(sample_translation, output_path)
        assert saved == output_path
        assert os.path.exists(output_path)

        loaded = load_translation(output_path)
        assert loaded["translated_text"] == sample_translation["translated_text"]
        assert loaded["source_lang"] == "en"
        assert loaded["target_lang"] == "es"

    def test_load_translation_nonexistent(self, tmp_dir):
        """Test loading nonexistent translation."""
        with pytest.raises(TranslationError, match="not found"):
            load_translation(os.path.join(tmp_dir, "nonexistent.json"))

    def test_load_translation_invalid_json(self, tmp_dir):
        """Test loading invalid JSON translation."""
        path = os.path.join(tmp_dir, "invalid.json")
        with open(path, "w") as f:
            f.write("{invalid json}")
        with pytest.raises(TranslationError, match="Invalid JSON"):
            load_translation(path)


# ============================================================
# Synthesize Module Tests
# ============================================================

class TestSynthesize:
    """Test synthesis module functions."""

    def test_synthesize_speech_empty_text(self):
        """Test synthesis with empty text."""
        with pytest.raises(SynthesisError, match="Empty text"):
            synthesize_speech("", "es")

    def test_synthesize_speech_no_target_lang(self):
        """Test synthesis with no target language."""
        with pytest.raises(SynthesisError, match="cannot be empty"):
            synthesize_speech("Hello", "")

    def test_synthesize_speech_creates_file(self, tmp_dir):
        """Test that synthesis creates a WAV file."""
        output_path = os.path.join(tmp_dir, "synthesized.wav")
        result = synthesize_speech("Hello world", "es", output_path)
        assert result == output_path
        assert os.path.exists(output_path)
        # Verify it's a valid WAV file
        with open(output_path, "rb") as f:
            header = f.read(4)
            assert header == b"RIFF"

    def test_generate_lip_params_nonexistent_video(self, tmp_dir):
        """Test lip params generation with nonexistent video."""
        with pytest.raises(LipSyncError, match="not found"):
            generate_lip_params(
                os.path.join(tmp_dir, "nonexistent.mp4"),
                "/tmp/audio.wav",
            )

    def test_generate_lip_params_creates_file(self, tmp_dir, sample_video_path):
        """Test that lip params generation creates a JSON file."""
        audio_path = os.path.join(tmp_dir, "audio.wav")
        # Create a dummy audio file
        with open(audio_path, "wb") as f:
            f.write(b"dummy audio")
        output_path = os.path.join(tmp_dir, "lip_params.json")
        result = generate_lip_params(sample_video_path, audio_path, output_path)
        assert result == output_path
        assert os.path.exists(output_path)
        # Verify it's valid JSON
        with open(output_path, "r") as f:
            data = json.load(f)
            assert "fps" in data
            assert "duration" in data
            assert "params" in data

    def test_apply_lip_sync_nonexistent_video(self, tmp_dir):
        """Test lip sync application with nonexistent video."""
        with pytest.raises(LipSyncError, match="not found"):
            apply_lip_sync(
                os.path.join(tmp_dir, "nonexistent.mp4"),
                "/tmp/audio.wav",
                "/tmp/params.json",
            )

    def test_apply_lip_sync_creates_file(self, tmp_dir, sample_video_path):
        """Test that lip sync application creates a video file."""
        audio_path = os.path.join(tmp_dir, "audio.wav")
        params_path = os.path.join(tmp_dir, "params.json")
        # Create dummy files
        with open(audio_path, "wb") as f:
            f.write(b"dummy audio")
        with open(params_path, "w") as f:
            json.dump({"fps": 30, "duration": 1.0, "params": []}, f)
        output_path = os.path.join(tmp_dir, "output.mp4")
        result = apply_lip_sync(sample_video_path, audio_path, params_path, output_path)
        assert result == output_path
        assert os.path.exists(output_path)

    def test_write_wav(self, tmp_dir):
        """Test _write_wav helper function."""
        path = os.path.join(tmp_dir, "test.wav")
        sample_rate = 16000
        waveform = np.sin(np.linspace(0, 1, sample_rate)).astype(np.float32)
        _write_wav(path, waveform, sample_rate)
        assert os.path.exists(path)
        with open(path, "rb") as f:
            header = f.read(4)
            assert header == b"RIFF"


# ============================================================
# Pipeline Tests
# ============================================================

class TestPipeline:
    """Test the main pipeline class."""
    
    @pytest.fixture(autouse=True)
    def mock_whisper(self):
        with patch("video_langfake.audio.WHISPER_AVAILABLE", False):
            yield

    def test_pipeline_nonexistent_video(self, tmp_dir):
        """Test pipeline with nonexistent video."""
        pipeline = VideoLangFake()
        with pytest.raises(PipelineError, match="not found"):
            pipeline.process(
                video_path=os.path.join(tmp_dir, "nonexistent.mp4"),
                target_language="es",
                output_path=os.path.join(tmp_dir, "output.mp4"),
            )
        pipeline.cleanup()

    def test_pipeline_no_target_language(self, tmp_dir, sample_video_path):
        """Test pipeline with no target language."""
        pipeline = VideoLangFake()
        with pytest.raises(PipelineError, match="must be specified"):
            pipeline.process(
                video_path=sample_video_path,
                target_language="",
                output_path=os.path.join(tmp_dir, "output.mp4"),
            )
        pipeline.cleanup()

    def test_pipeline_no_output_path(self, tmp_dir, sample_video_path):
        """Test pipeline with no output path."""
        pipeline = VideoLangFake()
        with pytest.raises(PipelineError, match="must be specified"):
            pipeline.process(
                video_path=sample_video_path,
                target_language="es",
                output_path="",
            )
        pipeline.cleanup()

    def test_pipeline_full_run(self, tmp_dir, sample_video_path):
        """Test full pipeline run."""
        pipeline = VideoLangFake()
        output_path = os.path.join(tmp_dir, "output.mp4")
        try:
            result = pipeline.process(
                video_path=sample_video_path,
                target_language="es",
                output_path=output_path,
                source_language="en",
            )
            assert result == output_path
            assert os.path.exists(output_path)
        finally:
            pipeline.cleanup()

    def test_pipeline_cleanup(self, tmp_dir, sample_video_path):
        """Test that pipeline cleans up temp directory."""
        pipeline = VideoLangFake()
        tmp_dir_path = pipeline._tmp_dir
        output_path = os.path.join(tmp_dir, "output.mp4")
        try:
            pipeline.process(
                video_path=sample_video_path,
                target_language="es",
                output_path=output_path,
            )
        finally:
            pipeline.cleanup()
        assert not os.path.exists(tmp_dir_path)

    def test_pipeline_cleanup_on_error(self, tmp_dir):
        """Test that pipeline cleans up even on error."""
        pipeline = VideoLangFake()
        tmp_dir_path = pipeline._tmp_dir
        with pytest.raises(PipelineError):
            pipeline.process(
                video_path=os.path.join(tmp_dir, "nonexistent.mp4"),
                target_language="es",
                output_path=os.path.join(tmp_dir, "output.mp4"),
            )
        assert not os.path.exists(tmp_dir_path)


# ============================================================
# Integration Tests
# ============================================================

class TestIntegration:
    """Integration tests for the full workflow."""
    
    @pytest.fixture(autouse=True)
    def mock_whisper(self):
        with patch("video_langfake.audio.WHISPER_AVAILABLE", False):
            yield

    def test_full_workflow(self, tmp_dir, sample_video_path):
        """Test the complete workflow end-to-end."""
        # Step 1: Extract audio
        audio_path = os.path.join(tmp_dir, "audio.wav")
        # Skip actual extraction for speed; use a dummy file
        with open(audio_path, "wb") as f:
            f.write(b"dummy audio")

        # Step 2: Transcribe
        transcription = transcribe_audio(audio_path)
        assert "text" in transcription

        # Step 3: Translate
        translation = translate_text(
            transcription["text"],
            source_lang="en",
            target_lang="es",
            segments=transcription.get("segments"),
        )
        assert "translated_text" in translation

        # Step 4: Synthesize
        synthesized_path = os.path.join(tmp_dir, "synthesized.wav")
        synthesize_speech(translation["translated_text"], "es", synthesized_path)
        assert os.path.exists(synthesized_path)

        # Step 5: Generate lip params
        lip_params_path = os.path.join(tmp_dir, "lip_params.json")
        generate_lip_params(sample_video_path, synthesized_path, lip_params_path)
        assert os.path.exists(lip_params_path)

        # Step 6: Apply lip sync
        output_path = os.path.join(tmp_dir, "output.mp4")
        apply_lip_sync(sample_video_path, synthesized_path, lip_params_path, output_path)
        assert os.path.exists(output_path)

    def test_pipeline_class_integration(self, tmp_dir, sample_video_path):
        """Test using the VideoLangFake class."""
        pipeline = VideoLangFake()
        output_path = os.path.join(tmp_dir, "output.mp4")
        try:
            result = pipeline.process(
                video_path=sample_video_path,
                target_language="fr",
                output_path=output_path,
            )
            assert result == output_path
            assert os.path.exists(output_path)
        finally:
            pipeline.cleanup()


# ============================================================
# Edge Case Tests
# ============================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture(autouse=True)
    def mock_whisper(self):
        with patch("video_langfake.audio.WHISPER_AVAILABLE", False):
            yield

    def test_translate_with_special_characters(self):
        """Test translation with special characters."""
        text = "Hello! @#$% World?"
        result = translate_text(text, "en", "es")
        assert "translated_text" in result
        assert len(result["translated_text"]) > 0

    def test_translate_with_unicode(self):
        """Test translation with Unicode characters."""
        text = "Hello 世界 🌍"
        result = translate_text(text, "en", "zh")
        assert "translated_text" in result

    def test_synthesize_long_text(self):
        """Test synthesis with long text."""
        long_text = " ".join(["word"] * 1000)
        output_path = "/tmp/long_synthesis.wav"
        try:
            result = synthesize_speech(long_text, "en", output_path)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_pipeline_with_none_source_lang(self, tmp_dir, sample_video_path):
        """Test pipeline with None source language."""
        pipeline = VideoLangFake()
        output_path = os.path.join(tmp_dir, "output.mp4")
        try:
            result = pipeline.process(
                video_path=sample_video_path,
                target_language="es",
                output_path=output_path,
                source_language=None,
            )
            assert result == output_path
        finally:
            pipeline.cleanup()
