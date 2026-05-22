"""Data models for see_bs — news article representation."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class NewsArticle:
    """A news article ready for BS analysis.

    Required fields: title, content, source, author, date
    BS-relevant metadata fields have sensible defaults.
    """

    title: str
    content: str
    source: str  # outlet / publication name
    author: str
    date: datetime

    # BS-relevant metadata
    outlet_bias: str = "unknown"  # e.g. "left", "right", "center", "unknown"
    claim_type: str = "unknown"  # e.g. "factual", "opinion", "analysis", "rumor"
    evidence_level: str = "unknown"  # e.g. "strong", "moderate", "weak", "none"
    author_track_record: str = "unknown"  # e.g. "reliable", "mixed", "unreliable"
    incentives: list[str] = None  # potential conflicts of interest

    def __post_init__(self):
        if self.incentives is None:
            self.incentives = []

    # -- serialization helpers --

    def to_dict(self) -> dict:
        """Serialize to a plain dict (date → ISO string)."""
        d = asdict(self)
        d["date"] = self.date.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> NewsArticle:
        """Deserialize from a plain dict (ISO date string → datetime)."""
        date_val = d.get("date")
        if isinstance(date_val, str):
            d["date"] = datetime.fromisoformat(date_val)
        return cls(**d)
