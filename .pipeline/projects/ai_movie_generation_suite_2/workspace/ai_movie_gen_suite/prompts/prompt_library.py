"""Prompt templates for the AI Movie Generation Suite.

Provides a library of reusable prompt templates for each pipeline stage.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptTemplate:
    """A reusable prompt template with variable substitution.

    Attributes:
        name: Template name.
        template: The template string with {variable} placeholders.
        description: Human-readable description.
    """

    def __init__(self, name: str, template: str, description: str = ""):
        """Initialize the prompt template.

        Args:
            name: Template name.
            template: The template string with {variable} placeholders.
            description: Human-readable description.
        """
        self.name = name
        self.template = template
        self.description = description

    def render(self, **kwargs: Any) -> str:
        """Render the template with the given variables.

        Args:
            **kwargs: Variables to substitute into the template.

        Returns:
            The rendered template string.

        Raises:
            KeyError: If a required variable is missing.
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing variable in template '{self.name}': {e}") from e

    def __str__(self) -> str:
        """Return the template name."""
        return self.name


class PromptLibrary:
    """Library of prompt templates for the pipeline.

    Provides access to all prompt templates used in the movie generation pipeline.
    """

    def __init__(self):
        """Initialize the prompt library with all templates."""
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_templates()
        self._register_additional_templates()

    def _register_templates(self) -> None:
        """Register all prompt templates."""
        self._templates = {
            "beat_generator": PromptTemplate(
                name="beat_generator",
                description="Generates beats for a scene",
                template=(
                    "You are an expert screenwriter specializing in {genre} films.\n\n"
                    "Given the following scene information, generate detailed beats for the scene.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Scene Description: {description}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "For each beat, provide:\n"
                    "- beat_number: The beat number (integer)\n"
                    "- action: The action taking place\n"
                    "- dialogue: Any dialogue (or null if none)\n"
                    "- emotion: The emotional tone of the beat\n"
                    "- camera_directions: Camera directions for the beat\n\n"
                    "Return a JSON object with a 'beats' array containing all beats.\n"
                    "Each beat should be a JSON object with the fields listed above.\n"
                    "Ensure the beats flow logically and build tension appropriately.\n"
                    "Include at least 3 beats and no more than 8 beats.\n"
                ),
            ),
            "character_generator": PromptTemplate(
                name="character_generator",
                description="Generates character profiles",
                template=(
                    "You are an expert character developer for {genre} films.\n\n"
                    "Given the following script information, generate detailed character profiles.\n\n"
                    "Script Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Logline: {logline}\n\n"
                    "For each character, provide:\n"
                    "- name: Character name\n"
                    "- age: Character age (or null if unknown)\n"
                    "- occupation: Character occupation\n"
                    "- personality: Personality traits (array of strings)\n"
                    "- backstory: Character backstory\n"
                    "- motivation: What drives the character\n"
                    "- arc: Character development arc\n"
                    "- voice: Speaking style and mannerisms\n"
                    "- appearance: Physical description\n\n"
                    "Return a JSON object with a 'characters' array containing all characters.\n"
                    "Include at least 3 characters and no more than 10 characters.\n"
                    "Ensure characters have distinct personalities and motivations.\n"
                ),
            ),
            "script_generator": PromptTemplate(
                name="script_generator",
                description="Generates script content",
                template=(
                    "You are an expert screenwriter specializing in {genre} films.\n\n"
                    "Given the following script information, generate a detailed script.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Logline: {logline}\n"
                    "Characters: {characters}\n\n"
                    "Generate a script with the following structure:\n"
                    "- title: Script title\n"
                    "- logline: One-sentence summary\n"
                    "- genre: Film genre\n"
                    "- tone: Overall tone\n"
                    "- scenes: Array of scene objects\n"
                    "Each scene should have:\n"
                    "- number: Scene number (integer)\n"
                    "- location: Scene location\n"
                    "- description: Scene description\n"
                    "- dialogue: Array of dialogue objects\n"
                    "Each dialogue should have:\n"
                    "- character: Character name\n"
                    "- text: Dialogue text\n"
                    "- emotion: Emotional tone\n\n"
                    "Ensure the script has a clear beginning, middle, and end.\n"
                    "Include at least 5 scenes and no more than 20 scenes.\n"
                    "Make the dialogue natural and engaging.\n"
                ),
            ),
            "scene_generator": PromptTemplate(
                name="scene_generator",
                description="Generates scene details",
                template=(
                    "You are an expert director specializing in {genre} films.\n\n"
                    "Given the following scene information, generate detailed scene directions.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Scene Description: {description}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "For this scene, provide:\n"
                    "- scene_number: The scene number (integer)\n"
                    "- location: Scene location\n"
                    "- visual_description: Detailed visual description of the scene\n"
                    "- camera_directions: Camera directions and movements\n"
                    "- lighting: Lighting design and mood\n"
                    "- color_palette: Color palette for the scene\n"
                    "- mood: Overall mood and atmosphere\n"
                    "- props_and_set_design: Props and set design details\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific and detailed in your descriptions.\n"
                    "Consider the genre and tone when making creative choices.\n"
                ),
            ),
            "scene_description": PromptTemplate(
                name="scene_description",
                description="Generates scene descriptions",
                template=(
                    "You are an expert cinematographer specializing in {genre} films.\n\n"
                    "Given the following scene information, generate a detailed scene description.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Scene Description: {description}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "Provide a detailed scene description including:\n"
                    "- scene_number: The scene number (integer)\n"
                    "- location: Scene location\n"
                    "- visual_description: Detailed visual description\n"
                    "- camera_directions: Camera directions\n"
                    "- lighting: Lighting design\n"
                    "- color_palette: Color palette\n"
                    "- mood: Overall mood\n"
                    "- props_and_set_design: Props and set design\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific and detailed in your descriptions.\n"
                    "Consider the genre and tone when making creative choices.\n"
                ),
            ),
        }

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name.

        Args:
            name: Template name.

        Returns:
            The PromptTemplate object, or None if not found.
        """
        return self._templates.get(name)

    def render_template(self, name: str, **kwargs: Any) -> str:
        """Render a template by name with the given variables.

        Args:
            name: Template name.
            **kwargs: Variables to substitute into the template.

        Returns:
            The rendered template string.

        Raises:
            KeyError: If the template is not found or a required variable is missing.
        """
        template = self.get_template(name)
        if not template:
            raise KeyError(f"Template '{name}' not found")
        return template.render(**kwargs)

    def list_templates(self) -> List[str]:
        """List all available template names.

        Returns:
            List of template names.
        """
        return list(self._templates.keys())

    def get_template_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get information about a template.

        Args:
            name: Template name.

        Returns:
            Dictionary with template information, or None if not found.
        """
        template = self.get_template(name)
        if not template:
            return None
        return {
            "name": template.name,
            "description": template.description,
            "template": template.template,
        }

    def _register_additional_templates(self) -> None:
        """Register additional prompt templates for later pipeline stages."""
        additional_templates = {
            "beat_sheet": PromptTemplate(
                name="beat_sheet",
                description="Generates beat sheet for a scene",
                template=(
                    "You are an expert screenwriter specializing in {genre} films.\n\n"
                    "Given the following scene information, generate a beat sheet for the scene.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Scene Description: {description}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "Provide a beat sheet with:\n"
                    "- scene_number: The scene number\n"
                    "- beats: Array of beat objects\n"
                    "Each beat should have:\n"
                    "- beat_number: The beat number (integer)\n"
                    "- action: The action taking place\n"
                    "- dialogue: Any dialogue (or null if none)\n"
                    "- emotion: The emotional tone of the beat\n"
                    "- camera_directions: Camera directions for the beat\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Ensure the beats flow logically and build tension appropriately.\n"
                    "Include at least 3 beats and no more than 8 beats.\n"
                ),
            ),
            "character_design": PromptTemplate(
                name="character_design",
                description="Generates character design profiles",
                template=(
                    "You are an expert character developer for {genre} films.\n\n"
                    "Given the following script information, generate detailed character design profiles.\n\n"
                    "Script Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Logline: {logline}\n\n"
                    "Provide character designs with:\n"
                    "- characters: Array of character objects\n"
                    "Each character should have:\n"
                    "- name: Character name\n"
                    "- age: Character age (or null if unknown)\n"
                    "- occupation: Character occupation\n"
                    "- personality: Personality traits (array of strings)\n"
                    "- backstory: Character backstory\n"
                    "- motivation: What drives the character\n"
                    "- arc: Character development arc\n"
                    "- voice: Speaking style and mannerisms\n"
                    "- appearance: Physical description\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Include at least 3 characters and no more than 10 characters.\n"
                    "Ensure characters have distinct personalities and motivations.\n"
                ),
            ),
            "concept_development": PromptTemplate(
                name="concept_development",
                description="Generates concept development document",
                template=(
                    "You are an expert film developer and producer.\n\n"
                    "Given the following movie concept, develop a comprehensive concept document.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Logline: {logline}\n\n"
                    "Provide a concept development document with:\n"
                    "- title: Project title\n"
                    "- logline: One-sentence summary\n"
                    "- genre: Film genre\n"
                    "- tone: Overall tone\n"
                    "- synopsis: A 2-3 paragraph synopsis\n"
                    "- themes: Key themes explored in the film (array)\n"
                    "- target_audience: Description of the target audience\n"
                    "- comparable_films: 2-3 comparable films (array)\n"
                    "- unique_selling_points: What makes this project unique (array)\n"
                    "- market_potential: Assessment of market potential\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific and professional in your analysis.\n"
                ),
            ),
            "summary_generator": PromptTemplate(
                name="summary_generator",
                description="Generates a project summary",
                template=(
                    "You are an expert film critic and storyteller.\n\n"
                    "Given the following movie project information, generate a comprehensive summary.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Logline: {logline}\n"
                    "Beat Sheet: {beat_sheet}\n"
                    "Characters: {characters}\n"
                    "Script Summary: {script_summary}\n\n"
                    "Provide a summary with:\n"
                    "- title: Project title\n"
                    "- synopsis: A compelling 2-3 paragraph synopsis\n"
                    "- themes: Key themes explored in the film (array)\n"
                    "- target_audience: Description of the target audience\n"
                    "- comparable_films: 2-3 comparable films (array)\n"
                    "- critical_notes: Notable strengths and unique elements\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Make the synopsis engaging and professional.\n"
                ),
            ),
            "music_generator": PromptTemplate(
                name="music_generator",
                description="Generates music composition plan",
                template=(
                    "You are an expert film composer specializing in {genre} films.\n\n"
                    "Given the following movie project information, create a music composition plan.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Synopsis: {synopsis}\n"
                    "Key Themes: {themes}\n\n"
                    "Provide a music plan with:\n"
                    "- title: Music composition title\n"
                    "- main_theme: Description of the main musical theme\n"
                    "- leitmotifs: List of character/scene leitmotifs (array)\n"
                    "- instrumentation: Recommended instruments and orchestration\n"
                    "- mood_by_act: Mood descriptions for each act (array)\n"
                    "- key_moments: Musical cues for key dramatic moments (array)\n"
                    "- tempo_range: Recommended tempo range (e.g., '60-120 BPM')\n"
                    "- genre_influences: Musical genre influences (array)\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific about how music supports the narrative.\n"
                ),
            ),
            "post_production_generator": PromptTemplate(
                name="post_production_generator",
                description="Generates post-production plan",
                template=(
                    "You are an expert film post-production supervisor.\n\n"
                    "Given the following movie project information, create a comprehensive post-production plan.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Scene Descriptions: {scene_descriptions}\n"
                    "Music Plan: {music_plan}\n\n"
                    "Provide a post-production plan with:\n"
                    "- title: Post-production plan title\n"
                    "- editing_plan: Detailed editing workflow and timeline\n"
                    "- visual_effects: VFX requirements and approach\n"
                    "- sound_design: Sound design and mixing plan\n"
                    "- color_grading: Color grading style and approach\n"
                    "- special_effects: Practical and digital effects needed\n"
                    "- delivery_specs: Technical delivery specifications\n"
                    "- timeline: Phase-by-phase timeline with milestones\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific about technical requirements and creative decisions.\n"
                ),
            ),
            "marketing_generator": PromptTemplate(
                name="marketing_generator",
                description="Generates marketing plan",
                template=(
                    "You are an expert film marketing strategist.\n\n"
                    "Given the following movie project information, create a comprehensive marketing plan.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Synopsis: {synopsis}\n"
                    "Target Audience: {target_audience}\n"
                    "Comparable Films: {comparable_films}\n\n"
                    "Provide a marketing plan with:\n"
                    "- title: Marketing plan title\n"
                    "- campaign_overview: High-level campaign strategy\n"
                    "- key_messages: Core messaging pillars (array)\n"
                    "- promotional_channels: Recommended promotional channels (array)\n"
                    "- social_media_strategy: Social media approach and content plan\n"
                    "- trailer_strategy: Trailer release strategy and key moments\n"
                    "- press_and_media: Press tour and media engagement plan\n"
                    "- budget_allocation: Suggested budget breakdown by channel\n"
                    "- timeline: Marketing timeline from pre-release to post-release\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific about tactics and measurable outcomes.\n"
                ),
            ),
            "summary": PromptTemplate(
                name="summary",
                description="Generates a concise summary of the movie project",
                template=(
                    "You are an expert film critic and storyteller.\n\n"
                    "Given the following movie project information, create a concise and compelling summary.\n\n"
                    "Title: {title}\n"
                    "Logline: {logline}\n"
                    "Genre: {genre}\n"
                    "Synopsis: {synopsis}\n\n"
                    "Provide a summary with:\n"
                    "- title: The movie title\n"
                    "- logline: A one-sentence hook\n"
                    "- summary: A 2-3 paragraph overview of the plot\n"
                    "- themes: Key themes explored in the film\n"
                    "- tone: The overall tone and mood\n"
                    "- target_audience: Who this movie is for\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific and engaging.\n"
                ),
            ),
            "music": PromptTemplate(
                name="music",
                description="Generates music and sound design for a scene",
                template=(
                    "You are an expert film composer and sound designer.\n\n"
                    "Given the following scene information, create music and sound design cues.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Mood: {mood}\n"
                    "Location: {location}\n"
                    "Genre: {genre}\n\n"
                    "Provide music and sound design with:\n"
                    "- scene_number: The scene number\n"
                    "- music_cue: Description of the music for this scene\n"
                    "- instruments: Recommended instruments\n"
                    "- tempo: Tempo description\n"
                    "- volume_level: Volume level (low, medium, high)\n"
                    "- sound_effects: List of sound effects\n"
                    "- audio_notes: Additional audio direction\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific about musical elements and sound design.\n"
                ),
            ),
            "post_production": PromptTemplate(
                name="post_production",
                description="Generates post-production notes for a scene",
                template=(
                    "You are an expert film post-production supervisor.\n\n"
                    "Given the following scene information, create post-production notes.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Mood: {mood}\n"
                    "Genre: {genre}\n"
                    "Action: {action}\n\n"
                    "Provide post-production notes with:\n"
                    "- scene_number: The scene number\n"
                    "- editing_notes: Editing direction for this scene\n"
                    "- vfx_requirements: VFX requirements\n"
                    "- color_grading: Color grading direction\n"
                    "- sound_design: Sound design notes\n"
                    "- special_effects: Special effects requirements\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific about technical requirements.\n"
                ),
            ),
            "marketing": PromptTemplate(
                name="marketing",
                description="Generates marketing materials for the movie",
                template=(
                    "You are an expert film marketing executive.\n\n"
                    "Given the following movie project information, create marketing materials.\n\n"
                    "Title: {title}\n"
                    "Logline: {logline}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "Provide marketing materials with:\n"
                    "- tagline: A catchy tagline for the movie\n"
                    "- poster_description: Description of the movie poster\n"
                    "- social_media: List of social media post ideas\n"
                    "- press_release: A press release summary\n"
                    "- campaign_strategy: Overall marketing campaign strategy\n"
                    "- key_messages: Key messages for the campaign\n"
                    "- budget_allocation: Suggested budget breakdown by channel\n"
                    "- timeline: Marketing timeline from pre-release to post-release\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific about tactics and measurable outcomes.\n"
                ),
            ),
            "distribution": PromptTemplate(
                name="distribution",
                description="Generates distribution plan",
                template=(
                    "You are an expert film distribution executive.\n\n"
                    "Given the following movie project information, create a comprehensive distribution plan.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Synopsis: {synopsis}\n"
                    "Target Audience: {target_audience}\n"
                    "Comparable Films: {comparable_films}\n\n"
                    "Provide a distribution plan with:\n"
                    "- title: Distribution plan title\n"
                    "- release_strategy: Theatrical, streaming, or hybrid strategy\n"
                    "- target_platforms: Recommended distribution platforms (array)\n"
                    "- release_windows: Optimal release timing and windows\n"
                    "- territorial_strategy: Territory-by-territory approach\n"
                    "- pricing_strategy: Pricing model for different platforms\n"
                    "- revenue_projections: Estimated revenue by channel\n"
                    "- partnership_opportunities: Potential distribution partnerships\n"
                    "- risk_analysis: Key risks and mitigation strategies\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific about market positioning and financial considerations.\n"
                ),
            ),
        }
        self._templates.update(additional_templates)

    def list_templates(self) -> List[str]:
        """List all available template names.

        Returns:
            List of template names.
        """
        return list(self._templates.keys())


# Global prompt library instance
prompt_library = PromptLibrary()
