"""Mock transcription for environments without Whisper installed."""

import os


def mock_transcribe(audio_path: str, language: str = None) -> dict:
    """Mock transcription that returns synthetic timing data.

    Args:
        audio_path: Path to the audio file.
        language: Language code (ignored in mock).

    Returns:
        Dict with 'text', 'segments', and 'words' keys.
    """
    duration = 0.0
    if os.path.exists(audio_path):
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            audio.close()
        except Exception:
            pass

    mock_text = f"[Mock transcription of {os.path.basename(audio_path)} in {language or 'auto'}]"
    mock_segments = [
        {
            "start": 0.0,
            "end": duration if duration > 0 else 5.0,
            "text": mock_text,
        }
    ]
    mock_words = [
        {"word": word, "start": i * 0.5, "end": (i + 1) * 0.5}
        for i, word in enumerate(mock_text.split())
    ]

    return {
        "text": mock_text,
        "segments": mock_segments,
        "words": mock_words,
    }
