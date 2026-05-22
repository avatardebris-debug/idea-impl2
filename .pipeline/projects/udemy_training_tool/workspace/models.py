"""Core data models for Udemy courses and learning paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Lesson:
    """A single lesson within a module."""
    title: str = ""
    duration: str = ""  # e.g., "10:30"
    lesson_type: str = "video"  # video, quiz, article, practice

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "duration": self.duration,
            "type": self.lesson_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Lesson:
        return cls(
            title=data.get("title", ""),
            duration=data.get("duration", ""),
            lesson_type=data.get("type", "video"),
        )


@dataclass
class Module:
    """A module containing lessons."""
    title: str = ""
    order: int = 0
    num_lectures: int = 0
    lessons: List[Lesson] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "order": self.order,
            "num_lectures": self.num_lectures,
            "lessons": [l.to_dict() for l in self.lessons],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Module:
        lessons = [Lesson.from_dict(l) for l in data.get("lessons", [])]
        return cls(
            title=data.get("title", ""),
            order=data.get("order", 0),
            num_lectures=data.get("num_lectures", len(lessons)),
            lessons=lessons,
        )


@dataclass
class Course:
    """A Udemy course."""
    title: str = ""
    instructor: str = ""
    rating: float = 0.0
    num_students: int = 0
    price: float = 0.0
    level: str = "All Levels"
    category: str = ""
    tags: List[str] = field(default_factory=list)
    duration: str = ""
    num_lectures: int = 0
    description: str = ""
    language: str = "English"
    modules: List[Module] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "instructor": self.instructor,
            "rating": self.rating,
            "num_students": self.num_students,
            "price": self.price,
            "level": self.level,
            "category": self.category,
            "tags": self.tags,
            "duration": self.duration,
            "num_lectures": self.num_lectures,
            "description": self.description,
            "language": self.language,
            "modules": [m.to_dict() for m in self.modules],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Course:
        modules = [Module.from_dict(m) for m in data.get("modules", [])]
        return cls(
            title=data.get("title", ""),
            instructor=data.get("instructor", ""),
            rating=data.get("rating", 0.0),
            num_students=data.get("num_students", 0),
            price=data.get("price", 0.0),
            level=data.get("level", "All Levels"),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            duration=data.get("duration", ""),
            num_lectures=data.get("num_lectures", 0),
            description=data.get("description", ""),
            language=data.get("language", "English"),
            modules=modules,
        )

    def validate(self) -> None:
        """Validate required fields. Raises ValueError on missing fields."""
        missing = []
        if not self.title:
            missing.append("title")
        if not self.instructor:
            missing.append("instructor")
        if self.rating <= 0:
            missing.append("rating")
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    def matches_query(self, query: str) -> bool:
        """Check if course matches the search query (case-insensitive, partial word)."""
        if not query:
            return True
        query_lower = query.lower()
        query_words = query_lower.split()

        searchable = " ".join([
            self.title,
            self.description,
            self.instructor,
            " ".join(self.tags),
        ]).lower()

        return all(word in searchable for word in query_words)

    def matches_filters(
        self,
        min_rating: float = 0,
        max_price: Optional[float] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
    ) -> bool:
        """Check if course matches all filter criteria."""
        if min_rating is not None and self.rating < min_rating:
            return False
        if max_price is not None and self.price > max_price:
            return False
        if level is not None and self.level.lower() != level.lower():
            return False
        if category is not None and self.category.lower() != category.lower():
            return False
        return True


@dataclass
class LearningPath:
    """A curated learning path of courses."""
    title: str = ""
    courses: List[Course] = field(default_factory=list)
    target_skill: str = ""
    estimated_hours: float = 0.0
    difficulty: str = "Beginner"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "courses": [c.to_dict() for c in self.courses],
            "target_skill": self.target_skill,
            "estimated_hours": self.estimated_hours,
            "difficulty": self.difficulty,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LearningPath:
        courses = [Course.from_dict(c) for c in data.get("courses", [])]
        return cls(
            title=data.get("title", ""),
            courses=courses,
            target_skill=data.get("target_skill", ""),
            estimated_hours=data.get("estimated_hours", 0.0),
            difficulty=data.get("difficulty", "Beginner"),
        )

    def compute_estimated_hours(self) -> float:
        """Sum course durations to compute estimated hours."""
        total = 0.0
        for course in self.courses:
            hours = self._parse_duration(course.duration)
            total += hours
        self.estimated_hours = total
        return total

    @staticmethod
    def _parse_duration(duration_str: str) -> float:
        """Parse a duration string like '22.5 hours' or '120 hours' into hours."""
        if not duration_str:
            return 0.0
        duration_str = duration_str.lower().strip()
        if "hour" in duration_str:
            try:
                return float(duration_str.split()[0])
            except (IndexError, ValueError):
                return 0.0
        elif "minute" in duration_str:
            try:
                return float(duration_str.split()[0]) / 60.0
            except (IndexError, ValueError):
                return 0.0
        return 0.0
