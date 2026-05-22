"""Course comparison and recommendation engine."""

from __future__ import annotations

from typing import Dict, List, Optional

from udemy_training_tool.models import Course


def recommend_courses(
    courses: List[Course],
    target_skill: str,
    top_n: int = 5,
) -> List[Dict]:
    """Score and rank courses for a given target skill/topic.

    Composite score (0-100) based on:
      - Rating:        30% weight (scale 0-5)
      - Student count: 25% weight (normalized via min-max)
      - Price value:   20% weight (lower price = higher score)
      - Course depth:  15% weight (lecture count)
      - Instructor:    10% weight (name length proxy)

    Args:
        courses: List of courses to evaluate.
        target_skill: Skill/topic to match courses against.
        top_n: Number of top results to return.

    Returns:
        List of dicts with course, score, and breakdown.
    """
    if not courses:
        return []

    scored = [_score_course(course, target_skill) for course in courses]

    # Sort by score descending, then by rating (desc), then by price (asc)
    scored.sort(key=lambda x: (-x["score"], -x["breakdown"]["rating"], x["course"].price))

    return scored[:top_n]


def compare_courses(
    courses: List[Course],
    target_skill: Optional[str] = None,
) -> List[Dict]:
    """Score and rank all courses without filtering by skill.

    Args:
        courses: List of courses to evaluate.
        target_skill: Optional skill to match (for display purposes).

    Returns:
        List of dicts with course, score, and breakdown.
    """
    if not courses:
        return []

    scored = [_score_course(course, target_skill or "") for course in courses]

    # Sort by score descending, then by rating (desc), then by price (asc)
    scored.sort(key=lambda x: (-x["score"], -x["breakdown"]["rating"], x["course"].price))

    return scored


def _score_course(course: Course, target_skill: str = "") -> Dict:
    """Score a single course and return detailed breakdown.

    Args:
        course: Course to score.
        target_skill: Optional skill/topic to match.

    Returns:
        Dict with course, score, and breakdown.
    """
    skill_match = _skill_match(course, target_skill)

    # Calculate component scores
    rating_score = course.rating / 5.0 * 100.0
    students_score = _normalize_student_count(course.num_students)
    price_score = _normalize_price(course.price)
    depth_score = _normalize_lectures(course.num_lectures)
    instructor_score = _score_instructor(course.instructor)

    # Weighted composite score
    score = (
        rating_score * 0.30 +
        students_score * 0.25 +
        price_score * 0.20 +
        depth_score * 0.15 +
        instructor_score * 0.10
    )

    return {
        "course": course,
        "score": round(score, 2),
        "breakdown": {
            "rating": round(rating_score, 2),
            "students": round(students_score, 2),
            "price_value": round(price_score, 2),
            "depth": round(depth_score, 2),
            "instructor": round(instructor_score, 2),
            "skill_match": skill_match,
        },
    }


def _skill_match(course: Course, target_skill: str) -> bool:
    """Check if course matches the target skill/topic."""
    if not target_skill:
        return True

    target_lower = target_skill.lower()

    # Check title
    if target_lower in course.title.lower():
        return True

    # Check description
    if target_lower in course.description.lower():
        return True

    # Check tags
    for tag in course.tags:
        if target_lower in tag.lower():
            return True

    # Check category
    if target_lower in course.category.lower():
        return True

    return False


def _normalize_student_count(num_students: int) -> float:
    """Normalize student count to 0-100 scale.

    Uses min-max normalization with:
      - min = 0 (imputed for 0 or negative)
      - max = 150,000 (capped)

    Returns:
        Normalized score between 0 and 100.
    """
    if num_students <= 0:
        # Median imputation for missing values
        return 50.0

    # Cap at max
    capped = min(num_students, 150_000)

    # Min-max normalization
    score = (capped / 150_000) * 100.0
    return min(100.0, max(0.0, score))


def _normalize_price(price: float) -> float:
    """Normalize price to 0-100 scale (lower price = higher score).

    Uses min-max normalization with:
      - min = 0 (free courses get max score)
      - max = 200 (capped)

    Returns:
        Normalized score between 0 and 100.
    """
    if price <= 0:
        return 100.0

    # Cap at max
    capped = min(price, 200.0)

    # Inverted min-max normalization
    score = 100.0 - (capped / 200.0) * 100.0
    return min(100.0, max(0.0, score))


def _normalize_lectures(num_lectures: int) -> float:
    """Normalize lecture count to 0-100 scale.

    Uses min-max normalization with:
      - min = 0 (imputed for 0 or negative)
      - max = 300 (capped)

    Returns:
        Normalized score between 0 and 100.
    """
    if num_lectures <= 0:
        # Median imputation for missing values
        return 50.0

    # Cap at max
    capped = min(num_lectures, 300)

    # Min-max normalization
    score = (capped / 300) * 100.0
    return min(100.0, max(0.0, score))


def _score_instructor(instructor: str) -> float:
    """Score instructor based on name length (proxy for experience).

    Uses min-max normalization with:
      - min = 0 (empty/whitespace)
      - max = 15 characters (capped)

    Returns:
        Normalized score between 0 and 100.
    """
    if not instructor or not instructor.strip():
        # Median imputation for missing values
        return 50.0

    name_length = len(instructor.strip())

    # Cap at max
    capped = min(name_length, 15)

    # Min-max normalization
    score = (capped / 15) * 100.0
    return min(100.0, max(0.0, score))
