"""Audiobook metadata extractor for m4b/mp4 Amazon audiobook files."""

import io
from mutagen.mp4 import MP4


class AudiobookError(Exception):
    """Base exception for audiobook2pdf errors."""


class MetadataExtractError(AudiobookError):
    """Raised when metadata extraction fails."""


def extract_metadata(file_path: str) -> dict:
    """Extract metadata from an m4b/mp4 audiobook file.

    Args:
        file_path: Path to the audiobook file.

    Returns:
        Dict with keys: title, author, narrator, cover_art_bytes, chapters, duration.

    Raises:
        MetadataExtractError: If the file cannot be read or parsed.
    """
    if not file_path:
        raise MetadataExtractError("file_path cannot be empty")

    try:
        audio = MP4(file_path)
    except Exception as e:
        raise MetadataExtractError(f"Failed to read audiobook file '{file_path}': {e}")

    # Extract title
    title = ""
    if audio.get("\xa9nam") is not None and len(audio["\xa9nam"]) > 0:
        title = str(audio["\xa9nam"][0])

    # Extract artist (author)
    author = ""
    if audio.get("\xa9ART") is not None and len(audio["\xa9ART"]) > 0:
        author = str(audio["\xa9ART"][0])

    # Extract performer (narrator)
    narrator = ""
    if audio.get("prf") is not None and len(audio["prf"]) > 0:
        narrator = str(audio["prf"][0])

    # Extract cover art
    cover_art_bytes = None
    if audio.get("covr") is not None and len(audio["covr"]) > 0:
        cover_art_bytes = audio["covr"][0].get_data()

    # Extract duration (in milliseconds)
    duration = 0
    if audio.get("\xa9day") is not None:
        # Try to get duration from length property
        pass
    if hasattr(audio, "info") and audio.info is not None:
        duration = int(audio.info.length * 1000)

    # Extract chapters
    chapters = []
    if audio.get("trkn") is not None:
        # Some files store chapter info in custom atoms
        pass
    # Check for chapter metadata in common MP4 atoms
    for key in ["----:com.apple:itunes:chapter"]:
        if audio.get(key) is not None:
            pass

    return {
        "title": title,
        "author": author,
        "narrator": narrator,
        "cover_art_bytes": cover_art_bytes,
        "chapters": chapters,
        "duration": duration,
    }
