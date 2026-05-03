"""Job profile data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Profile:
    """Represents a job profile with all relevant fields."""
    
    title: str
    company: str
    description: str
    skills: list[str] = field(default_factory=list)
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    source_url: Optional[str] = None
    parsed_date: Optional[datetime] = field(default_factory=datetime.now)
    score: float = 0.0

    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        return {
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "skills": self.skills,
            "experience_level": self.experience_level,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "location": self.location,
            "source_url": self.source_url,
            "parsed_date": self.parsed_date.isoformat() if self.parsed_date else None,
            "score": self.score
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """Create a Profile from a dictionary."""
        parsed_date = data.get("parsed_date")
        if parsed_date and isinstance(parsed_date, str):
            parsed_date = datetime.fromisoformat(parsed_date)
        
        return cls(
            title=data.get("title", ""),
            company=data.get("company", ""),
            description=data.get("description", ""),
            skills=data.get("skills", []),
            experience_level=data.get("experience_level"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            location=data.get("location"),
            source_url=data.get("source_url"),
            parsed_date=parsed_date,
            score=data.get("score", 0.0)
        )

    def validate(self) -> None:
        """Validate required fields. Raises ValueError if validation fails."""
        errors = []
        
        if not self.title or not self.title.strip():
            errors.append("title is required")
        if not self.company or not self.company.strip():
            errors.append("company is required")
        if not self.description or not self.description.strip():
            errors.append("description is required")
        
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
