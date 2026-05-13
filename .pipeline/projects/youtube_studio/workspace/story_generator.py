"""
Story Generator Module

AI-powered story generation for different video formats:
- Short-form (TikTok/Shorts)
- Long-form informational
- Commercial scripts
- Save the Cat (beat-sheet narrative)
- Movie/feature-length outlines
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class VideoFormat(Enum):
    """Supported video story formats."""
    SHORT_FORM = "short_form"           # TikTok/Shorts (15-60 sec)
    LONG_FORM = "long_form"             # Educational/informational (10-30 min)
    COMMERCIAL = "commercial"           # Ad/promo (30-120 sec)
    SAVE_THE_CAT = "save_the_cat"       # Narrative beat-sheet
    MOVIE_OUTLINE = "movie_outline"     # Feature-length outline


class StoryTone(Enum):
    """Story tone/style."""
    COMEDIC = "comedic"
    DRAMATIC = "dramatic"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    CASUAL = "casual"
    PROFESSIONAL = "professional"


@dataclass
class StoryBeat:
    """A single beat/section in a story."""
    name: str
    description: str
    content: str
    duration_hint: str = ""  # e.g. "30 seconds", "2 minutes"
    notes: str = ""


@dataclass
class StoryResult:
    """Complete generated story."""
    title: str
    format: VideoFormat
    tone: StoryTone
    logline: str
    beats: List[StoryBeat]
    characters: List[Dict[str, str]] = field(default_factory=list)
    settings: List[str] = field(default_factory=list)
    estimated_duration: str = ""
    full_script: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "format": self.format.value,
            "tone": self.tone.value,
            "logline": self.logline,
            "beats": [{"name": b.name, "description": b.description,
                        "content": b.content, "duration_hint": b.duration_hint}
                       for b in self.beats],
            "characters": self.characters,
            "settings": self.settings,
            "estimated_duration": self.estimated_duration,
            "full_script": self.full_script,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ── Beat-sheet templates per format ──────────────────────────────────

_SAVE_THE_CAT_BEATS = [
    ("Opening Image", "A visual that sets the tone and shows the 'before' state."),
    ("Theme Stated", "A character hints at the lesson/theme of the story."),
    ("Set-Up", "Introduce the hero, their world, and what's missing."),
    ("Catalyst", "Something happens that changes the hero's world."),
    ("Debate", "The hero hesitates — should they act?"),
    ("Break into Two", "The hero commits and enters a new world/situation."),
    ("B Story", "A subplot (often love/friendship) that carries the theme."),
    ("Fun and Games", "The promise of the premise — the fun part."),
    ("Midpoint", "A false victory or false defeat raises the stakes."),
    ("Bad Guys Close In", "Opposition intensifies; internal doubts grow."),
    ("All Is Lost", "The hero hits rock bottom."),
    ("Dark Night of the Soul", "The hero processes the loss and finds inner truth."),
    ("Break into Three", "A new idea or solution emerges from the B story."),
    ("Finale", "The hero enacts the plan, battles opposition, transforms."),
    ("Final Image", "A visual that shows the 'after' — transformation complete."),
]

_SHORT_FORM_BEATS = [
    ("Hook", "Grab attention in the first 2 seconds."),
    ("Problem/Setup", "Present the relatable problem or question."),
    ("Payoff", "Deliver the answer, twist, or punchline."),
    ("CTA", "Call to action — follow, like, comment."),
]

_LONG_FORM_BEATS = [
    ("Hook", "Why should the viewer keep watching?"),
    ("Intro", "Introduce the topic and what the viewer will learn."),
    ("Context", "Background information and why this matters."),
    ("Main Point 1", "First major argument or lesson."),
    ("Main Point 2", "Second major argument or lesson."),
    ("Main Point 3", "Third major argument or lesson."),
    ("Deep Dive", "Go deeper on the most important aspect."),
    ("Counter-arguments", "Address objections or alternative views."),
    ("Summary", "Recap the key takeaways."),
    ("CTA / Outro", "Call to action and sign-off."),
]

_COMMERCIAL_BEATS = [
    ("Attention", "Immediate hook — visual or audio."),
    ("Problem", "Show the pain point the audience relates to."),
    ("Solution", "Introduce the product/service as the answer."),
    ("Proof", "Testimonials, stats, or demonstrations."),
    ("CTA", "Clear call to action with urgency."),
]

_MOVIE_OUTLINE_BEATS = [
    ("Act 1 — Setup", "Introduce characters, world, and the inciting incident."),
    ("Act 1 — First Turning Point", "The protagonist commits to the journey."),
    ("Act 2A — Rising Action", "Obstacles, allies, and tests."),
    ("Act 2 — Midpoint", "Major revelation or reversal."),
    ("Act 2B — Complications", "Stakes rise; antagonist gains ground."),
    ("Act 2 — Second Turning Point", "All seems lost; crisis moment."),
    ("Act 3 — Climax", "Final confrontation and resolution."),
    ("Act 3 — Resolution", "New normal; character arc complete."),
]

_BEAT_TEMPLATES = {
    VideoFormat.SHORT_FORM: _SHORT_FORM_BEATS,
    VideoFormat.LONG_FORM: _LONG_FORM_BEATS,
    VideoFormat.COMMERCIAL: _COMMERCIAL_BEATS,
    VideoFormat.SAVE_THE_CAT: _SAVE_THE_CAT_BEATS,
    VideoFormat.MOVIE_OUTLINE: _MOVIE_OUTLINE_BEATS,
}

_DURATION_HINTS = {
    VideoFormat.SHORT_FORM: "15-60 seconds",
    VideoFormat.LONG_FORM: "10-30 minutes",
    VideoFormat.COMMERCIAL: "30-120 seconds",
    VideoFormat.SAVE_THE_CAT: "5-15 minutes",
    VideoFormat.MOVIE_OUTLINE: "90-120 minutes",
}


class StoryGenerator:
    """Generate structured stories for various video formats.

    Uses beat-sheet templates to produce structured outlines. Each beat
    gets placeholder content that can be refined with an LLM or manually.
    """

    def __init__(self, llm_client=None):
        """Initialize. Optional LLM client for AI generation."""
        self.llm_client = llm_client

    def generate(
        self,
        topic: str,
        format: VideoFormat = VideoFormat.LONG_FORM,
        tone: StoryTone = StoryTone.EDUCATIONAL,
        characters: Optional[List[Dict[str, str]]] = None,
        settings: Optional[List[str]] = None,
    ) -> StoryResult:
        """Generate a story for the given topic and format.

        Args:
            topic: The subject/concept of the video.
            format: Video format to target.
            tone: Desired tone/style.
            characters: Optional character descriptions.
            settings: Optional setting descriptions.

        Returns:
            StoryResult with beats, logline, and full script.
        """
        beat_template = _BEAT_TEMPLATES[format]
        beats = self._build_beats(topic, beat_template, tone)
        logline = self._generate_logline(topic, format, tone)
        full_script = self._compile_script(beats)

        return StoryResult(
            title=self._generate_title(topic, format),
            format=format,
            tone=tone,
            logline=logline,
            beats=beats,
            characters=characters or [],
            settings=settings or [],
            estimated_duration=_DURATION_HINTS.get(format, "varies"),
            full_script=full_script,
        )

    def list_formats(self) -> List[Dict[str, str]]:
        """List all available story formats with descriptions."""
        return [
            {"format": f.value, "duration": _DURATION_HINTS[f],
             "beats": len(_BEAT_TEMPLATES[f])}
            for f in VideoFormat
        ]

    # ── Internal ─────────────────────────────────────────────────────

    def _build_beats(self, topic: str, template: list, tone: StoryTone) -> List[StoryBeat]:
        beats = []
        for name, desc in template:
            content = self._generate_beat_content(topic, name, desc, tone)
            beats.append(StoryBeat(
                name=name,
                description=desc,
                content=content,
            ))
        return beats

    def _generate_beat_content(self, topic: str, beat_name: str,
                                beat_desc: str, tone: StoryTone) -> str:
        """Generate content for a single beat. Uses LLM if available."""
        if self.llm_client:
            prompt = (
                f"Write the '{beat_name}' section of a {tone.value} video about: {topic}.\n"
                f"Beat purpose: {beat_desc}\n"
                f"Keep it concise and engaging."
            )
            try:
                return self.llm_client.generate(prompt)
            except Exception:
                pass  # Fall through to template

        # Template fallback
        return f"[{beat_name}] — {beat_desc}\nTopic: {topic}\nTone: {tone.value}"

    def _generate_logline(self, topic: str, fmt: VideoFormat, tone: StoryTone) -> str:
        return f"A {tone.value} {fmt.value.replace('_', ' ')} video exploring {topic}."

    def _generate_title(self, topic: str, fmt: VideoFormat) -> str:
        prefixes = {
            VideoFormat.SHORT_FORM: "Quick Take:",
            VideoFormat.LONG_FORM: "Deep Dive:",
            VideoFormat.COMMERCIAL: "Introducing:",
            VideoFormat.SAVE_THE_CAT: "The Story of",
            VideoFormat.MOVIE_OUTLINE: "Untitled:",
        }
        return f"{prefixes.get(fmt, '')} {topic}".strip()

    def _compile_script(self, beats: List[StoryBeat]) -> str:
        lines = []
        for i, beat in enumerate(beats, 1):
            lines.append(f"=== {beat.name} ===")
            lines.append(beat.content)
            lines.append("")
        return "\n".join(lines)
