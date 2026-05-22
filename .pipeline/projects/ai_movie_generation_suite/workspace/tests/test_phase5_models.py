"""Tests for Phase 5 audio models (VoiceProfile, VoiceProfileRegistry, DialogueSegment, SFXCue, etc.)."""

import pytest
from ai_movie_gen_suite.models import (
    VoiceProfile,
    VoiceProfileRegistry,
    VoiceProvider,
    DialogueSegment,
    DialogueSegmentCollection,
    SFXCue,
    SFXCollection,
    AudioTrack,
    AudioMixResult,
    AudioCompositionResult,
    CharacterRole,
)
from ai_movie_gen_suite.config import VoiceConfig


class TestVoiceProfile:
    def test_default_voice_profile(self):
        vp = VoiceProfile(id="char1", name="Hero", role=CharacterRole.PROTAGONIST)
        assert vp.id == "char1"
        assert vp.name == "Hero"
        assert vp.pitch == 1.0
        assert vp.pace == 1.0
        assert vp.accent == ""
        assert vp.emotion_range == ["neutral", "happy", "sad", "angry"]
        assert vp.provider == "elevenlabs"

    def test_custom_voice_profile(self):
        vp = VoiceProfile(
            id="char2",
            name="Villain",
            role=CharacterRole.ANTAGONIST,
            pitch=0.8,
            pace=1.2,
            accent="British",
            emotion_range=["angry", "sneering"],
            provider="openai",
        )
        assert vp.pitch == 0.8
        assert vp.pace == 1.2
        assert vp.accent == "British"
        assert vp.provider == "openai"

    def test_voice_profile_dump(self):
        vp = VoiceProfile(id="char1", name="Hero", role=CharacterRole.PROTAGONIST)
        d = vp.model_dump()
        assert d["id"] == "char1"
        assert d["name"] == "Hero"
        assert d["role"] == "protagonist"
        assert d["pitch"] == 1.0


class TestVoiceProfileRegistry:
    def test_add_and_get_profile(self):
        reg = VoiceProfileRegistry()
        vp = VoiceProfile(id="char1", name="Hero", role=CharacterRole.PROTAGONIST)
        reg.add_profile(vp)
        assert reg.get_profile("char1") is vp

    def test_get_missing_profile(self):
        reg = VoiceProfileRegistry()
        assert reg.get_profile("missing") is None

    def test_get_or_create_default(self):
        reg = VoiceProfileRegistry()
        vp = reg.get_or_create_default("char1", "Hero")
        assert vp.id == "char1"
        assert vp.name == "Hero"
        assert reg.get_profile("char1") is vp

    def test_get_or_create_returns_existing(self):
        reg = VoiceProfileRegistry()
        vp1 = VoiceProfile(id="char1", name="Hero", role=CharacterRole.PROTAGONIST)
        reg.add_profile(vp1)
        vp2 = reg.get_or_create_default("char1", "Other")
        assert vp2 is vp1

    def test_registry_dump(self):
        reg = VoiceProfileRegistry()
        vp = VoiceProfile(id="char1", name="Hero", role=CharacterRole.PROTAGONIST)
        reg.add_profile(vp)
        d = reg.model_dump()
        assert "profiles" in d
        assert "char1" in d["profiles"]


class TestDialogueSegment:
    def test_default_segment(self):
        seg = DialogueSegment(
            scene_id="scene1",
            character_id="char1",
            character_name="Hero",
            text="Hello world",
        )
        assert seg.scene_id == "scene1"
        assert seg.emotion == "neutral"
        assert seg.delivery is None
        assert seg.estimated_duration_ms == 0
        assert seg.phoneme_stub == ""

    def test_segment_dump(self):
        seg = DialogueSegment(
            scene_id="scene1",
            character_id="char1",
            character_name="Hero",
            text="Hello world",
            emotion="happy",
            delivery="enthusiastic",
            estimated_duration_ms=1500,
            phoneme_stub="PHN-abc123",
        )
        d = seg.model_dump()
        assert d["emotion"] == "happy"
        assert d["delivery"] == "enthusiastic"
        assert d["estimated_duration_ms"] == 1500


