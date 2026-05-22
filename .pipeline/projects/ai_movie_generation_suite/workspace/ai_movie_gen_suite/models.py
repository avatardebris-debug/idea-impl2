"""Core data models for the AI Movie Generation Suite."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class BeatPhase(str, Enum):
    """Save-the-Cat act phases."""
    SETUP = "setup"
    CONFRONTATION = "confrontation"
    RESOLUTION = "resolution"


class CharacterRole(str, Enum):
    """Standard character roles."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    MENTOR = "mentor"
    ALLY = "ally"
    SIDEKICK = "sidekick"
    DEUS_EX_MACHINA = "deus_ex_machina"
    SUPPORTING = "supporting"


# ── Beat Models ──────────────────────────────────────────────────────────────

SAVE_THE_CAT_BEATS = [
    "Opening Image",
    "Theme Stated",
    "Setup",
    "Catalyst",
    "Debate",
    "Break into Two",
    "B Story",
    "Fun and Games",
    "Midpoint",
    "Bad Guys Close In",
    "All Is Lost",
    "Dark Night of the Soul",
    "Break into Three",
    "Finale",
    "Final Image",
]


class Beat(BaseModel):
    """A single Save-the-Cat beat."""
    beat_name: str
    beat_number: int
    summary: str
    description: str = ""
    characters_involved: List[str] = Field(default_factory=list)
    estimated_page_range: Optional[str] = None
    phase: Optional[BeatPhase] = None
    scene_ids: List[str] = Field(default_factory=list)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        if self.phase is not None:
            d["phase"] = self.phase.value
        return d


class BeatSheet(BaseModel):
    """Collection of 15 Save-the-Cat beats."""
    title: str = "Untitled"
    logline: str
    genre: str
    beats: List[Beat] = Field(default_factory=list)

    def add_beat(self, beat: Beat) -> None:
        self.beats.append(beat)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["beats"] = [b.model_dump() for b in self.beats]
        return d


# ── Character Models ─────────────────────────────────────────────────────────

