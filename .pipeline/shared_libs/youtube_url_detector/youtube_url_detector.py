"""YouTube URL detector — checks if a string is a YouTube URL."""

import urllib.parse


def is_youtube_url(url: str) -> bool:
    """Check if a string is a YouTube URL.

    Args:
        url: The URL string to check.

    Returns:
        True if the URL is a YouTube URL, False otherwise.
    """
    youtube_domains = [
        "youtube.com", "www.youtube.com", "youtu.be",
        "www.youtu.be", "youtube-nocookie.com",
    ]
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc in youtube_domains
