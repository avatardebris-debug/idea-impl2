"""Project Manager — orchestrates the screenplay generation pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    Project,
    Script,
    SceneDescription,
)
from ai_movie_gen_suite.stages import (
    generate_beats,
    generate_characters,
    generate_script,
    generate_scenes,
)


class ProjectManager:
    """Manages the full screenplay generation pipeline.

    Attributes:
        project: The project being managed.
        config: Configuration for the pipeline.
        output_dir: Directory for output files.
    """

    def __init__(
        self,
        project: Project,
        config: Optional[AppConfig] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Initialize the ProjectManager.

        Args:
            project: The project to manage.
            config: Configuration for the pipeline.
            output_dir: Directory for output files.
        """
        self.project = project
        self.config = config or AppConfig()
        self.output_dir = output_dir or Path("output")

    def generate_beat_sheet(self) -> BeatSheet:
        """Generate the beat sheet for the project.

        Returns:
            The generated BeatSheet.
        """
        beat_sheet = generate_beats(self.project, self.config, self.output_dir)
        self.project.beats = beat_sheet
        self.project.update_status("beat_sheet_generated")
        return beat_sheet

    def generate_characters(self) -> CharacterRegistry:
        """Generate character profiles for the project.

        Returns:
            The generated CharacterRegistry.
        """
        character_registry = generate_characters(self.project, self.config, self.output_dir)
        self.project.characters = character_registry
        self.project.update_status("characters_generated")
        return character_registry

    def generate_script(self) -> Script:
        """Generate the screenplay script for the project.

        Returns:
            The generated Script.
        """
        script = generate_script(self.project, self.config, self.output_dir)
        self.project.script = script
        self.project.update_status("script_generated")
        return script

    def generate_scene_descriptions(self) -> List[SceneDescription]:
        """Generate scene descriptions for the project.

        Returns:
            The generated list of SceneDescriptions.
        """
        scene_descriptions = generate_scenes(self.project, self.config, self.output_dir)
        self.project.scenes = scene_descriptions
        self.project.update_status("scene_descriptions_generated")
        return scene_descriptions

    def run_pipeline(self) -> Dict[str, Any]:
        """Run the full screenplay generation pipeline.

        Returns:
            Dictionary with results from each stage.
        """
        results = {}
        results["beat_sheet"] = self.generate_beat_sheet()
        results["characters"] = self.generate_characters()
        results["script"] = self.generate_script()
        results["scene_descriptions"] = self.generate_scene_descriptions()
        self.project.update_status("pipeline_complete")
        return results

    def save_project(self, path: Optional[Path] = None) -> None:
        """Save the project to a JSON file.

        Args:
            path: Path to save to. Defaults to output_dir/project.json.
        """
        if path is None:
            path = self.output_dir / "project.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.project.to_json(indent=2))

    @classmethod
    def load_project(cls, path: Path) -> Project:
        """Load a project from a JSON file.

        Args:
            path: Path to load from.

        Returns:
            The loaded Project.
        """
        data = json.loads(path.read_text())
        return Project(**data)