class Character(BaseModel):
    """A character in the screenplay."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    role: CharacterRole
    physical_description: str = ""
    personality_traits: List[str] = Field(default_factory=list)
    motivation: str = ""
    voice_notes: str = ""
    costume_notes: str = ""
    visual_anchor: str = ""
    backstory: str = ""
    arc_summary: str = ""

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["role"] = self.role.value
        return d


class CharacterRegistry(BaseModel):
    """Registry of all characters."""
    characters: List[Character] = Field(default_factory=list)

    def add_character(self, character: Character) -> None:
        self.characters.append(character)

    def get_by_id(self, char_id: str) -> Optional[Character]:
        for c in self.characters:
            if c.id == char_id:
                return c
        return None

    def get_by_name(self, name: str) -> Optional[Character]:
        for c in self.characters:
            if c.name.lower() == name.lower():
                return c
        return None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["characters"] = [c.model_dump() for c in self.characters]
        return d


# ── Scene / Script Models ────────────────────────────────────────────────────

class DialogueLine(BaseModel):
    """A single line of dialogue."""
    character_name: str
    character_id: str
    text: str
    parenthetical: Optional[str] = None
    delivery: Optional[str] = None  # e.g. "whispering", "shouting"


class Scene(BaseModel):
    """A single screenplay scene."""
    scene_id: str = Field(default_factory=lambda: f"SC-{uuid.uuid4().hex[:6].upper()}")
    scene_heading: str  # e.g. "INT. COFFEE SHOP - DAY"
    action: str
    characters_present: List[str] = Field(default_factory=list)
    dialogue_lines: List[DialogueLine] = Field(default_factory=list)
    estimated_page_range: Optional[str] = None
    beat_ref: Optional[str] = None  # references which beat this scene expands

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["dialogue_lines"] = [dl.model_dump() for dl in self.dialogue_lines]
        return d


class Script(BaseModel):
    """Full screenplay output."""
    title: str
    logline: str
    genre: str
    scenes: List[Scene] = Field(default_factory=list)

    def add_scene(self, scene: Scene) -> None:
        self.scenes.append(scene)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["scenes"] = [s.model_dump() for s in self.scenes]
        return d


# ── Scene Description Models ─────────────────────────────────────────────────

class SceneDescription(BaseModel):
    """Visual direction for a single scene."""
    scene_id: str
    setting: str = ""
    lighting: str = ""
    camera_notes: str = ""
    mood: str = ""
    action_beats: List[str] = Field(default_factory=list)
    visual_style: str = ""


class SceneDescriptionCollection(BaseModel):
    """All scene descriptions."""
    descriptions: Dict[str, SceneDescription] = Field(default_factory=dict)

    def add_description(self, scene_id: str, desc: SceneDescription) -> None:
        self.descriptions[scene_id] = desc

    def get_description(self, scene_id: str) -> Optional[SceneDescription]:
        return self.descriptions.get(scene_id)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["descriptions"] = {k: v.model_dump() for k, v in self.descriptions.items()}
        return d


# ── Project Model ────────────────────────────────────────────────────────────

class Project(BaseModel):
    """Top-level project container."""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    logline: str
    genre: str
    tone: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    beat_sheet: Optional[BeatSheet] = None
    character_registry: Optional[CharacterRegistry] = None
    script: Optional[Script] = None
    scene_descriptions: Optional[SceneDescriptionCollection] = None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        if self.beat_sheet:
            d["beat_sheet"] = self.beat_sheet.model_dump()
        if self.character_registry:
            registry_dump = self.character_registry.model_dump()
            d["character_registry"] = registry_dump
            d["characters"] = registry_dump
        if self.script:
            d["script"] = self.script.model_dump()
        if self.scene_descriptions:
            d["scene_descriptions"] = self.scene_descriptions.model_dump()
        return d


# ── Phase 2: Visual Planning Models ───────────────────────────────────────────

class ImageModelTarget(str, Enum):
    """Target AI image generation model."""
    MIDJOURNEY = "midjourney"
    DALLE = "dalle"
    SDXL = "sdxl"


class StoryboardFramePrompt(BaseModel):
    """A single storyboard frame prompt for AI image generation."""
    frame_index: int
    prompt: str
    negative_prompt: str = ""
    camera: str = ""
    lighting: str = ""
    mood: str = ""
    style: str = ""
    characters: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SceneStoryboardPrompts(BaseModel):
    """Per-scene storyboard prompts (1–3 frames)."""
    scene_id: str
    scene_heading: str = ""
    target_model: ImageModelTarget = ImageModelTarget.SDXL
    beat_ref: Optional[str] = None
    prompts: List[StoryboardFramePrompt] = Field(default_factory=list)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["target_model"] = self.target_model.value
        d["prompts"] = [p.model_dump() for p in self.prompts]
        return d


class CharacterSheetPrompt(BaseModel):
    """AI image prompt for a character reference sheet."""
    character_id: str
    character_name: str
    prompt: str
    negative_prompt: str = ""
    target_model: ImageModelTarget = ImageModelTarget.SDXL
    visual_anchor: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["target_model"] = self.target_model.value
        return d


class MoodBoardReference(BaseModel):
    """A reference slot on a mood board (image path or prompt)."""
    label: str = ""
    prompt: str = ""
    image_path: Optional[str] = None
    notes: str = ""


class CharacterMoodBoard(BaseModel):
    """Visual reference collection for a character."""
    character_id: str
    character_name: str
    character_sheet_prompt: str = ""
    references: List[MoodBoardReference] = Field(default_factory=list)
    style_tags: List[str] = Field(default_factory=list)


class SceneMoodBoard(BaseModel):
    """Visual reference collection for a scene."""
    scene_id: str
    scene_heading: str = ""
    storyboard_frame_count: int = 0
    references: List[MoodBoardReference] = Field(default_factory=list)
    style_tags: List[str] = Field(default_factory=list)


# ── Phase 4: Animatic Models ─────────────────────────────────────────────────

class AnimaticTransition(str, Enum):
    CUT = "cut"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    MATCH_CUT = "match_cut"


class AnimaticSegment(BaseModel):
    """One timed segment on the animatic timeline."""
    segment_id: str
    scene_id: str
    frame_index: int = 1
    duration_ms: int
    transition: AnimaticTransition = AnimaticTransition.CUT
    beat_ref: Optional[str] = None
    storyboard_prompt_ref: Optional[str] = None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["transition"] = self.transition.value
        return d


class AudioCue(BaseModel):
    """Placeholder audio guidance for an animatic segment."""
    segment_id: str
    music_mood: str = ""
    sfx_cues: List[str] = Field(default_factory=list)
    voiceover_note: str = ""


class AnimaticTimeline(BaseModel):
    """Full animatic timeline for a project."""
    title: str = ""
    total_duration_ms: int = 0
    segments: List[AnimaticSegment] = Field(default_factory=list)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["segments"] = [s.model_dump() for s in self.segments]
        return d


class AnimaticAudioCues(BaseModel):
    """Music/SFX/voiceover placeholder cues keyed by segment."""
    cues: List[AudioCue] = Field(default_factory=list)


# ── Phase 5: Audio Models ─────────────────────────────────────────────────

class VoiceProfile(Character):
    """Character voice profile extending Character with TTS parameters."""
    pitch: float = 1.0
    pace: float = 1.0
    accent: str = ""
    emotion_range: List[str] = Field(default_factory=lambda: ["neutral", "happy", "sad", "angry"])
    provider: str = "elevenlabs"

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["role"] = self.role.value
        return d


class VoiceProfileRegistry(BaseModel):
    """Registry of voice profiles keyed by character_id."""
    profiles: Dict[str, VoiceProfile] = Field(default_factory=dict)

    def add_profile(self, profile: VoiceProfile) -> None:
        self.profiles[profile.id] = profile

    def get_profile(self, char_id: str) -> Optional[VoiceProfile]:
        return self.profiles.get(char_id)

    def get_or_create_default(self, char_id: str, name: str) -> VoiceProfile:
        if char_id in self.profiles:
            return self.profiles[char_id]
        profile = VoiceProfile(
            id=char_id,
            name=name,
            role=CharacterRole.SUPPORTING,
        )
        self.profiles[char_id] = profile
        return profile

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["profiles"] = {k: v.model_dump() for k, v in self.profiles.items()}
        return d


class DialogueSegment(BaseModel):
    """A single dialogue-to-audio segment."""
    segment_id: str = Field(default_factory=lambda: f"DS-{uuid.uuid4().hex[:8]}")
    scene_id: str
    character_id: str
    character_name: str
    text: str
    emotion: str = "neutral"
    delivery: Optional[str] = None
    estimated_duration_ms: int = 0
    phoneme_stub: str = ""

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        return d


class DialogueSegmentCollection(BaseModel):
    """Collection of dialogue segments for batch management."""
    segments: List[DialogueSegment] = Field(default_factory=list)

    def add(self, segment: DialogueSegment) -> None:
        self.segments.append(segment)

    def get_by_scene(self, scene_id: str) -> List[DialogueSegment]:
        return [s for s in self.segments if s.scene_id == scene_id]

    def get_by_character(self, character_id: str) -> List[DialogueSegment]:
        return [s for s in self.segments if s.character_id == character_id]

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["segments"] = [s.model_dump() for s in self.segments]
        return d


class SFXCue(BaseModel):
    """A sound effect cue derived from scene description."""
    cue_id: str = Field(default_factory=lambda: f"SFX-{uuid.uuid4().hex[:8]}")
    scene_id: str
    sfx_type: str
    description: str = ""
    start_time_ms: int = 0
    duration_ms: int = 0
    volume_db: float = 0.0

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        return d


class SFXCollection(BaseModel):
    """Collection of SFX cues for batch management."""
    cues: List[SFXCue] = Field(default_factory=list)

    def add(self, cue: SFXCue) -> None:
        self.cues.append(cue)

    def get_by_scene(self, scene_id: str) -> List[SFXCue]:
        return [c for c in self.cues if c.scene_id == scene_id]

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["cues"] = [c.model_dump() for c in self.cues]
        return d


class AudioTrack(BaseModel):
    """A single audio track in the mix."""
    track_id: str = Field(default_factory=lambda: f"TRK-{uuid.uuid4().hex[:8]}")
    start_time_ms: int = 0
    duration_ms: int = 0
    volume_db: float = 0.0
    source_type: str  # "dialogue", "sfx", "music"
    segment_id: Optional[str] = None
    audio_bytes: Optional[bytes] = None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["audio_bytes"] = None  # don't serialize raw bytes
        return d


class AudioMixResult(BaseModel):
    """Result of audio mixing."""
    tracks: List[AudioTrack] = Field(default_factory=list)
    total_duration_ms: int = 0

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["tracks"] = [t.model_dump() for t in self.tracks]
        return d


class AudioCompositionResult(BaseModel):
    """Full audio composition result."""
    dialogue_tracks: List[AudioTrack] = Field(default_factory=list)
    sfx_tracks: List[AudioTrack] = Field(default_factory=list)
    music_tracks: List[AudioTrack] = Field(default_factory=list)
    total_duration_ms: int = 0

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["dialogue_tracks"] = [t.model_dump() for t in self.dialogue_tracks]
        d["sfx_tracks"] = [t.model_dump() for t in self.sfx_tracks]
        d["music_tracks"] = [t.model_dump() for t in self.music_tracks]
        return d


# ── Phase 5: Voice Provider ABC ──────────────────────────────────────

from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    """Abstract base class for TTS voice providers."""

    @abstractmethod
    def generate(self, text: str, profile: VoiceProfile) -> bytes:
        """Generate TTS audio bytes for the given text and voice profile."""
        ...

    @abstractmethod
    def validate(self) -> bool:
        """Check if the provider is configured and available."""
        ...

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return list of available voice model IDs."""
        ...


