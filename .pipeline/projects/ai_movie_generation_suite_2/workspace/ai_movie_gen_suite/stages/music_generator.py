"""Stage 6: Music Generator.

Takes the script and scene descriptions to generate music and sound design.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class MusicGenerator(BaseStageGenerator):
    """Generate music and sound design from script and scene data.

    Uses the MUSIC prompt template to create detailed music and sound
    design including themes, motifs, sound effects, and audio cues.
    """

    def execute(self, project: Project) -> Project:
        """Execute music generation on the project.

        Args:
            project: Project with script and scene_descriptions data.

        Returns:
            Updated project with music data populated.
        """
        script = project.script
        if not script:
            raise ValueError("Project must have script for music generation")

        scene_descriptions = project.scene_descriptions or []

        # Generate music themes
        themes = self._generate_music_themes(project)

        # Generate sound design
        sound_design = self._generate_sound_design(project, scene_descriptions)

        # Generate audio cues for each scene
        audio_cues = self._generate_audio_cues(project, scene_descriptions)

        project.music = {
            "themes": themes,
            "sound_design": sound_design,
            "audio_cues": audio_cues,
        }
        project.status = "music_generated"
        logger.info(f"Music generation complete: {len(themes)} themes, {len(audio_cues)} audio cues")
        return project

    def _generate_music_themes(self, project: Project) -> List[Dict[str, Any]]:
        """Generate music themes for the movie.

        Args:
            project: The project to generate themes for.

        Returns:
            List of music theme dictionaries.
        """
        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "music_themes",
            title=project.title,
            genre=project.genre,
            tone=project.tone,
            logline=project.logline,
            characters=self._format_characters_for_prompt(project),
        )
        messages = self._get_messages(prompt)
        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        return [
            {
                "theme_name": theme.get("theme_name", ""),
                "description": theme.get("description", ""),
                "instruments": theme.get("instruments", []),
                "tempo": theme.get("tempo", 0),
                "mood": theme.get("mood", ""),
                "scenes": theme.get("scenes", []),
            }
            for theme in data.get("themes", [])
        ]

    def _generate_sound_design(self, project: Project, scene_descriptions: List[Dict]) -> Dict[str, Any]:
        """Generate overall sound design for the movie.

        Args:
            project: The project to generate sound design for.
            scene_descriptions: List of scene descriptions.

        Returns:
            Sound design dictionary.
        """
        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "sound_design",
            title=project.title,
            genre=project.genre,
            tone=project.tone,
            logline=project.logline,
            num_scenes=len(scene_descriptions),
        )
        messages = self._get_messages(prompt)
        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        return {
            "overall_style": data.get("overall_style", ""),
            "ambient_sounds": data.get("ambient_sounds", []),
            "signature_sounds": data.get("signature_sounds", []),
            "silence_usage": data.get("silence_usage", ""),
            "audio_mixing_notes": data.get("audio_mixing_notes", ""),
        }

    def _generate_audio_cues(self, project: Project, scene_descriptions: List[Dict]) -> List[Dict[str, Any]]:
        """Generate audio cues for each scene.

        Args:
            project: The project to generate audio cues for.
            scene_descriptions: List of scene descriptions.

        Returns:
            List of audio cue dictionaries.
        """
        from ai_movie_gen_suite.prompts import prompt_library

        audio_cues = []

        for scene_desc in scene_descriptions:
            scene_num = scene_desc.get("scene_number", 0)
            location = scene_desc.get("location", "")
            visual_desc = scene_desc.get("visual_description", "")

            prompt = prompt_library.render_template(
                "audio_cues",
                scene_number=scene_num,
                location=location,
                visual_description=visual_desc,
                genre=project.genre,
                tone=project.tone,
            )
            messages = self._get_messages(prompt)
            response = self.client.generate(messages)
            data = self._parse_json_response(response.content)

            audio_cues.append({
                "scene_number": data.get("scene_number", scene_num),
                "background_music": data.get("background_music", ""),
                "sound_effects": data.get("sound_effects", []),
                "ambient_sounds": data.get("ambient_sounds", []),
                "music_cues": data.get("music_cues", []),
                "silence_moments": data.get("silence_moments", []),
            })

        return audio_cues

    def _format_characters_for_prompt(self, project: Project) -> str:
        """Format characters for prompt rendering.

        Args:
            project: The project with character data.

        Returns:
            Formatted character string.
        """
        characters = project.characters or []
        formatted = []
        for char in characters:
            name = char.get("name", "Unknown")
            personality = ", ".join(char.get("personality", []))
            formatted.append(f"- {name}: {personality}")
        return "\n".join(formatted) if formatted else "No characters defined"
