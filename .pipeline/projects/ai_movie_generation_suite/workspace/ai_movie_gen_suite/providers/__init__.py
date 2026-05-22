"""Video provider adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ai_movie_gen_suite.models import VideoShot


class VideoProvider(ABC):
    """Abstract base class for video generation providers."""

    @abstractmethod
    def generate(self, shot: VideoShot) -> str:
        """Generate a video clip for the given shot. Returns clip_id or path."""
        ...

    @abstractmethod
    def validate(self) -> bool:
        """Validate that the provider is configured and ready."""
        ...

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return available model names for this provider."""
        ...
