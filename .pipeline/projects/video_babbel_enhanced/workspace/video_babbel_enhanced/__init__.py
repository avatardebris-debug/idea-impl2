"""
video_babbel_enhanced
Frequency-ordered language learning from video using comprehensible input.

Pipeline: video → Whisper STT → LLM translate → SUBTLEX-US frequency score → ffmpeg clip extract
"""
__version__ = "0.1.0"
__all__ = ["transcriber", "translator", "frequency_scorer", "clip_extractor", "cli"]
