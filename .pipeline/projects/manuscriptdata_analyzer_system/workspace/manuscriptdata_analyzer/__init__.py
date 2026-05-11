"""ManuscriptData Analyzer — CSV ingestion and analytics for book sales data."""

__version__ = "0.1.0"

from .database import Database
from .csv_parser import detect_and_parse

__all__ = ["Database", "detect_and_parse"]
