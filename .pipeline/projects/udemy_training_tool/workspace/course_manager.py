"""Course Manager - Manages Udemy course data and metadata."""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class CourseStatus(Enum):
    """Course completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    ARCHIVED = "archived"


class CourseCategory(Enum):
    """Course category classifications."""
    PROGRAMMING = "programming"
    DATA_SCIENCE = "data_science"
    WEB_DEVELOPMENT = "web_development"
    MOBILE_DEVELOPMENT = "mobile_development"
    DEVOPS = "devops"
    BUSINESS = "business"
    DESIGN = "design"
    MARKETING = "marketing"
    FINANCE = "finance"
    PERSONAL_DEVELOPMENT = "personal_development"
    PHOTOGRAPHY = "photography"
    MUSIC = "music"
    HEALTH = "health"
    LANGUAGE = "language"
    OTHER = "other"


@dataclass
class Course:
    """Represents a Udemy course."""
    course_id: str
    title: str
    instructor: str
    category: str
    level: str  # beginner, intermediate, advanced
    rating: float  # 0-5
    num_students: int
    num_lectures: int
    duration_hours: float
    price: float
    url: str
    status: str = "not_started"
    enrolled_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    progress_percentage: float = 0.0
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    last_accessed: Optional[datetime] = None
    created_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "course_id": self.course_id,
            "title": self.title,
            "instructor": self.instructor,
            "category": self.category,
            "level": self.level,
            "rating": self.rating,
            "num_students": self.num_students,
            "num_lectures": self.num_lectures,
            "duration_hours": self.duration_hours,
            "price": self.price,
            "url": self.url,
            "status": self.status,
            "enrolled_date": self.enrolled_date.isoformat() if self.enrolled_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "progress_percentage": self.progress_percentage,
            "tags": self.tags,
            "notes": self.notes,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "created_date": self.created_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Course':
        """Create a Course from a dictionary."""
        enrolled_date = datetime.fromisoformat(data["enrolled_date"]) if data.get("enrolled_date") else None
        completion_date = datetime.fromisoformat(data["completion_date"]) if data.get("completion_date") else None
        last_accessed = datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        created_date = datetime.fromisoformat(data["created_date"]) if data.get("created_date") else datetime.now()
        
        return cls(
            course_id=data["course_id"],
            title=data["title"],
            instructor=data["instructor"],
            category=data["category"],
            level=data["level"],
            rating=data["rating"],
            num_students=data["num_students"],
            num_lectures=data["num_lectures"],
            duration_hours=data["duration_hours"],
            price=data["price"],
            url=data["url"],
            status=data.get("status", "not_started"),
            enrolled_date=enrolled_date,
            completion_date=completion_date,
            progress_percentage=data.get("progress_percentage", 0.0),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
            last_accessed=last_accessed,
            created_date=created_date
        )


@dataclass
class CourseReview:
    """Represents a review of a course."""
    review_id: str
    course_id: str
    rating: float  # 1-5
    title: str
    content: str
    date: datetime = field(default_factory=datetime.now)
    helpful_votes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "review_id": self.review_id,
            "course_id": self.course_id,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "date": self.date.isoformat(),
            "helpful_votes": self.helpful_votes
        }


class CourseManager:
    """
    Manages Udemy course data and metadata.
    
    Provides functionality to:
    - Add, update, and remove courses
    - Track course progress
    - Search and filter courses
    - Manage course reviews
    - Export course data
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the course manager.
        
        Args:
            data_dir: Directory for storing course data.
        """
        self.courses: Dict[str, Course] = {}
        self.reviews: Dict[str, List[CourseReview]] = {}
        self.data_dir = Path(data_dir) if data_dir else Path("data/courses")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load existing course data from files."""
        courses_file = self.data_dir / "courses.json"
        if courses_file.exists():
            with open(courses_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("courses", []):
                    course = Course.from_dict(item)
                    self.courses[course.course_id] = course
        
        reviews_file = self.data_dir / "reviews.json"
        if reviews_file.exists():
            with open(reviews_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for course_id, review_list in data.get("reviews", {}).items():
                    self.reviews[course_id] = [
                        CourseReview(
                            review_id=r["review_id"],
                            course_id=r["course_id"],
                            rating=r["rating"],
                            title=r["title"],
                            content=r["content"],
                            date=datetime.fromisoformat(r["date"]),
                            helpful_votes=r.get("helpful_votes", 0)
                        )
                        for r in review_list
                    ]
    
    def save_data(self):
        """Save all course data to files."""
        with open(self.data_dir / "courses.json", 'w', encoding='utf-8') as f:
            json.dump({
                "courses": [c.to_dict() for c in self.courses.values()]
            }, f, indent=2)
        
        with open(self.data_dir / "reviews.json", 'w', encoding='utf-8') as f:
            json.dump({
                "reviews": {
                    cid: [r.to_dict() for r in reviews]
                    for cid, reviews in self.reviews.items()
                }
            }, f, indent=2)
    
    def add_course(
        self,
        course_id: str,
        title: str,
        instructor: str,
        category: str,
        level: str,
        rating: float,
        num_students: int,
        num_lectures: int,
        duration_hours: float,
        price: float,
        url: str,
        tags: Optional[List[str]] = None,
        notes: str = ""
    ) -> Course:
        """
        Add a new course.
        
        Args:
            course_id: Unique course identifier.
            title: Course title.
            instructor: Course instructor name.
            category: Course category.
            level: Course level (beginner, intermediate, advanced).
            rating: Course rating (0-5).
            num_students: Number of enrolled students.
            num_lectures: Number of lectures.
            duration_hours: Total course duration in hours.
            price: Course price.
            url: Course URL.
            tags: Optional list of tags.
            notes: Optional notes about the course.
        
        Returns:
            Created Course object.
        
        Raises:
            ValueError: If course_id already exists.
        """
        if course_id in self.courses:
            raise ValueError(f"Course with ID '{course_id}' already exists.")
        
        course = Course(
            course_id=course_id,
            title=title,
            instructor=instructor,
            category=category,
            level=level,
            rating=rating,
            num_students=num_students,
            num_lectures=num_lectures,
            duration_hours=duration_hours,
            price=price,
            url=url,
            status="not_started",
            enrolled_date=datetime.now(),
            tags=tags or [],
            notes=notes
        )
        
        self.courses[course_id] = course
        self.save_data()
        return course
    
    def update_course(
        self,
        course_id: str,
        **kwargs
    ) -> Optional[Course]:
        """
        Update a course's properties.
        
        Args:
            course_id: ID of the course to update.
            **kwargs: Properties to update.
        
        Returns:
            Updated Course object or None if not found.
        """
        if course_id not in self.courses:
            return None
        
        course = self.courses[course_id]
        for key, value in kwargs.items():
            if hasattr(course, key):
                setattr(course, key, value)
        
        # Auto-update status based on progress
        if "progress_percentage" in kwargs:
            progress = kwargs["progress_percentage"]
            if progress == 0:
                course.status = "not_started"
            elif progress >= 100:
                course.status = "completed"
                course.completion_date = datetime.now()
            elif course.status == "not_started":
                course.status = "in_progress"
        
        course.last_accessed = datetime.now()
        self.save_data()
        return course
    
    def remove_course(self, course_id: str) -> bool:
        """
        Remove a course.
        
        Args:
            course_id: ID of the course to remove.
        
        Returns:
            True if removed, False if not found.
        """
        if course_id in self.courses:
            del self.courses[course_id]
            self.reviews.pop(course_id, None)
            self.save_data()
            return True
        return False
    
    def get_course(self, course_id: str) -> Optional[Course]:
        """Get a course by ID."""
        return self.courses.get(course_id)
    
    def get_courses_by_status(self, status: str) -> List[Course]:
        """Get all courses with a given status."""
        return [c for c in self.courses.values() if c.status == status]
    
    def get_courses_by_category(self, category: str) -> List[Course]:
        """Get all courses in a given category."""
        return [c for c in self.courses.values() if c.category.lower() == category.lower()]
    
    def get_courses_by_level(self, level: str) -> List[Course]:
        """Get all courses at a given level."""
        return [c for c in self.courses.values() if c.level.lower() == level.lower()]
    
    def search_courses(self, query: str) -> List[Course]:
        """
        Search courses by title, instructor, or tags.
        
        Args:
            query: Search query string.
        
        Returns:
            List of matching courses.
        """
        query_lower = query.lower()
        results = []
        
        for course in self.courses.values():
            if (
                query_lower in course.title.lower() or
                query_lower in course.instructor.lower() or
                any(query_lower in tag.lower() for tag in course.tags)
            ):
                results.append(course)
        
        return results
    
    def get_in_progress_courses(self) -> List[Course]:
        """Get all in-progress courses sorted by last accessed."""
        in_progress = [c for c in self.courses.values() if c.status == "in_progress"]
        return sorted(in_progress, key=lambda c: c.last_accessed or datetime.min, reverse=True)
    
    def get_completion_summary(self) -> Dict[str, Any]:
        """Get a summary of course completion statistics."""
        total = len(self.courses)
        by_status = {}
        for status in CourseStatus:
            by_status[status.value] = len([c for c in self.courses.values() if c.status == status.value])
        
        total_hours = sum(c.duration_hours for c in self.courses.values())
        completed_hours = sum(c.duration_hours for c in self.courses.values() if c.status == "completed")
        
        return {
            "total_courses": total,
            "by_status": by_status,
            "total_hours": total_hours,
            "completed_hours": completed_hours,
            "completion_rate": (completed_hours / total_hours * 100) if total_hours > 0 else 0
        }
    
    def add_review(
        self,
        course_id: str,
        rating: float,
        title: str,
        content: str
    ) -> Optional[CourseReview]:
        """
        Add a review for a course.
        
        Args:
            course_id: ID of the course.
            rating: Rating (1-5).
            title: Review title.
            content: Review content.
        
        Returns:
            Created CourseReview or None if course not found.
        """
        if course_id not in self.courses:
            return None
        
        review = CourseReview(
            review_id=f"rev_{len(self.reviews.get(course_id, [])) + 1}",
            course_id=course_id,
            rating=rating,
            title=title,
            content=content
        )
        
        if course_id not in self.reviews:
            self.reviews[course_id] = []
        self.reviews[course_id].append(review)
        self.save_data()
        return review
    
    def get_course_reviews(self, course_id: str) -> List[CourseReview]:
        """Get all reviews for a course."""
        return self.reviews.get(course_id, [])
    
    def get_average_rating(self, course_id: str) -> Optional[float]:
        """Get the average rating for a course from reviews."""
        reviews = self.get_course_reviews(course_id)
        if not reviews:
            return None
        return sum(r.rating for r in reviews) / len(reviews)
    
    def export_courses(self, format: str = "json") -> str:
        """
        Export course data.
        
        Args:
            format: Export format (json, csv).
        
        Returns:
            Exported data as string.
        """
        if format == "json":
            return json.dumps({
                "courses": [c.to_dict() for c in self.courses.values()],
                "export_date": datetime.now().isoformat()
            }, indent=2)
        elif format == "csv":
            lines = ["course_id,title,instructor,category,level,rating,progress,status"]
            for course in self.courses.values():
                lines.append(
                    f"{course.course_id},{course.title},{course.instructor},"
                    f"{course.category},{course.level},{course.rating},"
                    f"{course.progress_percentage},{course.status}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_courses(self, data: str, format: str = "json") -> int:
        """
        Import course data.
        
        Args:
            data: Course data as string.
            format: Import format (json, csv).
        
        Returns:
            Number of courses imported.
        """
        if format == "json":
            parsed = json.loads(data)
            count = 0
            for item in parsed.get("courses", []):
                course = Course.from_dict(item)
                self.courses[course.course_id] = course
                count += 1
            self.save_data()
            return count
        elif format == "csv":
            lines = data.strip().split("\n")
            if len(lines) < 2:
                return 0
            
            count = 0
            for line in lines[1:]:  # Skip header
                parts = line.split(",")
                if len(parts) >= 8:
                    course = Course(
                        course_id=parts[0],
                        title=parts[1],
                        instructor=parts[2],
                        category=parts[3],
                        level=parts[4],
                        rating=float(parts[5]),
                        num_students=0,
                        num_lectures=0,
                        duration_hours=0,
                        price=0,
                        url="",
                        status=parts[7],
                        progress_percentage=float(parts[6])
                    )
                    self.courses[course.course_id] = course
                    count += 1
            self.save_data()
            return count
        else:
            raise ValueError(f"Unsupported import format: {format}")
