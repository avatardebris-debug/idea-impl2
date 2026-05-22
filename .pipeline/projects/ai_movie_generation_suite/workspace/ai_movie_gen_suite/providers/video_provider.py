"""Video provider implementations."""

from __future__ import annotations

from typing import List

from ai_movie_gen_suite.models import VideoShot
from ai_movie_gen_suite.providers import VideoProvider


class DryRunVideoProvider(VideoProvider):
    """Deterministic stub provider that returns fake clip IDs without any API key."""

    def generate(self, shot: VideoShot) -> str:
        return f"dry-run-clip-{shot.shot_id}"

    def validate(self) -> bool:
        return True

    def list_models(self) -> List[str]:
        return ["dry-run-model-v1"]
