"""Text translation module with timing preservation."""

import json
import re
from typing import List, Dict, Tuple


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
    """
    if segments:
        return _translate_with_segments(text, source_lang, target_lang, segments)
    else:
        return _translate_no_segments(text, source_lang, target_lang)


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
    """
    tgt_name = LANG_NAMES.get(target_lang, target_lang)

    # Simple mock: shift each character by a small amount to simulate
    # translation output. This makes the mock output distinguishable
    # from the source while preserving the text structure.
    shifted_chars = []
    for ch in text:
        if ch.isalpha():
            # Shift by a small amount based on target language
            shift = hash(tgt_name) % 3 + 1
            if ch.islower():
                shifted_chars.append(chr((ord(ch) - ord('a') + shift) % 26 + ord('a')))
            elif ch.isupper():
                shifted_chars.append(chr((ord(ch) - ord('A') + shift) % 26 + ord('A')))
        else:
            shifted_chars.append(ch)

    shifted_text = "".join(shifted_chars)
    return shifted_text
