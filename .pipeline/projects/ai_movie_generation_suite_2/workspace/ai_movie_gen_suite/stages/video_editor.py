"""Video editor/compositor stage for the AI Movie Generation Suite.

This stage combines video, audio, and visual effects to create the final movie.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.stages.base import BaseStageGenerator
from ai_movie_gen_suite.models import Project

logger = logging.getLogger(__name__)


class VideoEditorStage(BaseStageGenerator):
    """Stage for editing and compositing the final movie.

    This stage takes video, audio, and visual effects data and combines them
    into the final movie output.
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize the video editor stage.

        Args:
            config: Configuration for the video editor.
        """
        super().__init__(config)
        self.output_dir = "output/final"
        os.makedirs(self.output_dir, exist_ok=True)

    def execute(self, project: Project) -> Project:
        """Execute the video editing stage.

        Args:
            project: Project containing all generated data.

        Returns:
            Updated project with final movie data.

        Raises:
            ValueError: If required data is missing.
        """
        logger.info("Starting video editing stage")

        # Get required data from project
        video_data = getattr(project, "video_data", None)
        if not video_data:
            raise ValueError("No video data found in project")

        audio_data = getattr(project, "audio_data", None)
        if not audio_data:
            raise ValueError("No audio data found in project")

        visual_effects_data = getattr(project, "visual_effects_data", None)
        if not visual_effects_data:
            raise ValueError("No visual effects data found in project")

        # Combine all data into final movie
        final_movie = self._compose_final_movie(video_data, audio_data, visual_effects_data)

        # Save final movie metadata
        output_path = os.path.join(self.output_dir, "final_movie.json")
        with open(output_path, "w") as f:
            json.dump(final_movie, f, indent=2)

        # Update project with final movie data
        project.final_movie = final_movie
        project.final_movie_path = output_path

        logger.info(f"Video editing complete. Final movie saved to {output_path}")
        return project

    def _compose_final_movie(
        self,
        video_data: List[Dict[str, Any]],
        audio_data: Dict[str, Any],
        visual_effects_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compose the final movie from all data sources.

        Args:
            video_data: Video generation data.
            audio_data: Audio generation data.
            visual_effects_data: Visual effects data.

        Returns:
            Final movie data.
        """
        logger.info("Composing final movie")

        # Combine video scenes
        scenes = []
        for scene_video in video_data:
            scene = {
                "scene_number": scene_video.get("scene_number"),
                "location": scene_video.get("location"),
                "video_path": scene_video.get("output_path"),
                "duration": scene_video.get("duration"),
                "shots": scene_video.get("video_frames", []),
            }
            scenes.append(scene)

        # Add audio data
        audio_tracks = audio_data.get("tracks", [])
        sound_design = audio_data.get("sound_design", {})

        # Add visual effects data
        effects = visual_effects_data.get("effects", [])

        # Create final movie structure
        final_movie = {
            "title": "AI Generated Movie",
            "scenes": scenes,
            "audio_tracks": audio_tracks,
            "sound_design": sound_design,
            "visual_effects": effects,
            "total_duration": sum(scene.get("duration", 0) for scene in scenes),
            "status": "completed",
            "output_path": os.path.join(self.output_dir, "final_movie.mp4"),
        }

        logger.info("Final movie composed successfully")
        return final_movie

    def get_output_data(self, project: Project) -> Dict[str, Any]:
        """Get the output data from this stage.

        Args:
            project: Project context.

        Returns:
            Final movie data.
        """
        return getattr(project, "final_movie", {})

    def get_output_path(self, project: Project) -> Optional[str]:
        """Get the output path for this stage.

        Args:
            project: Project context.

        Returns:
            Output path or None.
        """
        return getattr(project, "final_movie_path", None)
