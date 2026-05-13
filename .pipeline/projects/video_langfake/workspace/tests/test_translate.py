"""Tests for video_langfake.translate module."""

import json
import os
import tempfile
import pytest

from video_langfake.translate import (
    translate_text,
    save_translation,
    load_translation,
    SUPPORTED_LANGUAGES,
    LANG_NAMES,
)
from video_langfake.exceptions import TranslationError


class TestTranslateText:
    def test_translate_text_basic(self):
        result = translate_text("Hello world", "en", "es")
        assert result["translated_text"] != "Hello world"
        assert result["source_lang"] == "en"
        assert result["target_lang"] == "es"
        assert len(result["segments"]) == 1

    def test_translate_text_empty_text(self):
        with pytest.raises(TranslationError, match="Empty text provided"):
            translate_text("", "en", "es")

    def test_translate_text_empty_source_lang(self):
        with pytest.raises(TranslationError, match="Language codes cannot be empty"):
            translate_text("Hello", "", "es")

    def test_translate_text_empty_target_lang(self):
        with pytest.raises(TranslationError, match="Language codes cannot be empty"):
            translate_text("Hello", "en", "")

    def test_translate_text_with_segments(self):
        segments = [
            {"start": 0.0, "end": 1.0, "text": "Hello"},
            {"start": 1.5, "end": 2.5, "text": "world"},
        ]
        result = translate_text("Hello world", "en", "es", segments=segments)
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 1.0
        assert result["segments"][1]["start"] == 1.5

    def test_translate_text_deterministic(self):
        result1 = translate_text("Hello world", "en", "es")
        result2 = translate_text("Hello world", "en", "es")
        assert result1["translated_text"] == result2["translated_text"]

    def test_translate_text_different_languages(self):
        result_es = translate_text("Hello", "en", "es")
        result_fr = translate_text("Hello", "en", "fr")
        # Different target languages should produce different results
        assert result_es["translated_text"] != result_fr["translated_text"]

    def test_translate_text_preserves_punctuation(self):
        result = translate_text("Hello, world!", "en", "es")
        # Punctuation should be preserved
        assert "," in result["translated_text"] or "," in result["segments"][0]["text"]


class TestSaveTranslation:
    def test_save_translation(self):
        translation = {
            "translated_text": "Hola mundo",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Hola mundo"}],
            "source_lang": "en",
            "target_lang": "es",
        }
        tmp_file = tempfile.mktemp(suffix=".json")
        try:
            result = save_translation(translation, tmp_file)
            assert result == tmp_file
            assert os.path.exists(tmp_file)
            with open(tmp_file, "r") as f:
                loaded = json.load(f)
            assert loaded["translated_text"] == translation["translated_text"]
        finally:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)

    def test_save_translation_creates_parent_dirs(self):
        translation = {"translated_text": "test", "segments": [], "source_lang": "en", "target_lang": "es"}
        tmp_dir = tempfile.mkdtemp()
        tmp_file = os.path.join(tmp_dir, "subdir", "output.json")
        try:
            result = save_translation(translation, tmp_file)
            assert os.path.exists(tmp_file)
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)


class TestLoadTranslation:
    def test_load_translation(self):
        tmp_file = tempfile.mktemp(suffix=".json")
        data = {"translated_text": "Hola", "segments": [], "source_lang": "en", "target_lang": "es"}
        with open(tmp_file, "w") as f:
            json.dump(data, f)
        try:
            result = load_translation(tmp_file)
            assert result["translated_text"] == "Hola"
        finally:
            os.unlink(tmp_file)

    def test_load_translation_file_not_found(self):
        with pytest.raises(TranslationError, match="Translation file not found"):
            load_translation("/nonexistent/file.json")

    def test_load_translation_invalid_json(self):
        tmp_file = tempfile.mktemp(suffix=".json")
        with open(tmp_file, "w") as f:
            f.write("not valid json {{{")
        try:
            with pytest.raises(TranslationError, match="Invalid JSON"):
                load_translation(tmp_file)
        finally:
            os.unlink(tmp_file)


class TestConstants:
    def test_supported_languages(self):
        assert "en" in SUPPORTED_LANGUAGES
        assert "es" in SUPPORTED_LANGUAGES
        assert "fr" in SUPPORTED_LANGUAGES

    def test_lang_names(self):
        assert LANG_NAMES["en"] == "English"
        assert LANG_NAMES["es"] == "Spanish"
        assert LANG_NAMES["ja"] == "Japanese"
