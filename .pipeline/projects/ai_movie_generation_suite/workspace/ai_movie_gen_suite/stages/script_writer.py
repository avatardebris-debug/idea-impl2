"""Script Writer — Converts beat sheet into a full screenplay.

Generates scene-by-scene screenplay content from the beat sheet and character registry.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    DialogueLine,
    Script,
    Scene,
)


class ScriptWriter:
    """Writes a screenplay from a beat sheet and character registry."""

    def __init__(
        self,
        title: str,
        logline: str,
        genre: str,
        beat_sheet: Optional[BeatSheet] = None,
        character_registry: Optional[CharacterRegistry] = None,
    ):
        self.title = title
        self.logline = logline
        self.genre = genre
        self.beat_sheet = beat_sheet
        self.character_registry = character_registry

    def write_script(self) -> Script:
        """Generate a full screenplay from the beat sheet.

        For MVP, creates a structured outline with scene headings and action lines.
        Each beat maps to one or more scenes.
        """
        script = Script(title=self.title, logline=self.logline, genre=self.genre)

        if self.beat_sheet is None:
            # Create a minimal script with placeholder scenes
            script.add_scene(self._create_placeholder_scene(1))
            return script

        scene_counter = 1
        for beat in self.beat_sheet.beats:
            # Each beat generates 1-3 scenes depending on complexity
            num_scenes = self._estimate_scenes_for_beat(beat)

            for j in range(num_scenes):
                scene = self._create_scene_from_beat(beat, scene_counter)
                script.add_scene(scene)
                scene_counter += 1

        return script

    def _estimate_scenes_for_beat(self, beat) -> int:
        """Estimate how many scenes a beat should generate.
        
        For the MVP, each beat maps to exactly one scene.
        """
        return 1

    def _create_placeholder_scene(self, scene_num: int) -> Scene:
        """Create a placeholder scene for MVP."""
        return Scene(
            scene_id=f"SC-{scene_num:03d}",
            scene_heading=f"INT. PLACEHOLDER - DAY",
            action=f"[Placeholder scene {scene_num} — to be filled by the screenplay writer]",
            characters_present=[],
            dialogue_lines=[],
            estimated_page_range=f"{scene_num}-{scene_num}",
        )

    def _create_scene_from_beat(self, beat, scene_num: int) -> Scene:
        """Create a scene from a beat."""
        # Determine scene heading based on beat phase
        if beat.phase:
            location_type = "INT" if beat.phase.value == "setup" else "EXT"
        else:
            location_type = "INT"

        scene = Scene(
            scene_id=f"SC-{scene_num:03d}",
            scene_heading=f"{location_type}. {beat.beat_name.upper().replace(' ', '_')} - DAY",
            action=f"[Scene based on beat: {beat.beat_name} — {beat.summary}]",
            characters_present=beat.characters_involved or [],
            dialogue_lines=[],
            estimated_page_range=beat.estimated_page_range,
            beat_ref=beat.beat_name,
        )

        # Add placeholder dialogue if characters are involved
        if self.character_registry:
            for char in self.character_registry.characters[:2]:
                scene.dialogue_lines.append(
                    DialogueLine(
                        character_name=char.name,
                        character_id=char.id,
                        text=f"[Dialogue for {char.name} in {beat.beat_name}]",
                    )
                )

        return scene

    def write_with_llm(self, llm_client=None, prompt_template: str = "") -> Script:
        """Write the script using an LLM (optional, for richer content).

        Args:
            llm_client: An LLM client with a .generate() method.
            prompt_template: Jinja2 template for the script writing prompt.

        Returns:
            Script with LLM-generated content.
        """
        if llm_client is None:
            return self.write_script()

        prompt = self._build_llm_prompt(prompt_template)
        response = llm_client.generate(prompt)
        return self._parse_llm_response(response)

    def _build_llm_prompt(self, template: str = "") -> str:
        """Build the prompt for LLM script writing."""
        if template:
            return template.format(
                title=self.title,
                logline=self.logline,
                genre=self.genre,
                beat_sheet=self.beat_sheet.model_dump() if self.beat_sheet else {},
                characters=self.character_registry.model_dump() if self.character_registry else {},
            )

        prompt = (
            f"Write a screenplay for a {self.genre} film.\n\n"
            f"Title: {self.title}\n"
            f"Logline: {self.logline}\n\n"
        )

        if self.beat_sheet:
            prompt += "Beat Sheet:\n"
            for beat in self.beat_sheet.beats:
                prompt += f"  {beat.beat_number}. {beat.beat_name}: {beat.summary}\n"

        if self.character_registry:
            prompt += "\nCharacters:\n"
            for char in self.character_registry.characters:
                prompt += f"  - {char.name} ({char.role.value})\n"

        prompt += "\nWrite the full screenplay in standard screenplay format."
        return prompt

    def _parse_llm_response(self, response: str) -> Script:
        """Parse LLM response into a Script."""
        script = Script(title=self.title, logline=self.logline, genre=self.genre)

        # Simple parsing: split by scene headings
        current_scene = None
        for line in response.split("\n"):
            line = line.strip()
            if line.upper().startswith(("INT.", "EXT.", "INT/EXT.")):
                if current_scene:
                    script.add_scene(current_scene)
                scene_id = f"SC-{len(script.scenes) + 1:03d}"
                current_scene = Scene(
                    scene_id=scene_id,
                    scene_heading=line,
                    action="",
                    characters_present=[],
                    dialogue_lines=[],
                )
            elif current_scene:
                if line.startswith("(") and ")" in line:
                    # Parenthetical
                    pass
                elif line.isupper() and not line.startswith("("):
                    # Character name
                    pass
                else:
                    # Action or dialogue
                    if current_scene.action:
                        current_scene.action += "\n" + line
                    else:
                        current_scene.action = line

        if current_scene:
            script.add_scene(current_scene)

        return script
