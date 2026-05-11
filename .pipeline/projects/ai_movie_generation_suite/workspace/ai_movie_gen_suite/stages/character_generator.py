"""Character Generator — Save-the-Cat character archetypes.

Generates character profiles based on Save-the-Cat archetypes and story context.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ai_movie_gen_suite.models import Character, CharacterRegistry, CharacterRole


# ── Default archetype templates ──────────────────────────────────────────────

ARCHETYPE_TEMPLATES: Dict[str, Dict[str, str]] = {
    "protagonist": {
        "physical_description": "The protagonist's physical appearance should reflect their inner journey.",
        "personality_traits": ["determined", "flawed", "relatable"],
        "voice_notes": "Distinctive speech pattern that sets them apart.",
        "costume_notes": "Clothing that evolves with their character arc.",
        "visual_anchor": "A distinctive visual element that identifies them instantly.",
        "backstory": "A past event that shaped their core wound or desire.",
        "arc_summary": "From [initial state] to [final state].",
    },
    "antagonist": {
        "physical_description": "Physically imposing or subtly menacing presence.",
        "personality_traits": ["ruthless", "calculating", "charismatic"],
        "voice_notes": "Cold, measured, or unnervingly calm.",
        "costume_notes": "Sharp, dark, or authoritative clothing.",
        "visual_anchor": "A signature prop or visual motif.",
        "backstory": "A motivation that makes them sympathetic despite their actions.",
        "arc_summary": "Their plan threatens the protagonist's world.",
    },
    "mentor": {
        "physical_description": "Weathered, experienced, wise appearance.",
        "personality_traits": ["wise", "patient", "eccentric"],
        "voice_notes": "Warm, gravelly, or scholarly tone.",
        "costume_notes": "Practical, worn clothing suggesting experience.",
        "visual_anchor": "A distinctive accessory or mannerism.",
        "backstory": "A past failure that drives their desire to guide the protagonist.",
        "arc_summary": "Passes the torch to the protagonist.",
    },
    "ally": {
        "physical_description": "Approachable, friendly appearance.",
        "personality_traits": ["loyal", "humorous", "resourceful"],
        "voice_notes": "Casual, warm, or energetic.",
        "costume_notes": "Casual, practical clothing.",
        "visual_anchor": "A distinctive style or accessory.",
        "backstory": "A shared history or bond with the protagonist.",
        "arc_summary": "Supports the protagonist through the journey.",
    },
    "sidekick": {
        "physical_description": "Smaller, less imposing than the protagonist.",
        "personality_traits": ["eager", "comic relief", "devoted"],
        "voice_notes": "Quick, nervous, or enthusiastic.",
        "costume_notes": "Colorful or distinctive clothing.",
        "visual_anchor": "A quirky habit or prop.",
        "backstory": "Admires the protagonist and wants to prove themselves.",
        "arc_summary": "Grows from eager follower to independent hero.",
    },
    "deus_ex_machina": {
        "physical_description": "Unexpected, almost surreal appearance.",
        "personality_traits": ["mysterious", "powerful", "enigmatic"],
        "voice_notes": "Authoritative, otherworldly, or cryptic.",
        "costume_notes": "Unusual, striking clothing.",
        "visual_anchor": "A supernatural or technological element.",
        "backstory": "Revealed backstory that explains their power.",
        "arc_summary": "Appears at the climax to resolve the conflict.",
    },
    "supporting": {
        "physical_description": "Distinctive but not overwhelming.",
        "personality_traits": ["memorable", "functional", "distinct"],
        "voice_notes": "Clear, purposeful speech.",
        "costume_notes": "Clothing appropriate to their role.",
        "visual_anchor": "A distinctive feature.",
        "backstory": "Brief backstory that supports the main plot.",
        "arc_summary": "Supports the protagonist's journey.",
    },
}


class CharacterGenerator:
    """Generates character profiles for a screenplay."""

    def __init__(self, logline: str, genre: str, tone: str = ""):
        self.logline = logline
        self.genre = genre
        self.tone = tone

    def generate_characters(self, roles: Optional[List[str]] = None) -> CharacterRegistry:
        """Generate characters for standard Save-the-Cat roles.

        Args:
            roles: List of role names to generate. Defaults to all archetypes.

        Returns:
            CharacterRegistry with generated characters.
        """
        registry = CharacterRegistry()

        if roles is None:
            roles = ["protagonist", "antagonist", "mentor", "ally", "sidekick"]

        for i, role_name in enumerate(roles, start=1):
            archetype = ARCHETYPE_TEMPLATES.get(role_name, ARCHETYPE_TEMPLATES["supporting"])

            character = Character(
                name=f"{role_name.title()} {i}",
                role=CharacterRole(role_name),
                physical_description=archetype["physical_description"],
                personality_traits=archetype["personality_traits"],
                voice_notes=archetype["voice_notes"],
                costume_notes=archetype["costume_notes"],
                visual_anchor=archetype["visual_anchor"],
                backstory=archetype["backstory"],
                arc_summary=archetype["arc_summary"],
            )
            registry.add_character(character)

        return registry

    def generate_custom_character(
        self,
        name: str,
        role: CharacterRole,
        physical_description: str,
        personality_traits: Optional[List[str]] = None,
        voice_notes: str = "",
        costume_notes: str = "",
        visual_anchor: str = "",
        backstory: str = "",
        arc_summary: str = "",
    ) -> Character:
        """Generate a custom character profile."""
        return Character(
            name=name,
            role=role,
            physical_description=physical_description,
            personality_traits=personality_traits or [],
            voice_notes=voice_notes,
            costume_notes=costume_notes,
            visual_anchor=visual_anchor,
            backstory=backstory,
            arc_summary=arc_summary,
        )

    def generate_with_llm(self, llm_client=None, prompt_template: str = "") -> CharacterRegistry:
        """Generate characters using an LLM (optional, for richer content).

        Args:
            llm_client: An LLM client with a .generate() method.
            prompt_template: Jinja2 template for the character generation prompt.

        Returns:
            CharacterRegistry with LLM-generated content.
        """
        if llm_client is None:
            return self.generate_characters()

        prompt = self._build_llm_prompt(prompt_template)
        response = llm_client.generate(prompt)
        return self._parse_llm_response(response)

    def _build_llm_prompt(self, template: str = "") -> str:
        """Build the prompt for LLM character generation."""
        if template:
            return template.format(
                logline=self.logline,
                genre=self.genre,
                tone=self.tone,
            )

        return (
            f"Generate character profiles for a {self.genre} screenplay.\n\n"
            f"Logline: {self.logline}\n"
            f"Tone: {self.tone or 'Not specified'}\n\n"
            f"Generate characters for these roles:\n"
            f"- Protagonist\n"
            f"- Antagonist\n"
            f"- Mentor\n"
            f"- Ally\n"
            f"- Sidekick\n\n"
            f"For each character include:\n"
            f"- Name\n"
            f"- Physical description\n"
            f"- Personality traits\n"
            f"- Voice notes\n"
            f"- Costume notes\n"
            f"- Visual anchor\n"
            f"- Backstory\n"
            f"- Arc summary\n"
        )

    def _parse_llm_response(self, response: str) -> CharacterRegistry:
        """Parse LLM response into a CharacterRegistry."""
        registry = CharacterRegistry()

        # Simple parsing: split by character blocks
        current_char = None
        current_role = None

        for line in response.split("\n"):
            line = line.strip()
            if line.lower().startswith(("protagonist", "antagonist", "mentor", "ally", "sidekick", "deus_ex_machina", "supporting")):
                if current_char:
                    registry.add_character(current_char)
                current_role = CharacterRole(line.lower().rstrip(":"))
                current_char = Character(
                    name="",
                    role=current_role,
                    physical_description="",
                    personality_traits=[],
                    voice_notes="",
                    costume_notes="",
                    visual_anchor="",
                    backstory="",
                    arc_summary="",
                )
            elif current_char and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                if key == "name":
                    current_char.name = value
                elif key == "physical description":
                    current_char.physical_description = value
                elif key == "personality traits":
                    current_char.personality_traits = [t.strip() for t in value.split(",")]
                elif key == "voice notes":
                    current_char.voice_notes = value
                elif key == "costume notes":
                    current_char.costume_notes = value
                elif key == "visual anchor":
                    current_char.visual_anchor = value
                elif key == "backstory":
                    current_char.backstory = value
                elif key == "arc summary":
                    current_char.arc_summary = value

        if current_char:
            registry.add_character(current_char)

        return registry
