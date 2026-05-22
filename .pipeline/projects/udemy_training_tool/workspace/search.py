"""Course search and filtering engine."""

from __future__ import annotations

from typing import List, Optional

from udemy_training_tool.models import Course


def search_courses(
    courses: List[Course],
    query: str = "",
    min_rating: float = 0,
    max_price: Optional[float] = None,
    level: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Course]:
    """Search and filter a list of courses by various criteria.

    Args:
        courses: List of Course objects to search.
        query: Search query — matches against title, description, tags, instructor.
               Case-insensitive, partial word matching.
        min_rating: Minimum rating filter (0-5).
        max_price: Maximum price filter (None = no limit).
        level: Course level filter (e.g., "All Levels", "Beginner", "Intermediate", "Advanced").
        category: Category filter.

    Returns:
        List of matching Course objects. Empty list if no courses match.
        Filters are combined with AND logic.
    """
    if not courses:
        return []

    results: List[Course] = []
    for course in courses:
        # Query matching
        if query and not course.matches_query(query):
            continue

        # Filter matching
        if not course.matches_filters(
            min_rating=min_rating if min_rating is not None else 0,
            max_price=max_price,
            level=level,
            category=category,
        ):
            continue

        results.append(course)

    return results
