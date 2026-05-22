"""
podcast — Extract lessons from podcast episodes.

Pipeline:
    audio/video → FastWhisper transcript → LLM lesson extractor → structured JSON

Output per episode:
    {
      "episode":   "file or title",
      "lessons":   [{"number": 1, "title": str, "detail": str, "quote": str}],
      "summary":   str,
      "metadata":  {"model": str, "n_lessons": int, "transcript_length": int, ...}
    }

Usage:
    python -m podcast episode.mp3 --lessons 10 --output lessons.json
    python -m podcast episode.mp3 --prompt "Focus on business tactics"
    python -m podcast transcript.txt --text-input --lessons 5
"""
__version__ = "0.1.0"
