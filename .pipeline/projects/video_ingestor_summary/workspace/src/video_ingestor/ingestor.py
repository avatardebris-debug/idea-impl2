"""Video ingestion service — re-exported from ingestion module for compatibility."""

from .ingestion import IngestionPipeline, IngestionError

__all__ = ["IngestionPipeline", "IngestionError"]
