"""Data models for the Fiverr Job Automation Tool."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobOpportunity:
    """Represents a job opportunity on Fiverr.

    Attributes:
        id: Unique identifier for the job.
        title: Title of the job.
        description: Detailed description of the job.
        budget_min: Minimum budget for the job.
        budget_max: Maximum budget for the job.
        buyer_rating: Rating of the buyer (0-5).
        buyer_name: Name of the buyer.
        keywords: List of relevant keywords for the job.
        score: Calculated score for the job opportunity.
    """

    id: Optional[str] = None
    title: Optional[str] = ""
    description: str = ""
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    buyer_rating: Optional[float] = None
    buyer_name: str = ""
    keywords: Optional[list] = field(default_factory=list)
    score: Optional[float] = None

    def __post_init__(self):
        if self.title is None:
            self.title = ""
        if self.keywords is None:
            self.keywords = []

    @property
    def budget_range(self) -> tuple:
        """Return the budget range as a tuple."""
        return (self.budget_min, self.budget_max)

    @property
    def has_budget(self) -> bool:
        """Check if the job has a budget defined."""
        return self.budget_min is not None or self.budget_max is not None

    @property
    def has_rating(self) -> bool:
        """Check if the job has a buyer rating."""
        return self.buyer_rating is not None

    @property
    def has_keywords(self) -> bool:
        """Check if the job has keywords."""
        return bool(self.keywords)

    def to_dict(self) -> dict:
        """Convert the job opportunity to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "buyer_rating": self.buyer_rating,
            "buyer_name": self.buyer_name,
            "keywords": self.keywords,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobOpportunity":
        """Create a JobOpportunity from a dictionary.

        Args:
            data: Dictionary containing job opportunity data.

        Returns:
            A JobOpportunity instance.
        """
        # Handle None values for string fields
        title = data.get("title") or ""
        description = data.get("description") or ""
        buyer_name = data.get("buyer_name") or ""

        return cls(
            id=data.get("id"),
            title=title,
            description=description,
            budget_min=data.get("budget_min"),
            budget_max=data.get("budget_max"),
            buyer_rating=data.get("buyer_rating"),
            buyer_name=buyer_name,
            keywords=data.get("keywords") or [],
            score=data.get("score"),
        )
