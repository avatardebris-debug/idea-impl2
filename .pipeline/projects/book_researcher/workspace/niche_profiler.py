"""Niche profiler that clusters gaps into marketable niche profiles."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List

from book_researcher.models import Gap, NicheProfile

logger = logging.getLogger(__name__)


def _cluster_gaps_by_topic(gaps: list[Gap], similarity_threshold: float = 0.5) -> list[list[Gap]]:
    """Cluster gaps by topic using simple keyword overlap.

    Groups gaps that share the same topic label together.
    """
    if not gaps:
        return []

    topic_groups: dict[str, list[Gap]] = defaultdict(list)
    for gap in gaps:
        topic_groups[gap.topic].append(gap)

    return list(topic_groups.values())


def profile_niches(gaps: list[Gap], min_gap_count: int = 1) -> list[NicheProfile]:
    """Profile niches from a list of gaps.

    Args:
        gaps: List of Gap objects to cluster.
        min_gap_count: Minimum number of gaps for a niche to be included.

    Returns:
        List of NicheProfile objects sorted by score descending.
    """
    if not gaps:
        logger.warning("No gaps provided to profile_niches")
        return []

    topic_groups = _cluster_gaps_by_topic(gaps)

    niches: list[NicheProfile] = []
    for topic, topic_gaps in topic_groups:
        if len(topic_gaps) < min_gap_count:
            continue

        # Score = number of gaps * average helpfulness heuristic
        score = len(topic_gaps) * 10  # Simple scoring heuristic

        niche = NicheProfile(
            topic=topic,
            gap_count=len(topic_gaps),
            score=score,
            sample_gaps=[g.text for g in topic_gaps[:3]],
            all_gaps=[g.text for g in topic_gaps],
        )
        niches.append(niche)

    # Sort by score descending
    niches.sort(key=lambda n: n.score, reverse=True)

    logger.info("Profiled %d niches from %d gaps", len(niches), len(gaps))
    return niches