class TestDialogueSegmentCollection:
    def test_add_and_get_by_scene(self):
        coll = DialogueSegmentCollection()
        s1 = DialogueSegment(scene_id="scene1", character_id="char1", character_name="A", text="Hi")
        s2 = DialogueSegment(scene_id="scene1", character_id="char2", character_name="B", text="Hey")
        s3 = DialogueSegment(scene_id="scene2", character_id="char1", character_name="A", text="Bye")
        coll.add(s1)
        coll.add(s2)
        coll.add(s3)
        assert len(coll.get_by_scene("scene1")) == 2
        assert len(coll.get_by_scene("scene2")) == 1

    def test_get_by_character(self):
        coll = DialogueSegmentCollection()
        s1 = DialogueSegment(scene_id="scene1", character_id="char1", character_name="A", text="Hi")
        s2 = DialogueSegment(scene_id="scene1", character_id="char2", character_name="B", text="Hey")
        coll.add(s1)
        coll.add(s2)
        assert len(coll.get_by_character("char1")) == 1
        assert len(coll.get_by_character("char2")) == 1


class TestSFXCue:
    def test_default_sfx_cue(self):
        cue = SFXCue(scene_id="scene1", sfx_type="explosion", description="Big boom")
        assert cue.start_time_ms == 0
        assert cue.duration_ms == 0
        assert cue.volume_db == 0.0

    def test_sfx_cue_dump(self):
        cue = SFXCue(scene_id="scene1", sfx_type="explosion", description="Big boom", start_time_ms=5000, duration_ms=2000, volume_db=10.0)
        d = cue.model_dump()
        assert d["sfx_type"] == "explosion"
        assert d["start_time_ms"] == 5000


class TestSFXCollection:
    def test_add_and_get_by_scene(self):
        coll = SFXCollection()
        c1 = SFXCue(scene_id="scene1", sfx_type="explosion")
        c2 = SFXCue(scene_id="scene2", sfx_type="rain")
        coll.add(c1)
        coll.add(c2)
        assert len(coll.get_by_scene("scene1")) == 1
        assert len(coll.get_by_scene("scene2")) == 1


class TestAudioTrack:
    def test_default_track(self):
        t = AudioTrack(source_type="dialogue")
        assert t.start_time_ms == 0
        assert t.duration_ms == 0
        assert t.volume_db == 0.0
        assert t.segment_id is None
        assert t.audio_bytes is None

    def test_track_dump_no_bytes(self):
        t = AudioTrack(source_type="dialogue", start_time_ms=100, duration_ms=500, volume_db=-6.0)
        d = t.model_dump()
        assert d["audio_bytes"] is None


class TestAudioMixResult:
    def test_empty_mix(self):
        m = AudioMixResult(total_duration_ms=30000)
        assert len(m.tracks) == 0
        assert m.total_duration_ms == 30000

    def test_mix_with_tracks(self):
        m = AudioMixResult(total_duration_ms=30000)
        t = AudioTrack(source_type="dialogue", start_time_ms=0, duration_ms=5000)
        m.tracks.append(t)
        d = m.model_dump()
        assert len(d["tracks"]) == 1


class TestAudioCompositionResult:
    def test_empty_composition(self):
        ac = AudioCompositionResult(total_duration_ms=60000)
        assert len(ac.dialogue_tracks) == 0
        assert len(ac.sfx_tracks) == 0
        assert len(ac.music_tracks) == 0


class TestVoiceConfig:
    def test_default_voice_config(self):
        vc = VoiceConfig()
        assert vc.provider == "elevenlabs"
        assert vc.api_key_env_var == "ELEVENLABS_API_KEY"
        assert vc.model == "eleven_multilingual_v2"
        assert vc.base_url is None

    def test_custom_voice_config(self):
        vc = VoiceConfig(provider="openai", api_key_env_var="OPENAI_TTS_KEY", model="tts-1")
        assert vc.provider == "openai"
        assert vc.api_key_env_var == "OPENAI_TTS_KEY"
        assert vc.model == "tts-1"
