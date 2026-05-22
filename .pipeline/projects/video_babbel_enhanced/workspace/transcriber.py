"""
transcriber.py — Whisper STT wrapper.

Priority:
1. Import from video_ingestor_summary workspace (reuse existing model instance)
2. Fall back to direct faster-whisper call

Returns a list of segment dicts:
    {"text": str, "start": float, "end": float, "words": list[dict]}
"""
from __future__ import annotations
import pathlib
import sys
from typing import Any


# ---------------------------------------------------------------------------
# Try to reuse video_ingestor_summary workspace
# ---------------------------------------------------------------------------

_VIS_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "video_ingestor_summary" / "workspace"


def _try_import_vis_transcribe():
    """Attempt to import transcribe() from video_ingestor_summary workspace."""
    if _VIS_PATH.exists():
        sys.path.insert(0, str(_VIS_PATH))
        try:
            from video_ingestor_summary import transcribe as _t  # type: ignore
            return _t
        except ImportError:
            pass
        # Also try a flat transcriber module
        try:
            import transcriber as _tr  # type: ignore
            if hasattr(_tr, "transcribe"):
                return _tr.transcribe
        except ImportError:
            pass
    return None


# ---------------------------------------------------------------------------
# Direct faster-whisper fallback
# ---------------------------------------------------------------------------

def _transcribe_direct(video_path: str, language: str | None = None) -> list[dict]:
    """Transcribe using faster-whisper directly."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as e:
        raise ImportError(
            "faster-whisper not installed. Run: pip install faster-whisper"
        ) from e

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        video_path,
        language=language,
        word_timestamps=True,
        beam_size=5,
    )
    result = []
    for seg in segments:
        words = []
        if seg.words:
            words = [
                {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                for w in seg.words
            ]
        result.append({
            "text": seg.text.strip(),
            "start": seg.start,
            "end": seg.end,
            "words": words,
        })
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transcribe(video_path: str, language: str | None = None) -> list[dict[str, Any]]:
    """Transcribe a video file and return a list of segment dicts.

    Args:
        video_path: Path to the video/audio file.
        language:   BCP-47 language code of the source audio (e.g. "en").
                    Pass None for auto-detect.

    Returns:
        List of segments: [{"text": str, "start": float, "end": float, "words": [...]}, ...]
    """
    # Try video_ingestor_summary workspace first
    vis_fn = _try_import_vis_transcribe()
    if vis_fn is not None:
        try:
            result = vis_fn(video_path, language=language)
            # Normalise to expected schema if it differs
            if result and isinstance(result[0], dict):
                for seg in result:
                    seg.setdefault("words", [])
                return result
        except Exception:
            pass  # fall through to direct

    # Direct faster-whisper fallback
    return _transcribe_direct(video_path, language=language)
