"""
transcriber.py — Audio/video → transcript text.

Priority:
1. Reuse video_babbel_enhanced workspace transcriber (shares faster-whisper model)
2. Reuse video_ingestor_summary workspace transcriber
3. Direct faster-whisper call as last resort

Returns full transcript as a single string (joined segments).
Also exposes get_segments() for time-stamped output.
"""
from __future__ import annotations
import pathlib
import sys
from typing import Any

# Sibling workspace paths
_VBE_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "video_babbel_enhanced" / "workspace"
_VIS_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "video_ingestor_summary" / "workspace"


def _try_workspace_transcribe(ws_path: pathlib.Path):
    """Try to import transcribe() from a sibling workspace."""
    if ws_path.exists():
        sys.path.insert(0, str(ws_path))
        for mod_name in ["video_babbel_enhanced.transcriber", "transcriber"]:
            try:
                import importlib
                mod = importlib.import_module(mod_name)
                if hasattr(mod, "transcribe"):
                    return mod.transcribe
            except ImportError:
                pass
    return None


def _direct_transcribe(audio_path: str, language: str | None = None) -> list[dict[str, Any]]:
    """Direct faster-whisper fallback."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        raise ImportError("pip install faster-whisper")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, language=language, word_timestamps=False)
    return [{"text": s.text.strip(), "start": s.start, "end": s.end} for s in segments]


def get_segments(audio_path: str, language: str | None = None) -> list[dict[str, Any]]:
    """Return list of {text, start, end} segment dicts."""
    for ws in [_VBE_PATH, _VIS_PATH]:
        fn = _try_workspace_transcribe(ws)
        if fn:
            try:
                result = fn(audio_path, language=language)
                if result:
                    for s in result:
                        s.setdefault("words", [])
                    return result
            except Exception:
                pass
    return _direct_transcribe(audio_path, language)


def transcribe(audio_path: str, language: str | None = None) -> str:
    """Return the full transcript as a single string."""
    segments = get_segments(audio_path, language)
    return " ".join(s.get("text", "").strip() for s in segments if s.get("text", "").strip())
