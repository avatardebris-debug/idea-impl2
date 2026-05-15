"""Text translation module with timing preservation."""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from video_langfake.exceptions import TranslationError

# Language code mapping for mock translation
LANG_NAMES = {
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
    "ar": "Arabic",
    "hi": "Hindi",
}

# Supported language codes
SUPPORTED_LANGUAGES = set(LANG_NAMES.keys())


def translate_text(
    text: str,
    source_lang: str = "en",
    target_lang: str = "es",
    segments: List[Dict] = None,
) -> Dict:
    """Translate text from source language to target language.

    Preserves timing information from input segments.

    Args:
        text: Source text to translate.
        source_lang: Source language code (e.g. 'en').
        target_lang: Target language code (e.g. 'es').
        segments: Optional list of segment dicts with 'start', 'end', 'text'
            from transcription. Timing is preserved.

    Returns:
        A dict with keys:
            - 'translated_text': The translated string.
            - 'segments': List of dicts with 'start', 'end', 'text' aligned
                to the original timing.
            - 'source_lang': Source language code.
            - 'target_lang': Target language code.

    Raises:
        TranslationError: If translation fails.
    """
    if not text or not text.strip():
        raise TranslationError(source_lang, target_lang, "Empty text provided")

    if not source_lang or not target_lang:
        raise TranslationError(source_lang, target_lang, "Language codes cannot be empty")

    try:
        if segments:
            return _translate_with_segments(text, source_lang, target_lang, segments)
        else:
            return _translate_no_segments(text, source_lang, target_lang)
    except TranslationError:
        raise
    except Exception as e:
        raise TranslationError(source_lang, target_lang, f"Translation failed: {e}")


def _translate_with_segments(
    text: str,
    source_lang: str,
    target_lang: str,
    segments: List[Dict],
) -> Dict:
    """Translate preserving segment timing."""
    translated_segments = []
    translated_parts = []

    for seg in segments:
        seg_text = seg.get("text", "")
        translated = _mock_translate_string(seg_text, source_lang, target_lang)
        translated_segments.append({
            "start": seg.get("start", 0.0),
            "end": seg.get("end", 0.0),
            "text": translated,
        })
        translated_parts.append(translated)

    return {
        "translated_text": " ".join(translated_parts),
        "segments": translated_segments,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }


def _translate_no_segments(
    text: str,
    source_lang: str,
    target_lang: str,
) -> Dict:
    """Translate without segment timing — returns a single segment."""
    translated = _mock_translate_string(text, source_lang, target_lang)
    return {
        "translated_text": translated,
        "segments": [
            {
                "start": 0.0,
                "end": float(len(text.split()) * 0.4),  # rough estimate
                "text": translated,
            }
        ],
        "source_lang": source_lang,
        "target_lang": target_lang,
    }


def _mock_translate_string(text: str, source_lang: str, target_lang: str) -> str:
    """Mock translation that simulates translation with a language tag.

    In a production system, this would call a real translation API
    (e.g., Google Translate, DeepL, or a local model like NLLB).

    For MVP, we use a simple Caesar-like cipher to simulate translation
    output, making the mock distinguishable from the source text.

    Uses a deterministic shift based on language codes (not hash())
    so results are reproducible across runs.
    """
    # Deterministic shift based on target_lang
    shift = sum(ord(c) * (i + 1) for i, c in enumerate(target_lang)) % 25 + 1

    shifted_chars = []
    for ch in text:
        if ch.isalpha():
            if ch.islower():
                shifted_chars.append(chr((ord(ch) - ord('a') + shift) % 26 + ord('a')))
            elif ch.isupper():
                shifted_chars.append(chr((ord(ch) - ord('A') + shift) % 26 + ord('A')))
        else:
            shifted_chars.append(ch)

    return "".join(shifted_chars)


def save_translation(translation: Dict, output_path: str) -> str:
    """Save translation results to a JSON file.

    Args:
        translation: Dict from translate_text().
        output_path: Path to save the JSON file.

    Returns:
        The output path.

    Raises:
        TranslationError: If saving fails.
    """
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(translation, f, indent=2, ensure_ascii=False)
        return output_path
    except Exception as e:
        raise TranslationError(
            translation.get("source_lang", ""),
            translation.get("target_lang", ""),
            f"Failed to save translation: {e}",
        )


def load_translation(input_path: str) -> Dict:
    """Load translation results from a JSON file.

    Args:
        input_path: Path to the JSON file.

    Returns:
        The translation dict.

    Raises:
        TranslationError: If loading fails.
    """
    if not os.path.exists(input_path):
        raise TranslationError("", "", f"Translation file not found: {input_path}")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise TranslationError("", "", f"Invalid JSON in translation file: {e}")
    except Exception as e:
        raise TranslationError("", "", f"Failed to load translation: {e}")
