"""
translator.py — LLM translation wrapper.

Priority:
1. Import from video_babbel workspace (reuse existing LLM connection)
2. Fall back to Ollama via direct HTTP call

Takes segments from transcriber.py and adds "l2_text" field to each.
Batches in groups of 20 for efficiency.
"""
from __future__ import annotations
import json
import pathlib
import sys
import urllib.request
import urllib.error
from typing import Any


_VB_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "video_babbel" / "workspace"
_OLLAMA_HOST = "http://localhost:11434"
_BATCH_SIZE = 20


# ---------------------------------------------------------------------------
# Try to reuse video_babbel workspace
# ---------------------------------------------------------------------------

def _try_import_vb_translate():
    """Attempt to import translate() from video_babbel workspace."""
    if _VB_PATH.exists():
        sys.path.insert(0, str(_VB_PATH))
        try:
            import video_babbel as _vb  # type: ignore
            if hasattr(_vb, "translate"):
                return _vb.translate
        except ImportError:
            pass
        try:
            import translator as _tr  # type: ignore
            if hasattr(_tr, "translate"):
                return _tr.translate
        except ImportError:
            pass
    return None


# ---------------------------------------------------------------------------
# Ollama direct fallback
# ---------------------------------------------------------------------------

def _ollama_translate_batch(texts: list[str], target_lang: str, source_lang: str, model: str = "qwen3:6b") -> list[str]:
    """Translate a batch of texts via Ollama /api/generate."""
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    prompt = (
        f"Translate the following {len(texts)} numbered sentences from {source_lang} to {target_lang}. "
        f"Return ONLY a JSON array of translated strings in the same order, no explanation.\n\n"
        f"{numbered}"
    )
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{_OLLAMA_HOST}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        response_text = raw.get("response", "").strip()
        # Extract JSON array from response (may have markdown fences)
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        if start >= 0 and end > start:
            translations = json.loads(response_text[start:end])
            if isinstance(translations, list) and len(translations) == len(texts):
                return [str(t) for t in translations]
    except Exception:
        pass
    # Fallback: return placeholder for each
    return [f"[{target_lang}] {t}" for t in texts]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate(
    segments: list[dict[str, Any]],
    target_lang: str,
    source_lang: str = "en",
    model: str = "qwen3:6b",
) -> list[dict[str, Any]]:
    """Translate segments and add 'l2_text' field to each.

    Args:
        segments:    List of segment dicts from transcriber.transcribe().
        target_lang: BCP-47 target language code (e.g. "es", "de", "fr").
        source_lang: BCP-47 source language code (default: "en").
        model:       Ollama model name for fallback translation.

    Returns:
        Same list of segments with 'l2_text' field populated.
    """
    if not segments:
        return segments

    # Try video_babbel workspace first
    vb_fn = _try_import_vb_translate()
    if vb_fn is not None:
        try:
            result = vb_fn(segments, target_lang=target_lang, source_lang=source_lang)
            if result and "l2_text" in result[0]:
                return result
        except Exception:
            pass

    # Ollama fallback — batch translate
    texts = [seg.get("text", "") for seg in segments]
    all_translated = []

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        translated = _ollama_translate_batch(batch, target_lang, source_lang, model)
        all_translated.extend(translated)

    for seg, l2 in zip(segments, all_translated):
        seg["l2_text"] = l2

    return segments
