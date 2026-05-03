"""Text cleaning and deduplication for the Scott Adams corpus.

Provides utilities to:
- Remove boilerplate (ads, navigation, comments, footers)
- Normalize whitespace
- Deduplicate samples by text similarity (hash-based)
"""

import hashlib
import logging
import re
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

# HTML tags to strip from raw content
HTML_TAGS = re.compile(r"<[^>]+>")

# Common boilerplate patterns to remove
BOILERPLATE_PATTERNS = [
    # Navigation / sidebar text
    r"(?:navigation|sidebar|widget|menu|archive|categories|tags|related\s+posts|recent\s+posts|share\s+this|follow\s+me)",
    # Footer text
    r"(?:proudly\s+powered\s+by|wordpress|blog\s+at|rss\s+feed|comments\s+closed|powered\s+by\s+wordpress)",
    # Comment sections
    r"(?:leave\s+a\s+reply|post\s+a\s+comment|comment\s+policy|privacy\s+policy|terms\s+of\s+service)",
    # Ad-related text
    r"(?:advertisement|sponsored\s+content|ad\s+space|buy\s+now|click\s+here\s+to)",
    # Social sharing
    r"(?:share\s+on\s+(?:twitter|facebook|linkedin|email)|follow\s+on\s+(?:twitter|facebook|instagram))",
]

