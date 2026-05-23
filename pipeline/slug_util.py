import re


def slugify_title(title: str) -> str:
    """Convert an idea title to a filesystem-safe slug.
    'CSV Analyzer' -> 'csv_analyzer', '[Youtube studio]' -> 'youtube_studio'
    """
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '_', slug)
    return slug.strip('_') or "unknown"

