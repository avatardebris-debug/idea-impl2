"""Animatic Timeline Builder — storyboard frames to timed segments with audio cues."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from ai_movie_gen_suite.models import (
    AnimaticAudioCues,
    AnimaticSegment,
    AnimaticTimeline,
    AnimaticTransition,
    AudioCue,
    SceneStoryboardPrompts,
    Script,
)


# Base hold per frame (ms); extended by dialogue and mood
BASE_FRAME_MS = 2500
MS_PER_DIALOGUE_LINE = 1200
MOOD_DURATION_MODIFIER = {
    "tense": 1.2,
    "dramatic": 1.15,
    "somber": 1.1,
    "bright": 0.9,
    "hopeful": 0.85,
}


class AnimaticTimelineBuilder:
    """Maps storyboard frames to a paced animatic timeline."""

    def __init__(
        self,
        script: Script,
        storyboard_prompts: Dict[str, SceneStoryboardPrompts],
        tone: str = "",
        manual_overrides: Optional[Dict[str, int]] = None,
    ):
        self.script = script
        self.storyboard_prompts = storyboard_prompts
        self.tone = tone
        self.manual_overrides = manual_overrides or {}

    def build_timeline(self) -> AnimaticTimeline:
        """Build animatic segments from storyboard prompts (one segment per frame)."""
        segments: List[AnimaticSegment] = []
        scene_by_id = {s.scene_id: s for s in self.script.scenes}

        for scene_id, sb in sorted(
            self.storyboard_prompts.items(),
            key=lambda x: self._scene_order(x[0], scene_by_id),
        ):
            scene = scene_by_id.get(scene_id)
            for frame in sb.prompts:
                seg_id = f"SEG-{uuid.uuid4().hex[:8].upper()}"
                override_key = f"{scene_id}:{frame.frame_index}"
                duration = self.manual_overrides.get(
                    override_key,
                    self._suggest_duration_ms(scene, frame.mood),
                )
                transition = self._suggest_transition(frame.frame_index, len(sb.prompts))
                segments.append(
                    AnimaticSegment(
                        segment_id=seg_id,
                        scene_id=scene_id,
                        frame_index=frame.frame_index,
                        duration_ms=duration,
                        transition=transition,
                        beat_ref=sb.beat_ref,
                        storyboard_prompt_ref=f"{scene_id}_frame_{frame.frame_index}",
                    )
                )

        total = sum(s.duration_ms for s in segments)
        return AnimaticTimeline(
            title=self.script.title,
            total_duration_ms=total,
            segments=segments,
        )

    def build_audio_cues(self, timeline: AnimaticTimeline) -> AnimaticAudioCues:
        """Placeholder music/SFX/voiceover cues per segment."""
        cues: List[AudioCue] = []
        scene_by_id = {s.scene_id: s for s in self.script.scenes}

        for seg in timeline.segments:
            scene = scene_by_id.get(seg.scene_id)
            sb = self.storyboard_prompts.get(seg.scene_id)
            mood = ""
            if sb and sb.prompts:
                idx = min(seg.frame_index - 1, len(sb.prompts) - 1)
                mood = sb.prompts[idx].mood

            music = self._music_mood(mood)
            sfx: List[str] = []
            if scene and "EXT" in scene.scene_heading.upper():
                sfx.append("ambient_exterior")
            if scene and scene.dialogue_lines and seg.frame_index == 2:
                sfx.append("room_tone_low")

            vo = ""
            if scene and scene.dialogue_lines:
                vo = f"Dialogue placeholder ({len(scene.dialogue_lines)} lines)"

            cues.append(
                AudioCue(
                    segment_id=seg.segment_id,
                    music_mood=music,
                    sfx_cues=sfx,
                    voiceover_note=vo,
                )
            )

        return AnimaticAudioCues(cues=cues)

    def build_preview_manifest(self, timeline: AnimaticTimeline) -> Dict:
        """Simple frame list + timings for downstream preview tools."""
        frames = []
        offset = 0
        for seg in timeline.segments:
            frames.append(
                {
                    "segment_id": seg.segment_id,
                    "scene_id": seg.scene_id,
                    "frame_index": seg.frame_index,
                    "start_ms": offset,
                    "duration_ms": seg.duration_ms,
                    "end_ms": offset + seg.duration_ms,
                    "transition": seg.transition.value,
                    "storyboard_prompt_ref": seg.storyboard_prompt_ref,
                }
            )
            offset += seg.duration_ms
        return {
            "title": timeline.title,
            "total_duration_ms": timeline.total_duration_ms,
            "frame_count": len(frames),
            "frames": frames,
        }

    def _suggest_duration_ms(self, scene, mood: str) -> int:
        base = BASE_FRAME_MS
        if scene:
            base += len(scene.dialogue_lines) * MS_PER_DIALOGUE_LINE
        modifier = 1.0
        mood_lower = (mood or "").lower()
        for key, mult in MOOD_DURATION_MODIFIER.items():
            if key in mood_lower:
                modifier = mult
                break
        return int(base * modifier)

    def _suggest_transition(self, frame_index: int, total_frames: int) -> AnimaticTransition:
        if frame_index >= total_frames:
            return AnimaticTransition.CUT
        if frame_index == 1:
            return AnimaticTransition.CUT
        return AnimaticTransition.DISSOLVE

    def _scene_order(self, scene_id: str, scene_by_id: dict) -> int:
        scene = scene_by_id.get(scene_id)
        if not scene:
            return 999
        try:
            return self.script.scenes.index(scene)
        except ValueError:
            return 999

    def _music_mood(self, mood: str) -> str:
        mood_lower = (mood or self.tone or "neutral").lower()
        if "tense" in mood_lower or "mysterious" in mood_lower:
            return "suspense, low strings, sparse percussion"
        if "bright" in mood_lower or "hopeful" in mood_lower:
            return "uplifting, light piano, soft pads"
        if "dramatic" in mood_lower or "somber" in mood_lower:
            return "dramatic underscore, minor key"
        return "neutral underscore, ambient bed"
