"""Scene description engine — generates detailed scene descriptions for characters.

Analyzes scenes and character information to produce rich, context-aware scene
descriptions that help maintain character consistency across different scenes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from ai_movie_gen_suite.models import Character, CharacterRegistry, Scene, Script

logger = logging.getLogger(__name__)


@dataclass
class SceneDescription:
    """A detailed description of a character in a scene.

    Fields:
        scene_id: The scene identifier.
        character_id: The character identifier.
        character_name: The character's name.
        scene_context: The scene's action/context.
        character_role: The character's role in the scene.
        emotional_state: The character's emotional state in the scene.
        key_interactions: Key interactions with other characters.
        visual_cues: Visual cues for rendering.
        dialogue_context: Any dialogue context for the character.
    """

    scene_id: str
    character_id: str
    character_name: str
    scene_context: str
    character_role: str
    emotional_state: str
    key_interactions: List[str]
    visual_cues: List[str]
    dialogue_context: str


class SceneDescriptionEngine:
    """Generates detailed scene descriptions for characters.

    Analyzes scenes and character information to produce rich, context-aware
    scene descriptions that help maintain character consistency across different
    scenes.

    Args:
        registry: Character registry with character information.
    """

    def __init__(self, registry: CharacterRegistry):
        self.registry = registry

    def describe_scene(
        self,
        scene: Scene,
    ) -> List[SceneDescription]:
        """Generate scene descriptions for all characters in a scene.

        Args:
            scene: The scene to describe.

        Returns:
            List of SceneDescription objects for each character in the scene.
        """
        present_characters = self._detect_present_characters(scene)
        descriptions = []

        for char_id in present_characters:
            character = self.registry.get_character(char_id)
            if not character:
                logger.warning("Character '%s' not found in registry", char_id)
                continue

            description = self._generate_scene_description(scene, character)
            descriptions.append(description)

        return descriptions

    def describe_script(
        self,
        script: Script,
    ) -> Dict[str, List[SceneDescription]]:
        """Generate scene descriptions for all scenes in a script.

        Args:
            script: The screenplay to describe.

        Returns:
            Dictionary mapping scene_id → list of SceneDescription objects.
        """
        descriptions: Dict[str, List[SceneDescription]] = {}

        for scene in script.scenes:
            scene_descs = self.describe_scene(scene)
            descriptions[scene.scene_id] = scene_descs

        return descriptions

    def _detect_present_characters(
        self,
        scene: Scene,
    ) -> List[str]:
        """Detect which characters are present in a scene.

        Uses keyword matching: if a character's name appears in the scene
        action, that character is considered present.

        Args:
            scene: The scene to analyze.

        Returns:
            List of character IDs present in the scene.
        """
        present: List[str] = []
        scene_text = scene.action.lower()

        for char_id, character in self.registry.characters.items():
            name = character.name.lower()
            if name in scene_text:
                present.append(char_id)

        return present

    def _generate_scene_description(
        self,
        scene: Scene,
        character: Character,
    ) -> SceneDescription:
        """Generate a detailed scene description for a character.

        Args:
            scene: The scene to describe.
            character: The character to describe.

        Returns:
            SceneDescription object with detailed information.
        """
        # Determine character role in scene
        character_role = self._determine_character_role(scene, character)

        # Determine emotional state
        emotional_state = self._determine_emotional_state(scene, character)

        # Identify key interactions
        key_interactions = self._identify_key_interactions(scene, character)

        # Identify visual cues
        visual_cues = self._identify_visual_cues(scene, character)

        # Extract dialogue context
        dialogue_context = self._extract_dialogue_context(scene, character)

        return SceneDescription(
            scene_id=scene.scene_id,
            character_id=character.id,
            character_name=character.name,
            scene_context=scene.action,
            character_role=character_role,
            emotional_state=emotional_state,
            key_interactions=key_interactions,
            visual_cues=visual_cues,
            dialogue_context=dialogue_context,
        )

    def _determine_character_role(
        self,
        scene: Scene,
        character: Character,
    ) -> str:
        """Determine the character's role in the scene.

        Args:
            scene: The scene to analyze.
            character: The character to analyze.

        Returns:
            String describing the character's role in the scene.
        """
        scene_text = scene.action.lower()
        name = character.name.lower()

        # Check for specific role indicators
        if "fight" in scene_text and name in scene_text:
            return "combatant"
        elif "talk" in scene_text and name in scene_text:
            return "speaker"
        elif "watch" in scene_text and name in scene_text:
            return "observer"
        elif "run" in scene_text and name in scene_text:
            return "pursuer"
        elif "climb" in scene_text and name in scene_text:
            return "climber"
        elif "enter" in scene_text and name in scene_text:
            return "entrant"
        elif "leave" in scene_text and name in scene_text:
            return "leaver"
        else:
            return character.role

    def _determine_emotional_state(
        self,
        scene: Scene,
        character: Character,
    ) -> str:
        """Determine the character's emotional state in the scene.

        Args:
            scene: The scene to analyze.
            character: The character to analyze.

        Returns:
            String describing the character's emotional state.
        """
        scene_text = scene.action.lower()
        name = character.name.lower()

        # Check for emotional indicators
        if "angry" in scene_text or "furious" in scene_text:
            return "angry"
        elif "happy" in scene_text or "excited" in scene_text:
            return "happy"
        elif "scared" in scene_text or "afraid" in scene_text:
            return "scared"
        elif "sad" in scene_text or "depressed" in scene_text:
            return "sad"
        elif "determined" in scene_text or "resolute" in scene_text:
            return "determined"
        elif "confused" in scene_text or "lost" in scene_text:
            return "confused"
        else:
            return "neutral"

    def _identify_key_interactions(
        self,
        scene: Scene,
        character: Character,
    ) -> List[str]:
        """Identify key interactions for the character in the scene.

        Args:
            scene: The scene to analyze.
            character: The character to analyze.

        Returns:
            List of interaction descriptions.
        """
        interactions: List[str] = []
        scene_text = scene.action.lower()
        name = character.name.lower()

        # Check for interactions with other characters
        for other_id, other_char in self.registry.characters.items():
            if other_id == character.id:
                continue

            other_name = other_char.name.lower()
            if other_name in scene_text:
                # Determine type of interaction
                if "fight" in scene_text or "attack" in scene_text:
                    interactions.append(f"fighting with {other_char.name}")
                elif "talk" in scene_text or "speak" in scene_text:
                    interactions.append(f"talking to {other_char.name}")
                elif "chase" in scene_text or "pursue" in scene_text:
                    interactions.append(f"chasing {other_char.name}")
                elif "help" in scene_text or "assist" in scene_text:
                    interactions.append(f"helping {other_char.name}")
                else:
                    interactions.append(f"interacting with {other_char.name}")

        return interactions

    def _identify_visual_cues(
        self,
        scene: Scene,
        character: Character,
    ) -> List[str]:
        """Identify visual cues for the character in the scene.

        Args:
            scene: The scene to analyze.
            character: The character to analyze.

        Returns:
            List of visual cue descriptions.
        """
        cues: List[str] = []
        scene_text = scene.action.lower()
        name = character.name.lower()

        # Add character's visual anchor
        if character.visual_anchor:
            cues.append(character.visual_anchor)

        # Add costume notes
        if character.costume_notes:
            cues.append(character.costume_notes)

        # Add scene-specific visual cues
        if "dark" in scene_text or "night" in scene_text:
            cues.append("dark lighting")
        elif "bright" in scene_text or "day" in scene_text:
            cues.append("bright lighting")
        elif "rain" in scene_text:
            cues.append("wet")
        elif "snow" in scene_text:
            cues.append("snowy")
        elif "fire" in scene_text:
            cues.append("fire-lit")

        return cues

    def _extract_dialogue_context(
        self,
        scene: Scene,
        character: Character,
    ) -> str:
        """Extract dialogue context for the character in the scene.

        Args:
            scene: The scene to analyze.
            character: The character to analyze.

        Returns:
            String describing the dialogue context.
        """
        scene_text = scene.action.lower()
        name = character.name.lower()

        # Check for dialogue indicators
        if "says" in scene_text or "speaks" in scene_text:
            return f"{character.name} speaks in this scene"
        elif "asks" in scene_text:
            return f"{character.name} asks a question"
        elif "yells" in scene_text or "shouts" in scene_text:
            return f"{character.name} yells"
        elif "whispers" in scene_text:
            return f"{character.name} whispers"
        else:
            return ""