# Stop words for hash-based deduplication (common English words)
STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "it", "its", "this",
    "that", "these", "those", "i", "you", "he", "she", "we", "they", "me",
    "him", "her", "us", "them", "my", "your", "his", "our", "their", "not",
    "no", "nor", "so", "if", "then", "than", "too", "very", "just", "about",
    "above", "after", "again", "all", "also", "am", "any", "as", "because",
    "before", "below", "between", "both", "each", "few", "get", "got", "here",
    "how", "into", "more", "most", "much", "must", "only", "other", "out",
    "over", "own", "same", "some", "such", "there", "through", "under",
    "until", "up", "us", "what", "when", "where", "which", "while", "who",
    "whom", "why", "down", "during", "even", "further", "had", "has", "have",
    "having", "here", "how", "i", "if", "in", "into", "is", "it", "its",
    "just", "me", "might", "more", "most", "must", "my", "no", "nor", "not",
    "now", "of", "off", "on", "once", "only", "or", "other", "our", "out",
    "over", "own", "s", "same", "she", "should", "so", "some", "still", "such",
    "t", "than", "that", "the", "their", "them", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "will", "with", "would", "you", "your",
})


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text: collapse multiple spaces/newlines."""
    # Collapse multiple whitespace chars (including newlines) into single space
    text = re.sub(r"\s+", " ", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    return HTML_TAGS.sub("", text)


def remove_boilerplate(text: str) -> str:
    """Remove common boilerplate patterns from text."""
    result = text
    for pattern in BOILERPLATE_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return result


def clean_text(text: str) -> str:
    """Full text cleaning pipeline.

    Args:
        text: Raw text (possibly with HTML).

    Returns:
        Cleaned text with normalized whitespace.
    """
    if not text:
        return ""

    # Remove HTML tags if present
    text = remove_html_tags(text)

    # Remove boilerplate
    text = remove_boilerplate(text)

    # Normalize whitespace
    text = normalize_whitespace(text)

    return text


def text_hash(text: str, ngram_size: int = 5) -> str:
    """Compute a hash of the text using n-gram based fingerprinting.

    Uses a set of n-grams (with stop words removed) to create a robust
    fingerprint that tolerates minor wording differences.

    Args:
        text: The text to fingerprint.
        ngram_size: Size of n-grams to use.

    Returns:
        Hex digest string.
    """
    words = text.lower().split()
    # Filter out stop words for more robust dedup
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    if not filtered:
        return hashlib.md5(text.lower().encode()).hexdigest()

    ngrams = set()
    for i in range(len(filtered) - ngram_size + 1):
        ngram = " ".join(filtered[i:i + ngram_size])
        ngrams.add(ngram)

    return hashlib.md5("|".join(sorted(ngrams)).encode()).hexdigest()


def deduplicate_samples(
    samples: List[Dict],
    similarity_threshold: float = 0.85,
) -> List[Dict]:
    """Deduplicate a list of corpus samples by text similarity.

    Uses hash-based n-gram comparison to identify near-duplicates.
    Samples with similarity >= threshold are considered duplicates;
    the first occurrence is kept.

    Args:
        samples: List of sample dicts (must have 'text' key).
        similarity_threshold: Minimum similarity to consider a duplicate.

    Returns:
        Deduplicated list of samples.
    """
    if not samples:
        return []

    # Pre-compute hashes
    hashes = []
    for sample in samples:
        h = text_hash(sample.get("text", ""))
        hashes.append(h)

    # Group by exact hash first (exact duplicates)
    seen_hashes: Dict[str, int] = {}  # hash -> index of first occurrence
    unique_indices: List[int] = []
    duplicate_count = 0

    for i, h in enumerate(hashes):
        if h in seen_hashes:
            # Exact duplicate — check similarity for near-duplicates
            first_idx = seen_hashes[h]
            sim = _jaccard_similarity(samples[i]["text"], samples[first_idx]["text"])
            if sim >= similarity_threshold:
                duplicate_count += 1
                continue
            # Near-duplicate — keep both but note it
        else:
            seen_hashes[h] = i

        unique_indices.append(i)

    if duplicate_count > 0:
        logger.info(f"Deduplication removed {duplicate_count} duplicate samples")

    return [samples[i] for i in unique_indices]


def _jaccard_similarity(text1: str, text2: str, ngram_size: int = 3) -> float:
    """Compute Jaccard similarity between two texts using n-grams."""
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def clean_corpus(
    samples: List[Dict],
    deduplicate: bool = True,
    min_text_length: int = 50,
) -> List[Dict]:
    """Full corpus cleaning pipeline.

    Args:
        samples: List of raw sample dicts.
        deduplicate: Whether to deduplicate samples.
        min_text_length: Minimum text length to keep a sample.

    Returns:
        Cleaned and optionally deduplicated list of samples.
    """
    logger.info(f"Cleaning {len(samples)} samples...")

    cleaned = []
    for sample in samples:
        text = sample.get("text", "")
        cleaned_text = clean_text(text)

        if len(cleaned_text) < min_text_length:
            logger.debug(f"Skipping sample {sample.get('id', '?')}: text too short ({len(cleaned_text)} chars)")
            continue

        sample["text"] = cleaned_text
        cleaned.append(sample)

    logger.info(f"After cleaning: {len(cleaned)} samples (removed {len(samples) - len(cleaned)} short/empty)")

    if deduplicate:
        cleaned = deduplicate_samples(cleaned)
        logger.info(f"After deduplication: {len(cleaned)} samples")

    return cleaned


def filter_by_length(
    samples: List[Dict],
    min_length: int = 50,
) -> List[Dict]:
    """Filter samples by minimum text length.

    Args:
        samples: List of sample dicts (must have 'text' key).
        min_length: Minimum text length to keep a sample.

    Returns:
        Filtered list of samples with text >= min_length.
    """
    return [s for s in samples if len(s.get("text", "")) >= min_length]


def filter_by_source(
    samples: List[Dict],
    allowed_sources: List[str],
) -> List[Dict]:
    """Filter samples by source type.

    Args:
        samples: List of sample dicts (must have 'source_type' key).
        allowed_sources: List of allowed source_type values.

    Returns:
        Filtered list of samples with source_type in allowed_sources.
    """
    return [s for s in samples if s.get("source_type") in allowed_sources]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Demo: clean a sample text
    raw = """
        <div class="article-body">
            <h1>Test Article</h1>
            <p>Most people think success is about talent. Actually, it's about systems.</p>
            <p>Here's what nobody tells you: small daily improvements lead to massive results.</p>
        </div>
        <div class="sidebar">Related Posts | Follow Me | Share This</div>
        <footer>Proudly powered by WordPress</footer>
    """

    cleaned = clean_text(raw)
    print(f"Cleaned text:\n{cleaned}\n")
    print(f"Length: {len(cleaned)} chars")

    # Demo: deduplication
    samples = [
        {"id": "1", "text": "Most people think success is about talent. Actually, it's about systems."},
        {"id": "2", "text": "Most people think success is about talent. Actually, it's about systems."},
        {"id": "3", "text": "Most people think success is about talent. Actually, it's about systems. And persistence."},
        {"id": "4", "text": "The key to success is building systems that work for you."},
    ]
    deduped = deduplicate_samples(samples)
    print(f"\nDeduplication: {len(samples)} -> {len(deduped)} samples")
    for s in deduped:
        print(f"  {s['id']}: {s['text'][:50]}...")
