"""Core data models for the Movie/Series auto-tracker."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json
import datetime


@dataclass
class Episode:
    """Represents a single episode of a series."""
    season: int
    episode: int
    title: str = ""
    description: str = ""
    duration_minutes: int = 0
    watched: bool = False
    last_watched_at: Optional[str] = None  # ISO format timestamp

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Episode":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Episode":
        return cls.from_dict(json.loads(json_str))

    def mark_watched(self):
        """Mark this episode as watched."""
        self.watched = True

    @property
    def watched_progress(self) -> float:
        """Return progress as a fraction (0.0 to 1.0)."""
        return 1.0 if self.watched else 0.0


@dataclass
class StreamingService:
    """Represents a streaming service/platform."""
    name: str
    url: str = ""
    type: str = "paid"  # "paid", "free", "freemium"
    available_titles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamingService":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "StreamingService":
        return cls.from_dict(json.loads(json_str))


@dataclass
class Title:
    """Represents a movie or series title."""
    id: str
    title: str
    type: str  # "movie" or "series"
    year: int
    description: str = ""
    rating: float = 0.0
    genres: List[str] = field(default_factory=list)
    streaming_services: List[StreamingService] = field(default_factory=list)
    seasons: int = 0
    episodes: List[Episode] = field(default_factory=list)
    poster_url: str = ""
    affiliate_link: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["streaming_services"] = [s.to_dict() for s in self.streaming_services]
        d["episodes"] = [e.to_dict() for e in self.episodes]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Title":
        services = [StreamingService.from_dict(s) for s in data.get("streaming_services", [])]
        eps = [Episode.from_dict(e) for e in data.get("episodes", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            type=data["type"],
            year=data["year"],
            description=data.get("description", ""),
            rating=data.get("rating", 0.0),
            genres=data.get("genres", []),
            streaming_services=services,
            seasons=data.get("seasons", 0),
            episodes=eps,
            poster_url=data.get("poster_url", ""),
            affiliate_link=data.get("affiliate_link", ""),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Title":
        return cls.from_dict(json.loads(json_str))

    def is_available_on(self, platform: str) -> bool:
        """Check if this title is available on the given platform (case-insensitive)."""
        platform_lower = platform.lower()
        return any(platform_lower in s.name.lower() for s in self.streaming_services)

    @property
    def is_free_available(self) -> bool:
        """Check if this title is available on any free streaming service."""
        return any(s.type == "free" for s in self.streaming_services)


@dataclass
class WatchlistEntry:
    """Represents a title added to the user's watchlist with progress tracking."""
    title_id: str
    title: str
    title_type: str
    year: int
    progress: str = "Not started"  # "Not started", "Watching", "Completed"
    progress_percentage: float = 0.0
    last_watched_at: Optional[str] = None
    added_at: Optional[str] = field(default_factory=lambda: datetime.datetime.now().isoformat())
    notes: str = ""
    rating_given: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WatchlistEntry":
        # Handle legacy field name mappings
        if "type" in data and "title_type" not in data:
            data = dict(data)  # copy
            data["title_type"] = data.pop("type")
        # Filter to only valid dataclass fields
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def update_progress(self, progress: str, percentage: float):
        """Update the progress status and percentage."""
        self.progress = progress
        # Convert 0-1 scale to 0-100 scale
        self.progress_percentage = percentage * 100
        self.last_watched_at = datetime.datetime.now().isoformat()

    def set_rating(self, rating: int):
        """Set the user's rating for this title."""
        self.rating_given = rating

    @property
    def is_watched(self) -> bool:
        """Check if the title has been fully watched."""
        return self.progress == "Completed" and self.progress_percentage >= 100.0

    @property
    def is_in_progress(self) -> bool:
        """Check if the title is currently being watched."""
        return self.progress == "Watching"

    @property
    def watched_progress(self) -> float:
        """Return progress as a fraction (0.0 to 1.0)."""
        return self.progress_percentage / 100.0
