"""udemy_training_tool — Search, compare, and recommend Udemy courses."""

from udemy_training_tool.models import Course, LearningPath, Module, Lesson
from udemy_training_tool.search import search_courses
from udemy_training_tool.recommender import recommend_courses

__version__ = "0.1.0"

__all__ = [
    "Course",
    "LearningPath",
    "Module",
    "Lesson",
    "search_courses",
    "recommend_courses",
]
