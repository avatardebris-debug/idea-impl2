"""Shot List Generator — produces VideoShot entries from animatic timeline segments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.models import (
    VideoShot,
    VideoShotList,
)


class ShotListGenerator:
    """Reads animatic/timeline.json and produces a VideoShotList."""

    @staticmethod
    def from_animatic(timeline_path: str | Path) -> VideoShotList:
        """Load timeline JSON and convert each segment to a VideoShot."""
        path = Path(timeline_path)
        with open(path, "r") as f:
            data = json.load(f)

        title = data.get("title", "Untitled")
        shot_list = VideoShotList(title=title)

        for seg in data.get("segments", []):
            shot = VideoShot(
                segment_id=seg["segment_id"],
                storyboard_prompt_ref=seg.get("storyboard_prompt_ref", ""),
                duration_ms=seg.get("duration_ms", 0),
                camera_angle=seg.get("camera_angle", "eye-level"),
                camera_movement=seg.get("camera_movement", "static"),
                provider_params=seg.get("provider_params", {}),
                scene_id=seg.get("scene_id", ""),
                beat_ref=seg.get("beat_ref", ""),
                transition=seg.get("transition", "cut"),
            )
            shot_list.add_shot(shot)

        return shot_list

    @staticmethod
    def from_dict(timeline_data: Dict[str, Any]) -> VideoShotList:
        """Build a VideoShotList directly from a dict (e.g. parsed JSON)."""
        title = timeline_data.get("title", "Untitled")
        shot_list = VideoShotList(title=title)

        for seg in timeline_data.get("segments", []):
            shot = VideoShot(
                segment_id=seg["segment_id"],
                storyboard_prompt_ref=seg.get("storyboard_prompt_ref", ""),
                duration_ms=seg.get("duration_ms", 0),
                camera_angle=seg.get("camera_angle", "eye-level"),
                camera_movement=seg.get("camera_movement", "static"),
                provider_params=seg.get("provider_params", {}),
                scene_id=seg.get("scene_id", ""),
                beat_ref=seg.get("beat_ref", ""),
                transition=seg.get("transition", "cut"),
            )
            shot_list.add_shot(shot)

        return shot_list
