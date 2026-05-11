"""Curated English stop-word set for keyword extraction.

Used to filter out common words when generating SEO keywords,
NLP features, or text classification features.
"""

STOP_WORDS: set[str] = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can",
    "this", "that", "these", "those", "it", "its", "not", "no",
    "as", "if", "so", "than", "too", "very", "just", "about",
    "also", "from", "into", "over", "after",
}
