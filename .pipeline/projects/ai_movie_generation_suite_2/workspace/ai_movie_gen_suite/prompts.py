"""Prompt templates for the AI Movie Generation Suite.

Provides pre-built prompt templates for each stage of the movie generation pipeline.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """A reusable prompt template with variable substitution.

    Attributes:
        name: Template name identifier.
        template: The template string with {variable} placeholders.
        description: Description of what this template does.
        variables: List of required variable names.
    """

    name: str = Field(description="Template name identifier")
    template: str = Field(description="Template string with {variable} placeholders")
    description: str = Field(description="Description of what this template does")
    variables: List[str] = Field(default_factory=list, description="Required variable names")

    def render(self, **kwargs: Any) -> str:
        """Render the template with the given variables.

        Args:
            **kwargs: Variable values for substitution.

        Returns:
            Rendered template string.

        Raises:
            ValueError: If required variables are missing.
        """
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        return self.template.format(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to a dictionary."""
        return {
            "name": self.name,
            "template": self.template,
            "description": self.description,
            "variables": self.variables,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert template to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PromptTemplate:
        """Create template from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> PromptTemplate:
        """Create template from a JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class PromptLibrary:
    """Collection of prompt templates for the movie generation pipeline.

    Provides access to all pre-built templates for each stage.
    """

    # Stage 1: Concept Development
    CONCEPT_DEVELOPMENT = PromptTemplate(
        name="concept_development",
        template="""You are an expert film producer and creative director. Your task is to develop a compelling movie concept based on the following input.

Input: {input_prompt}

Requirements:
- The concept should be original and engaging
- Consider genre, tone, and target audience
- Think about visual style and cinematic potential
- Ensure the concept is feasible for AI video generation

Please provide your response in the following JSON format:
{{
    "title": "Movie title",
    "genre": "Primary genre",
    "logline": "A one-sentence summary of the movie",
    "synopsis": "A brief synopsis (2-3 paragraphs)",
    "visual_style": "Description of the visual style",
    "target_audience": "Target audience description",
    "key_themes": ["theme1", "theme2", "theme3"],
    "mood": "Overall mood/atmosphere",
    "feasibility_notes": "Notes on AI generation feasibility"
}}

Ensure all fields are filled and the JSON is valid.""",
        description="Develop a movie concept from a user prompt",
        variables=["input_prompt"],
    )

    # Stage 2: Beat Sheet (Save-the-Cat structure)
    BEAT_SHEET = PromptTemplate(
        name="beat_sheet",
        template="""You are an expert screenwriter and story structure specialist. Your task is to create a Save-the-Cat beat sheet for a movie based on the following concept.

Movie Concept:
- Title: {title}
- Genre: {genre}
- Logline: {logline}
- Synopsis: {synopsis}

Create a beat sheet with 15 beats following the Save-the-Cat structure:
1. Opening Image
2. Theme Stated
3. Set-up
4. Catalyst
5. Debate
6. Break into Two
7. B Story
8. Fun and Games
9. Midpoint
10. Bad Guys Close In
11. All Is Lost
12. Dark Night of the Soul
13. Break into Three
14. Finale
15. Final Image

Please provide your response in the following JSON format:
{{
    "beats": [
        {{
            "number": 1,
            "name": "Beat name",
            "description": "Detailed description of this beat",
            "scene_numbers": [1, 2]
        }}
    ]
}}

Ensure all 15 beats are filled and the JSON is valid.""",
        description="Create a Save-the-Cat beat sheet from a movie concept",
        variables=["title", "genre", "logline", "synopsis"],
    )

    # Stage 3: Character Design
    CHARACTER_DESIGN = PromptTemplate(
        name="character_design",
        template="""You are an expert character designer and concept artist. Your task is to create detailed character descriptions for a movie.

Movie Context:
- Title: {title}
- Genre: {genre}
- Synopsis: {synopsis}

Characters to design:
{characters}

For each character, provide:
- Physical appearance (height, build, hair, eyes, distinctive features)
- Clothing and style
- Personality traits
- Background and motivation
- Visual references for AI generation

Please provide your response in the following JSON format:
{{
    "characters": [
        {{
            "name": "Character name",
            "role": "Character role (protagonist, antagonist, etc.)",
            "physical_description": "Detailed physical appearance",
            "clothing": "Clothing and style description",
            "personality": "Personality traits",
            "background": "Character background",
            "visual_prompt": "Detailed visual prompt for AI image generation",
            "reference_images": ["description1", "description2"]
        }}
    ]
}}

Ensure all characters are distinct and well-described.""",
        description="Create detailed character designs",
        variables=["title", "genre", "synopsis", "characters"],
    )

    # Stage 4: Script Writing
    SCRIPT_WRITING = PromptTemplate(
        name="script_writing",
        template="""You are an expert screenwriter. Your task is to write a detailed script for a movie based on the following concept and beat sheet.

Movie Concept:
- Title: {title}
- Genre: {genre}
- Logline: {logline}

Beat Sheet:
{beats}

Characters:
{characters}

Requirements:
- Write a complete script with dialogue and action descriptions
- Include scene headings, action lines, character names, and dialogue
- Format the script in standard screenplay format
- Include {num_scenes} scenes
- Each scene should be detailed enough for AI video generation
- Include camera directions and visual descriptions

Please provide your response in the following JSON format:
{{
    "scenes": [
        {{
            "number": 1,
            "location": "Scene location",
            "description": "Detailed action description",
            "dialogue": [
                {{
                    "character": "character_name",
                    "dialogue": "Dialogue text",
                    "action": "Action description"
                }}
            ],
            "characters_present": ["character1", "character2"],
            "camera_direction": "Camera movement and framing",
            "visual_notes": "Visual details for AI generation",
            "duration_seconds": 30
        }}
    ]
}}

Ensure all scenes are properly formatted and the JSON is valid.""",
        description="Write a detailed script from a movie concept and beat sheet",
        variables=["title", "genre", "logline", "beats", "characters", "num_scenes"],
    )

    # Stage 5: Scene Description
    SCENE_DESCRIPTION = PromptTemplate(
        name="scene_description",
        template="""You are an expert cinematographer and storyboard artist. Your task is to create a detailed visual description for a specific scene.

Scene Details:
- Scene Number: {scene_number}
- Location: {location}
- Description: {description}
- Genre: {genre}
- Tone: {tone}

Provide a detailed visual description including:
- Camera angles and movements
- Lighting setup
- Color palette
- Composition and framing
- Mood and atmosphere
- Props and set design details

Please provide your response in the following JSON format:
{{
    "scene_number": {scene_number},
    "location": "{location}",
    "visual_description": "Detailed visual description",
    "camera_directions": "Camera angles and movements",
    "lighting": "Lighting setup description",
    "color_palette": "Color palette description",
    "mood": "Mood and atmosphere",
    "props_and_set_design": "Props and set design details"
}}

Ensure the description is detailed enough for AI video generation.""",
        description="Create detailed visual descriptions for scenes",
        variables=["scene_number", "location", "description", "genre", "tone"],
    )

    # Stage 6: Summary
    SUMMARY = PromptTemplate(
        name="summary",
        template="""You are an expert film critic and journalist. Your task is to create a concise summary of a movie based on the following information.

Movie Information:
- Title: {title}
- Logline: {logline}
- Genre: {genre}
- Synopsis: {synopsis}

Create a summary that includes:
- A compelling overview of the movie
- Key plot points without spoilers
- Main characters and their arcs
- Themes and messages
- Why audiences should watch it

Please provide your response in the following JSON format:
{{
    "title": "{title}",
    "logline": "{logline}",
    "genre": "{genre}",
    "summary": "Concise movie summary",
    "key_themes": ["theme1", "theme2"],
    "target_audience": "Target audience description",
    "comparable_films": ["Film 1", "Film 2"],
    "rating": "Rating (e.g., PG-13, R)"
}}

Ensure the summary is engaging and informative.""",
        description="Create a concise movie summary",
        variables=["title", "logline", "genre", "synopsis"],
    )

    # Stage 7: Music
    MUSIC = PromptTemplate(
        name="music",
        template="""You are an expert film composer and sound designer. Your task is to create music and sound design for a specific scene.

Scene Details:
- Scene Number: {scene_number}
- Location: {location}
- Mood: {mood}
- Genre: {genre}

Provide music and sound design including:
- Music cues (tempo, instrumentation, mood)
- Sound effects
- Audio direction
- Silence and pauses

Please provide your response in the following JSON format:
{{
    "scene_number": {scene_number},
    "music_cues": [
        {{
            "start_time": "0:00",
            "end_time": "0:30",
            "instrumentation": "Instruments used",
            "tempo": "Tempo description",
            "mood": "Mood of the music",
            "volume": "Volume level"
        }}
    ],
    "sound_effects": [
        {{
            "type": "Sound effect type",
            "description": "Description",
            "timing": "When it occurs"
        }}
    ],
    "audio_direction": "Overall audio direction"
}}

Ensure the music and sound design enhance the scene's mood and story.""",
        description="Create music and sound design for scenes",
        variables=["scene_number", "mood", "location", "genre"],
    )

    # Stage 8: Post-Production
    POST_PRODUCTION = PromptTemplate(
        name="post_production",
        template="""You are an expert film editor and post-production supervisor. Your task is to create post-production notes for a specific scene.

Scene Details:
- Scene Number: {scene_number}
- Location: {location}
- Mood: {mood}
- Genre: {genre}
- Action: {action}

Provide {action} notes including:
- Specific requirements
- Technical details
- Timeline estimates
- Quality checks

Please provide your response in the following JSON format:
{{
    "scene_number": {scene_number},
    "action": "{action}",
    "notes": "Detailed notes",
    "requirements": ["requirement1", "requirement2"],
    "timeline": "Estimated timeline",
    "quality_checks": ["check1", "check2"]
}}

Ensure the notes are specific and actionable.""",
        description="Create post-production notes for scenes",
        variables=["scene_number", "location", "mood", "genre", "action"],
    )

    # Stage 9: Marketing
    MARKETING = PromptTemplate(
        name="marketing",
        template="""You are an expert film marketing director. Your task is to create marketing materials for a movie.

Movie Information:
- Title: {title}
- Logline: {logline}
- Genre: {genre}
- Tone: {tone}

Create marketing materials including:
- Tagline
- Poster description
- Social media content
- Press release

Please provide your response in the following JSON format:
{{
    "tagline": "Compelling tagline",
    "poster_description": "Detailed poster description",
    "social_media": [
        {{
            "platform": "Platform name",
            "content": "Content description",
            "hashtags": ["hashtag1", "hashtag2"]
        }}
    ],
    "press_release": "Press release text"
}}

Ensure the marketing materials are engaging and appropriate for the target audience.""",
        description="Create marketing materials for a movie",
        variables=["title", "logline", "genre", "tone"],
    )

    # Stage 10: Distribution
    DISTRIBUTION = PromptTemplate(
        name="distribution",
        template="""You are an expert film distribution strategist. Your task is to create a distribution strategy for a movie.

Movie Information:
- Title: {title}
- Genre: {genre}
- Tone: {tone}
- Budget: {budget}

Create a distribution strategy including:
- Platform recommendations
- Release strategy
- Target audience
- Estimated budget breakdown

Please provide your response in the following JSON format:
{{
    "platforms": ["Platform 1", "Platform 2"],
    "release_strategy": "Release strategy description",
    "target_audience": "Target audience description",
    "estimated_budget": "Budget breakdown"
}}

Ensure the strategy is realistic and appropriate for the movie's genre and budget.""",
        description="Create a distribution strategy for a movie",
        variables=["title", "genre", "tone", "budget"],
    )

    def __init__(self) -> None:
        """Initialize the prompt library with all templates."""
        self._templates: Dict[str, PromptTemplate] = {
            template.name: template
            for template in [
                self.CONCEPT_DEVELOPMENT,
                self.BEAT_SHEET,
                self.CHARACTER_DESIGN,
                self.SCRIPT_WRITING,
                self.SCENE_DESCRIPTION,
                self.SUMMARY,
                self.MUSIC,
                self.POST_PRODUCTION,
                self.MARKETING,
                self.DISTRIBUTION,
            ]
        }

    def get_template(self, name: str) -> PromptTemplate:
        """Get a template by name.

        Args:
            name: Template name.

        Returns:
            The requested template.

        Raises:
            ValueError: If template not found.
        """
        template = self._templates.get(name)
        if template is None:
            available = ", ".join(self._templates.keys())
            raise ValueError(f"Template '{name}' not found. Available: {available}")
        return template

    def render_template(self, name: str, **kwargs: Any) -> str:
        """Render a template by name with the given variables.

        Args:
            name: Template name.
            **kwargs: Variable values for substitution.

        Returns:
            Rendered template string.
        """
        template = self.get_template(name)
        return template.render(**kwargs)

    def get_all_templates(self) -> Dict[str, PromptTemplate]:
        """Get all templates.

        Returns:
            Dictionary of all templates.
        """
        return self._templates.copy()

    def get_template_names(self) -> List[str]:
        """Get all template names.

        Returns:
            List of template names.
        """
        return list(self._templates.keys())


# Global instance
prompt_library = PromptLibrary()
