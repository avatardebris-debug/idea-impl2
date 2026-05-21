"""Cluster content gaps into niche profiles using TF-IDF."""

from __future__ import annotations

from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from book_researcher.models import Gap, NicheProfile


def _normalize_text(text: str) -> str:
    """Normalize text for TF-IDF processing."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def cluster_gaps(gaps: List[Gap], min_cluster_size: int = 2) -> List[NicheProfile]:
    """Cluster gaps into niche profiles using TF-IDF and cosine similarity.

    Args:
        gaps: List of Gap objects to cluster.
        min_cluster_size: Minimum number of gaps required to form a valid niche.

    Returns:
        List of NicheProfile objects representing distinct niches.
    """
    if not gaps:
        return []

    # Normalize gap texts for TF-IDF
    normalized_texts = [_normalize_text(gap.text) for gap in gaps]

    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer(max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(normalized_texts)

    # Compute cosine similarity matrix
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # Cluster gaps based on similarity threshold
    threshold = 0.3
    visited = [False] * len(gaps)
    niches: List[NicheProfile] = []

    for i in range(len(gaps)):
        if visited[i]:
            continue

        # Start a new cluster
        cluster = [i]
        visited[i] = True

        for j in range(i + 1, len(gaps)):
            if not visited[j] and similarity_matrix[i][j] >= threshold:
                cluster.append(j)
                visited[j] = True

        # Only create a niche if cluster meets minimum size
        if len(cluster) >= min_cluster_size:
            cluster_gaps = [gaps[idx] for idx in cluster]
            cluster_texts = [_normalize_text(g.text) for g in cluster_gaps]

            # Calculate niche score based on cluster size and average helpful votes
            total_helpful = sum(g.helpful_votes for g in cluster_gaps)
            score = len(cluster_gaps) * 1.5 + total_helpful * 0.1

            # Generate description from cluster topics
            topics = [g.topic for g in cluster_gaps]
            topic_counts = {}
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            dominant_topic = max(topic_counts, key=topic_counts.get)

            niches.append(NicheProfile(
                topic=dominant_topic,
                gaps=cluster_gaps,
                score=score,
                description=f"Underserved area in {dominant_topic} with {len(cluster_gaps)} identified gaps",
            ))

    # Sort niches by score (highest first)
    niches.sort(key=lambda n: n.score, reverse=True)
    return niches
