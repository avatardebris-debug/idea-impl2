"""Udemy Training Tool - Course recommendation, progress tracking, and adaptive learning."""

__version__ = "0.1.0"

from udemy_training_tool.adaptive_sequencer import (
    AdaptiveSequencer,
    PerformanceLevel,
    SequenceStrategy,
    PerformanceMetrics,
    SequenceRecommendation,
    LearningSequence,
)
from udemy_training_tool.course_manager import CourseManager
from udemy_training_tool.progress_tracker import ProgressTracker
from udemy_training_tool.recommendation_engine import RecommendationEngine
from udemy_training_tool.cli import main

__all__ = [
    "AdaptiveSequencer",
    "PerformanceLevel",
    "SequenceStrategy",
    "PerformanceMetrics",
    "SequenceRecommendation",
    "LearningSequence",
    "CourseManager",
    "ProgressTracker",
    "RecommendationEngine",
    "main",
]
