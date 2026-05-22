"""Adaptive Sequencer - Adjusts learning sequence based on performance and feedback."""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import yaml


class PerformanceLevel(Enum):
    """Performance level classifications."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    NEEDS_IMPROVEMENT = "needs_improvement"
    STRUGGLING = "struggling"


class SequenceStrategy(Enum):
    """Strategies for sequencing learning content."""
    PROGRESSIVE = "progressive"
    SPIRAL = "spiral"
    INTERLEAVED = "interleaved"
    MASTERY_BASED = "mastery_based"
    ADAPTIVE = "adaptive"
    RANDOM = "random"


@dataclass
class PerformanceMetrics:
    """Tracks performance metrics for a concept."""
    concept_id: str
    total_attempts: int = 0
    successful_attempts: int = 0
    average_score: float = 0.0
    time_spent_minutes: float = 0.0
    last_attempt_date: Optional[datetime] = None
    performance_trend: List[float] = field(default_factory=list)
    difficulty_rating: float = 0.0  # User-rated difficulty 0-10
    performance_level: Optional[str] = None  # Computed performance level

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "concept_id": self.concept_id,
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "average_score": self.average_score,
            "time_spent_minutes": self.time_spent_minutes,
            "last_attempt_date": self.last_attempt_date.isoformat() if self.last_attempt_date else None,
            "performance_trend": self.performance_trend,
            "difficulty_rating": self.difficulty_rating
        }


@dataclass
class SequenceRecommendation:
    """Represents a sequencing recommendation."""
    recommendation_id: str
    concept_id: str
    concept_name: str
    recommended_action: str
    priority: float  # 0-10
    reasoning: str
    confidence_score: float  # 0-10
    suggested_duration_minutes: int
    optimal_time_of_day: str
    created_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendation_id": self.recommendation_id,
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "recommended_action": self.recommended_action,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "confidence_score": self.confidence_score,
            "suggested_duration_minutes": self.suggested_duration_minutes,
            "optimal_time_of_day": self.optimal_time_of_day,
            "created_date": self.created_date.isoformat()
        }


@dataclass
class LearningSequence:
    """Represents a complete learning sequence."""
    sequence_id: str
    topic_name: str
    concepts: List[str]
    sequence_type: str
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "active"
    current_position: int = 0
    completion_percentage: float = 0.0
    created_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "sequence_id": self.sequence_id,
            "topic_name": self.topic_name,
            "concepts": self.concepts,
            "sequence_type": self.sequence_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "current_position": self.current_position,
            "completion_percentage": self.completion_percentage,
            "created_date": self.created_date.isoformat()
        }


class AdaptiveSequencer:
    """
    Implements adaptive learning sequencing.
    
    Provides functionality to:
    - Track performance metrics
    - Generate personalized learning sequences
    - Adjust sequence based on performance
    - Recommend optimal learning times
    - Analyze learning patterns
    """
    
    def __init__(self, config_path: Optional[str] = None, data_dir: Optional[str] = None):
        """
        Initialize the adaptive sequencer.
        
        Args:
            config_path: Path to sequencer configuration file.
            data_dir: Directory for storing sequencer data.
        """
        self.config = self._load_config(config_path)
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.recommendations: List[SequenceRecommendation] = []
        self.sequences: List[LearningSequence] = []
        self.data_dir = Path(data_dir) if data_dir else Path("data/sequencer")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load sequencer configuration."""
        default_config = {
            "auto_save": True,
            "performance_thresholds": {
                "excellent": 90.0,
                "good": 75.0,
                "average": 60.0,
                "needs_improvement": 40.0
            },
            "default_sequence_type": "adaptive",
            "max_recommendations": 10,
            "confidence_threshold": 0.7,
            "trend_window": 5,
            "optimal_study_times": ["morning", "afternoon", "evening"]
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config:
                    default_config.update(loaded_config)
        
        return default_config
    
    def _load_data(self):
        """Load existing sequencer data from files."""
        # Load performance metrics
        metrics_file = self.data_dir / "performance_metrics.json"
        if metrics_file.exists():
            with open(metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("metrics", []):
                    last_attempt_date = datetime.fromisoformat(item["last_attempt_date"]) if item.get("last_attempt_date") else None
                    metrics = PerformanceMetrics(
                        concept_id=item["concept_id"],
                        total_attempts=item["total_attempts"],
                        successful_attempts=item["successful_attempts"],
                        average_score=item["average_score"],
                        time_spent_minutes=item["time_spent_minutes"],
                        last_attempt_date=last_attempt_date,
                        performance_trend=item["performance_trend"],
                        difficulty_rating=item["difficulty_rating"]
                    )
                    self.performance_metrics[item["concept_id"]] = metrics
        
        # Load recommendations
        recommendations_file = self.data_dir / "recommendations.json"
        if recommendations_file.exists():
            with open(recommendations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("recommendations", []):
                    created_date = datetime.fromisoformat(item["created_date"])
                    recommendation = SequenceRecommendation(
                        recommendation_id=item["recommendation_id"],
                        concept_id=item["concept_id"],
                        concept_name=item["concept_name"],
                        recommended_action=item["recommended_action"],
                        priority=item["priority"],
                        reasoning=item["reasoning"],
                        confidence_score=item["confidence_score"],
                        suggested_duration_minutes=item["suggested_duration_minutes"],
                        optimal_time_of_day=item["optimal_time_of_day"],
                        created_date=created_date
                    )
                    self.recommendations.append(recommendation)
        
        # Load sequences
        sequences_file = self.data_dir / "sequences.json"
        if sequences_file.exists():
            with open(sequences_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("sequences", []):
                    start_date = datetime.fromisoformat(item["start_date"])
                    end_date = datetime.fromisoformat(item["end_date"]) if item.get("end_date") else None
                    sequence = LearningSequence(
                        sequence_id=item["sequence_id"],
                        topic_name=item["topic_name"],
                        concepts=item["concepts"],
                        sequence_type=item["sequence_type"],
                        start_date=start_date,
                        end_date=end_date,
                        status=item["status"],
                        current_position=item["current_position"],
                        completion_percentage=item["completion_percentage"],
                        created_date=datetime.fromisoformat(item["created_date"])
                    )
                    self.sequences.append(sequence)
    
    def save_data(self):
        """Save all sequencer data to files."""
        # Save performance metrics
        with open(self.data_dir / "performance_metrics.json", 'w', encoding='utf-8') as f:
            json.dump({
                "metrics": [m.to_dict() for m in self.performance_metrics.values()]
            }, f, indent=2)
        
        # Save recommendations
        with open(self.data_dir / "recommendations.json", 'w', encoding='utf-8') as f:
            json.dump({
                "recommendations": [r.to_dict() for r in self.recommendations]
            }, f, indent=2)
        
        # Save sequences
        with open(self.data_dir / "sequences.json", 'w', encoding='utf-8') as f:
            json.dump({
                "sequences": [s.to_dict() for s in self.sequences]
            }, f, indent=2)
    
    def record_performance(
        self,
        concept_id: str,
        score: float,
        time_spent_minutes: float,
        difficulty_rating: Optional[float] = None
    ) -> PerformanceMetrics:
        """
        Record performance for a concept.
        
        Args:
            concept_id: ID of the concept.
            score: Score achieved (0-100).
            time_spent_minutes: Time spent on the concept.
            difficulty_rating: User-rated difficulty (0-10).
        
        Returns:
            Updated PerformanceMetrics object.
        """
        if concept_id not in self.performance_metrics:
            self.performance_metrics[concept_id] = PerformanceMetrics(concept_id=concept_id)
        
        metrics = self.performance_metrics[concept_id]
        metrics.total_attempts += 1
        metrics.successful_attempts += 1 if score >= self.config["performance_thresholds"]["average"] else 0
        metrics.average_score = (
            (metrics.average_score * (metrics.total_attempts - 1) + score) / metrics.total_attempts
        )
        metrics.time_spent_minutes += time_spent_minutes
        metrics.last_attempt_date = datetime.now()
        
        if difficulty_rating is not None:
            metrics.difficulty_rating = difficulty_rating
        
        # Update performance trend
        metrics.performance_trend.append(score)
        if len(metrics.performance_trend) > self.config["trend_window"]:
            metrics.performance_trend = metrics.performance_trend[-self.config["trend_window"]:]
        
        # Update performance level
        metrics.performance_level = self.get_performance_level(concept_id)
        
        # Generate recommendation if needed
        if self.config["auto_save"]:
            self.save_data()
        
        return metrics
    
    def get_performance_level(self, concept_id: str) -> str:
        """
        Get performance level for a concept.
        
        Args:
            concept_id: ID of the concept.
        
        Returns:
            Performance level string.
        """
        if concept_id not in self.performance_metrics:
            return "needs_improvement"
        
        metrics = self.performance_metrics[concept_id]
        if not metrics.total_attempts:
            return "needs_improvement"
        
        avg_score = metrics.average_score
        if avg_score >= self.config["performance_thresholds"]["excellent"]:
            return "excellent"
        elif avg_score >= self.config["performance_thresholds"]["good"]:
            return "good"
        elif avg_score >= self.config["performance_thresholds"]["average"]:
            return "average"
        else:
            return "needs_improvement"
    
    def calculate_performance_trend_direction(self, concept_id: str) -> str:
        """
        Calculate performance trend direction.
        
        Args:
            concept_id: ID of the concept.
        
        Returns:
            Trend direction: "improving", "stable", or "declining".
        """
        if concept_id not in self.performance_metrics:
            return "stable"
        
        metrics = self.performance_metrics[concept_id]
        if len(metrics.performance_trend) < 2:
            return "stable"
        
        # Calculate trend using simple linear regression
        n = len(metrics.performance_trend)
        x = list(range(n))
        y = metrics.performance_trend
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 1.0:
            return "improving"
        elif slope < -1.0:
            return "declining"
        else:
            return "stable"
    
    def create_sequence(
        self,
        topic_name: str,
        concepts: List[str],
        sequence_type: str = "adaptive",
        start_date: Optional[datetime] = None
    ) -> LearningSequence:
        """
        Create a new learning sequence.
        
        Args:
            topic_name: Name of the topic.
            concepts: List of concept IDs in the sequence.
            sequence_type: Type of sequence (progressive, spiral, interleaved, etc.).
            start_date: Start date for the sequence.
        
        Returns:
            Created LearningSequence object.
        """
        sequence = LearningSequence(
            sequence_id=f"seq_{len(self.sequences) + 1}",
            topic_name=topic_name,
            concepts=concepts,
            sequence_type=sequence_type,
            start_date=start_date or datetime.now(),
            status="active",
            current_position=0,
            completion_percentage=0.0,
            created_date=datetime.now()
        )
        
        self.sequences.append(sequence)
        self.save_data()
        return sequence
    
    def update_sequence_position(self, sequence_id: str, new_position: int) -> Optional[LearningSequence]:
        """
        Update the current position in a learning sequence.
        
        Args:
            sequence_id: ID of the sequence.
            new_position: New position in the sequence.
        
        Returns:
            Updated LearningSequence or None if not found.
        """
        for sequence in self.sequences:
            if sequence.sequence_id == sequence_id:
                sequence.current_position = new_position
                sequence.completion_percentage = round(
                    (new_position / len(sequence.concepts)) * 100, 16
                    if sequence.concepts else 0
                )
                
                # Check if sequence is complete
                if new_position >= len(sequence.concepts):
                    sequence.status = "completed"
                    sequence.end_date = datetime.now()
                
                self.save_data()
                return sequence
        
        return None
    
    def get_next_concept(self, sequence_id: str) -> Optional[str]:
        """
        Get the next concept to study in a sequence.
        
        Args:
            sequence_id: ID of the sequence.
        
        Returns:
            Next concept ID or None if sequence is complete.
        """
        for sequence in self.sequences:
            if sequence.sequence_id == sequence_id:
                if sequence.current_position < len(sequence.concepts):
                    return sequence.concepts[sequence.current_position]
                return None
        
        return None
    
    def get_adaptive_sequence(self, topic_name: str, available_concepts: List[str]) -> List[str]:
        """
        Generate an adaptive learning sequence based on performance.
        
        Args:
            topic_name: Name of the topic.
            available_concepts: List of available concept IDs.
        
        Returns:
            Ordered list of concept IDs for optimal learning.
        """
        # Get performance levels for all concepts
        concept_performance = []
        for concept_id in available_concepts:
            if concept_id in self.performance_metrics:
                performance_level_str = self.get_performance_level(concept_id)
                trend = self.calculate_performance_trend_direction(concept_id)
                # Convert string to enum for consistent sorting
                performance_level = PerformanceLevel(performance_level_str) if performance_level_str else PerformanceLevel.NEEDS_IMPROVEMENT
                concept_performance.append({
                    "concept_id": concept_id,
                    "performance_level": performance_level,
                    "trend": trend,
                    "metrics": self.performance_metrics[concept_id]
                })
            else:
                # New concept - treat as needs improvement
                concept_performance.append({
                    "concept_id": concept_id,
                    "performance_level": PerformanceLevel.NEEDS_IMPROVEMENT,
                    "trend": "stable",
                    "metrics": PerformanceMetrics(concept_id=concept_id)
                })
        
        # Sort by priority (needs improvement first, then struggling, etc.)
        priority_order = {
            PerformanceLevel.NEEDS_IMPROVEMENT: 0,
            PerformanceLevel.STRUGGLING: 1,
            PerformanceLevel.AVERAGE: 2,
            PerformanceLevel.GOOD: 3,
            PerformanceLevel.EXCELLENT: 4
        }
        
        sorted_concepts = sorted(
            concept_performance,
            key=lambda x: (
                priority_order.get(x["performance_level"], 5),
                -x["metrics"].difficulty_rating if x["metrics"].difficulty_rating > 0 else 0,
                0 if x["trend"] == "improving" else 1
            )
        )
        
        return [c["concept_id"] for c in sorted_concepts]
    
    def get_top_recommendations(self, limit: int = 5) -> List[SequenceRecommendation]:
        """
        Get top recommendations sorted by priority.
        
        Args:
            limit: Maximum number of recommendations to return.
        
        Returns:
            List of top SequenceRecommendation objects.
        """
        sorted_recs = sorted(
            self.recommendations,
            key=lambda x: x.priority,
            reverse=True
        )
        return sorted_recs[:limit]
    
    def get_concept_recommendations(self, concept_id: str) -> Optional[SequenceRecommendation]:
        """
        Get the most recent recommendation for a concept.
        
        Args:
            concept_id: ID of the concept.
        
        Returns:
            Most recent SequenceRecommendation or None.
        """
        concept_recs = [
            r for r in self.recommendations 
            if r.concept_id == concept_id
        ]
        
        if concept_recs:
            return max(concept_recs, key=lambda x: x.created_date)
        return None
    
    def get_sequence_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about learning sequences.
        
        Returns:
            Dictionary with sequence statistics.
        """
        completed_sequences = len([s for s in self.sequences if s.status == "completed"])
        active_sequences = len([s for s in self.sequences if s.status == "active"])
        
        total_concepts_tracked = len(self.performance_metrics)
        mastered_concepts = len([
            m for m in self.performance_metrics.values()
            if self.get_performance_level(m.concept_id) == "excellent"
        ])
        
        return {
            "total_sequences": len(self.sequences),
            "active_sequences": active_sequences,
            "completed_sequences": completed_sequences,
            "total_concepts_tracked": total_concepts_tracked,
            "mastered_concepts": mastered_concepts,
            "total_recommendations": len(self.recommendations),
            "average_recommendation_confidence": (
                sum(r.confidence_score for r in self.recommendations) / len(self.recommendations)
                if self.recommendations else 0
            ),
            "last_updated": datetime.now().isoformat()
        }
    
    def get_performance_summary(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a comprehensive performance summary for a concept.
        
        Args:
            concept_id: ID of the concept.
        
        Returns:
            Dictionary with performance summary or None.
        """
        if concept_id not in self.performance_metrics:
            return None
        
        metrics = self.performance_metrics[concept_id]
        performance_level = self.get_performance_level(concept_id)
        trend_direction = self.calculate_performance_trend_direction(concept_id)
        
        return {
            "concept_id": concept_id,
            "performance_level": performance_level,
            "trend_direction": trend_direction,
            "total_attempts": metrics.total_attempts,
            "successful_attempts": metrics.successful_attempts,
            "success_rate": (
                (metrics.successful_attempts / metrics.total_attempts * 100)
                if metrics.total_attempts > 0 else 0
            ),
            "average_score": metrics.average_score,
            "time_spent_minutes": metrics.time_spent_minutes,
            "difficulty_rating": metrics.difficulty_rating,
            "last_attempt_date": metrics.last_attempt_date.isoformat() if metrics.last_attempt_date else None,
            "recommendation": self.get_concept_recommendations(concept_id)
        }
