"""Tests for the Translator class."""

from unittest.mock import MagicMock, patch

import pytest

from video_babbel.core import TranslationError
from video_babbel.translator import SUPPORTED_LANGUAGES, Translator


class TestTranslator:
    """Tests for the Translator class."""

    def test_init_default_backend(self):
        """Default backend should be 'google'."""
        translator = Translator(target_lang="es")
        assert translator.target_lang == "es"
        assert translator.backend == "google"

    def test_init_custom_backend(self):
        """Custom backend should be set correctly."""
        translator = Translator(target_lang="es", backend="deepL")
        assert translator.backend == "deepL"

    def test_init_unsupported_language_raises_error(self):
        """TranslationError should be raised for unsupported languages."""
        with pytest.raises(TranslationError, match="Unsupported target language"):
            Translator(target_lang="xx")

    def test_supported_languages_contains_expected(self):
        """SUPPORTED_LANGUAGES should contain expected languages."""
        assert "en" in SUPPORTED_LANGUAGES
        assert "es" in SUPPORTED_LANGUAGES
        assert "fr" in SUPPORTED_LANGUAGES
        assert "ja" in SUPPORTED_LANGUAGES

    @patch("video_babbel.translator.Translator._translate_google")
    def test_translate_calls_google_backend(self, mock_translate):
        """translate should call the correct backend."""
        mock_translate.return_value = "Hola mundo"

        translator = Translator(target_lang="es")
        result = translator.translate("Hello world")

        assert result == "Hola mundo"
        mock_translate.assert_called_once_with("Hello world")

    @patch("video_babbel.translator.Translator._translate_deepl")
    def test_translate_calls_deepl_backend(self, mock_translate):
        """translate should call DeepL backend when configured."""
        mock_translate.return_value = "Hola mundo"

        translator = Translator(target_lang="es", backend="deepL")
        result = translator.translate("Hello world")

        assert result == "Hola mundo"
        mock_translate.assert_called_once_with("Hello world")

    def test_translate_empty_string(self):
        """translate should return empty string for empty input."""
        translator = Translator(target_lang="es")
        assert translator.translate("") == ""

    def test_translate_whitespace_only(self):
        """translate should return whitespace-only string as-is."""
        translator = Translator(target_lang="es")
        assert translator.translate("   ") == "   "

    @patch("video_babbel.translator.Translator._translate_google")
    def test_translate_unsupported_backend_raises_error(self, mock_translate):
        """TranslationError should be raised for unsupported backend."""
        translator = Translator(target_lang="es", backend="unsupported")
        with pytest.raises(TranslationError, match="Unsupported backend"):
            translator.translate("Hello world")

    @patch("video_babbel.translator.Translator._translate_google")
    def test_translate_exception_wrapped(self, mock_translate):
        """TranslationError should wrap underlying exceptions."""
        mock_translate.side_effect = Exception("google error")

        translator = Translator(target_lang="es")
        with pytest.raises(TranslationError, match="Translation failed"):
            translator.translate("Hello world")


class TestTranslateGoogle:
    """Tests for the _translate_google method."""

    @patch("video_babbel.translator._get_google_translator")
    def test_translate_google_success(self, mock_get_translator):
        """_translate_google should return translated text."""
        mock_translator_class = MagicMock()
        mock_translator = MagicMock()
        mock_translator.detect.return_value = MagicMock(lang="en")
        mock_result = MagicMock()
        mock_result.text = "Hola mundo"
        mock_translator.translate.return_value = mock_result
        mock_translator_class.return_value = mock_translator
        mock_get_translator.return_value = mock_translator_class

        translator = Translator(target_lang="es")
        result = translator._translate_google("Hello world")

        assert result == "Hola mundo"
        mock_translator.detect.assert_called_once_with("Hello world")
        mock_translator.translate.assert_called_once_with(
            "Hello world", src="en", dest="es"
        )

    def test_translate_google_import_error(self):
        """TranslationError should be raised if googletrans is not installed."""
        with patch.dict("sys.modules", {"googletrans": None}):
            translator = Translator(target_lang="es")
            with pytest.raises(TranslationError, match="googletrans is not installed"):
                translator._translate_google("Hello world")


class TestTranslateDeepL:
    """Tests for the _translate_deepl method."""

    @patch("video_babbel.translator._get_deepl")
    def test_translate_deepl_success(self, mock_get_deepl):
        """_translate_deepl should return translated text."""
        mock_deepl = MagicMock()
        mock_translator = MagicMock()
        mock_result = MagicMock()
        mock_result.text = "Hola mundo"
        mock_translator.translate_text.return_value = mock_result
        mock_deepl.Translator.return_value = mock_translator
        mock_get_deepl.return_value = mock_deepl

        with patch.dict("os.environ", {"DEEPL_API_KEY": "fake_key"}):
            translator = Translator(target_lang="es", backend="deepL")
            result = translator._translate_deepl("Hello world")

        assert result == "Hola mundo"
        mock_deepl.Translator.assert_called_once_with("fake_key")
        mock_translator.translate_text.assert_called_once_with(
            "Hello world", source_lang=None, target_lang="es"
        )

    @patch("video_babbel.translator._get_deepl")
    def test_translate_deepl_missing_api_key(self, mock_get_deepl):
        """TranslationError should be raised if DEEPL_API_KEY is not set."""
        mock_get_deepl.return_value = MagicMock()
        with patch.dict("os.environ", {}, clear=True):
            translator = Translator(target_lang="es", backend="deepL")
            with pytest.raises(TranslationError, match="DEEPL_API_KEY environment variable not set"):
                translator._translate_deepl("Hello world")

    def test_translate_deepl_import_error(self):
        """TranslationError should be raised if deepl is not installed."""
        with patch.dict("sys.modules", {"deepl": None}):
            translator = Translator(target_lang="es", backend="deepL")
            with pytest.raises(TranslationError, match="deepl is not installed"):
                translator._translate_deepl("Hello world")