# ── Phase 6: Video Provider & Shot Models ────────────────────────────────

class VideoProvider(str, Enum):
    """Supported video generation providers."""
    DRY_RUN = "dry-run"
    RUNWAY = "runway"
    PIKA = "pika"


class VideoClip(BaseModel):
    """A generated video clip for a single shot."""
    clip_id: str
    shot_id: str
    status: str  # "pending", "generating", "completed", "failed"
    error_message: Optional[str] = None
    provider: str = ""
    duration_ms: int = 0
    url: Optional[str] = None


class VideoShot(BaseModel):
    """A single video shot derived from an animatic segment."""
    shot_id: str = Field(default_factory=lambda: f"SHOT-{uuid.uuid4().hex[:8]}")
    segment_id: str
    storyboard_prompt_ref: str
    duration_ms: int = 0
    camera_angle: str = "eye-level"
    camera_movement: str = "static"
    provider_params: Dict[str, Any] = Field(default_factory=dict)
    scene_id: str = ""
    beat_ref: str = ""
    transition: str = "cut"


class VideoShotList(BaseModel):
    """A collection of video shots for a project."""
    title: str = ""
    shots: List[VideoShot] = Field(default_factory=list)

    def add_shot(self, shot: VideoShot) -> None:
        self.shots.append(shot)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["shots"] = [s.model_dump() for s in self.shots]
        return d


class VideoClipManifest(BaseModel):
    """Manifest of all generated video clips."""
    title: str = ""
    clips: List[VideoClip] = Field(default_factory=list)

    def add_clip(self, clip: VideoClip) -> None:
        self.clips.append(clip)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["clips"] = [c.model_dump() for c in self.clips]
        return d
