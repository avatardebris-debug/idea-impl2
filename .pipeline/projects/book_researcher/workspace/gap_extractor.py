"""Gap extraction engine with keyword matching and TF-IDF clustering."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from book_researcher.models import Gap


class GapExtractor:
    """Extracts and clusters content gaps from reviews.

    Uses:
    1. Keyword/phrase matching for initial gap detection
    2. TF-IDF clustering for grouping similar gaps
    """

    def __init__(self, min_gap_score: float = 0.3):
        self.min_gap_score = min_gap_score
        self.stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "s", "t", "just", "don",
            "now", "i", "me", "my", "myself", "we", "our", "ours", "you",
            "your", "yours", "he", "him", "his", "she", "her", "it", "its",
            "they", "them", "their", "what", "which", "who", "whom", "this",
            "that", "these", "those", "am", "but", "if", "or", "because",
            "until", "while", "about", "against", "between", "into", "through",
            "during", "before", "after", "above", "below", "up", "down", "out",
            "off", "over", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "any", "both",
            "each", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        }

    def extract_gaps(self, reviews: List[dict]) -> List[Gap]:
        """Extract gaps from reviews."""
        gaps = []
        gap_indicators = [
            "wish", "wanted", "missing", "didn't", "did not",
            "forgot", "lacked", "hope", "expected", "should have",
            "need to know", "confusing", "unclear", "not covered",
            "didn't cover", "didn't explain", "didn't mention",
            "didn't include", "didn't discuss", "lacking", "unclear",
            "incomplete", "insufficient", "outdated", "superficial",
        ]

        for review in reviews:
            text = review.get("text", "").lower()
            rating = review.get("rating", 3)

            # Only extract gaps from reviews that express dissatisfaction
            if rating >= 4:
                continue

            for indicator in gap_indicators:
                if indicator in text:
                    gap_text = self._extract_gap_text(text, indicator)
                    if gap_text:
                        gap = Gap(
                            text=gap_text,
                            topic=review.get("topic", "general"),
                            source=review.get("source", "unknown"),
                            helpful_votes=review.get("helpful_votes", 0),
                            confidence=self._calculate_confidence(gap_text, rating),
                        )
                        gaps.append(gap)
                    break  # One gap per review is enough for MVP

        return gaps

    def cluster_gaps(self, gaps: List[Gap], threshold: float = 0.6) -> List[List[Gap]]:
        """Cluster similar gaps using TF-IDF and cosine similarity."""
        if not gaps:
            return []

        # Build vocabulary and document frequency
        vocabulary = set()
        doc_freq = defaultdict(int)

        for gap in gaps:
            words = self._tokenize(gap.text)
            vocabulary.update(words)
            for word in words:
                doc_freq[word] += 1

        # Calculate IDF
        n_docs = len(gaps)
        idf = {}
        for word in vocabulary:
            idf[word] = math.log(n_docs / (1 + doc_freq[word]))

        # Calculate TF-IDF vectors
        tfidf_vectors = {}
        for i, gap in enumerate(gaps):
            words = self._tokenize(gap.text)
            tf = defaultdict(int)
            for word in words:
                tf[word] += 1
            # Normalize TF
            total = len(words) if words else 1
            tfidf = {}
            for word, count in tf.items():
                tfidf[word] = (count / total) * idf.get(word, 0)
            tfidf_vectors[i] = tfidf

        # Calculate cosine similarities
        clusters = []
        assigned = set()

        for i in range(len(gaps)):
            if i in assigned:
                continue

            cluster = [gaps[i]]
            assigned.add(i)

            for j in range(i + 1, len(gaps)):
                if j in assigned:
                    continue

                similarity = self._cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
                if similarity >= threshold:
                    cluster.append(gaps[j])
                    assigned.add(j)

            clusters.append(cluster)

        return clusters

    def prioritize_gaps(self, gaps: List[Gap]) -> List[Gap]:
        """Prioritize gaps by score (confidence * helpful_votes)."""
        for gap in gaps:
            gap.score = gap.confidence * (1 + math.log1p(gap.helpful_votes))

        return sorted(gaps, key=lambda g: g.score, reverse=True)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words, removing stop words."""
        words = text.lower().split()
        # Remove punctuation
        words = [w.strip(".,!?;:'\"()[]{}") for w in words]
        # Remove stop words and short words
        words = [w for w in words if w not in self.stop_words and len(w) > 2]
        return words

    def _extract_gap_text(self, text: str, indicator: str) -> Optional[str]:
        """Extract the gap description from review text."""
        sentences = text.split(".")
        for sentence in sentences:
            if indicator in sentence:
                gap = sentence.strip().capitalize()
                if len(gap) > 10:  # Filter out very short gaps
                    return gap
        return None

    def _calculate_confidence(self, gap_text: str, rating: int) -> float:
        """Calculate confidence score for a gap."""
        base_confidence = 0.5
        rating_factor = (5 - rating) / 4.0
        length_factor = min(len(gap_text) / 100.0, 1.0)
        return min(base_confidence + rating_factor * 0.3 + length_factor * 0.2, 1.0)

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two TF-IDF vectors."""
        # Get common words
        common_words = set(vec1.keys()) & set(vec2.keys())
        if not common_words:
            return 0.0

        # Calculate dot product
        dot_product = sum(vec1[w] * vec2[w] for w in common_words)

        # Calculate magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)
