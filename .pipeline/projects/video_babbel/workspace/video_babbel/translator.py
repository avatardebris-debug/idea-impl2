"""Translation module — translates text between languages."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from video_babbel.core import TranslationError, get_logger

logger = get_logger(__name__)

# Supported languages: ISO 639-1 code → display name
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ru": "Russian",
}


def _get_google_translator():
    """Import and return GoogleTranslator, raising TranslationError if unavailable."""
    try:
        from googletrans import Translator as GoogleTranslator
        return GoogleTranslator
    except ImportError:
        raise TranslationError("googletrans is not installed")


def _get_deepl():
    """Import and return deepl module, raising TranslationError if unavailable."""
    try:
        import deepl
        return deepl
    except ImportError:
        raise TranslationError("deepl is not installed")


class Translator:
    """Translates text between languages.

    Parameters
    ----------
    target_lang : str
        ISO 639-1 code for the target language.
    source_lang : str, optional
        ISO 639-1 code for the source language (auto-detected if None).
    backend : str, optional
        Translation backend to use.  Supported values are ``"google"`` and
        ``"deepL"``.  Default is ``"google"``.
    """

    def __init__(
        self,
        target_lang: str,
        source_lang: Optional[str] = None,
        backend: str = "google",
    ) -> None:
        if target_lang not in SUPPORTED_LANGUAGES:
            raise TranslationError(
                f"Unsupported target language: {target_lang}",
                target_lang=target_lang,
            )
        self.target_lang = target_lang
        self.source_lang = source_lang
        self.backend = backend
        logger.info(
            "Initializing Translator: %s → %s (backend=%s)",
            source_lang or "auto",
            target_lang,
            backend,
        )

    def translate(self, text: str) -> str:
        """Translate *text* to the target language.

        Parameters
        ----------
        text : str
            The source text to translate.

        Returns
        ----- --
        str
            The translated text.

        Raises
        ------
        TranslationError
            If translation fails.
        """
        if not text or not text.strip():
            return text

        logger.info("Translating text to %s", self.target_lang)
        try:
            if self.backend == "google":
                return self._translate_google(text)
            elif self.backend == "deepL":
                return self._translate_deepl(text)
            else:
                raise TranslationError(
                    f"Unsupported backend: {self.backend}",
                    target_lang=self.target_lang,
                )
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(
                f"Translation failed: {exc}",
                source_lang=self.source_lang,
                target_lang=self.target_lang,
            ) from exc

    def _translate_google(self, text: str) -> str:
        """Translate using Google Translate (via googletrans)."""
        GoogleTranslator = _get_google_translator()
        translator = GoogleTranslator()
        detected = translator.detect(text)
        result = translator.translate(text, src=detected.lang, dest=self.target_lang)
        return result.text

    def _translate_deepl(self, text: str) -> str:
        """Translate using DeepL API."""
        deepl = _get_deepl()
        api_key = os.environ.get("DEEPL_API_KEY")
        if not api_key:
            raise TranslationError("DEEPL_API_KEY environment variable not set")

        translator = deepl.Translator(api_key)
        result = translator.translate_text(
            text,
            source_lang=self.source_lang or None,
            target_lang=self.target_lang,
        )
        return result.text
