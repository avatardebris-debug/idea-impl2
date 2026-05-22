# Phase 5 Tasks

- [x] Task 1: Voice profile registry model and provider interface
  - What: Add VoiceProfile, VoiceProfileRegistry, and VoiceProvider base class to models.py; add VoiceConfig to config.py. VoiceProfile extends Character with TTS params (pitch, pace, accent, emotion_range, provider). VoiceProvider is an ABC with generate(text, profile) -> bytes, validate() -> bool, and list_models() -> list[str].
  - Files: workspace/ai_movie_gen_suite/models.py, workspace/ai_movie_gen_suite/config.py
  - Done when: New models compile; VoiceProfile has pitch/pace/accent/emotion_range/provider fields; VoiceProvider ABC has generate/validate/list_models; VoiceConfig has provider, api_key_env_var, model, base_url fields; existing 106 tests still pass

- [x] Task 2: Dialogue-to-audio segment converter
  - What: Create stages/audio/dialogue_segmenter.py that reads a Script and produces DialogueSegment objects (scene_id, character_id, character_name, text, emotion, delivery, estimated_duration_ms, phoneme_stub). Each DialogueLine in every Scene gets exactly one segment. Add DialogueSegmentCollection for batch management.
  - Files: workspace/ai_movie_gen_suite/models.py (add DialogueSegment, DialogueSegmentCollection), workspace/ai_movie_gen_suite/stages/audio/dialogue_segmenter.py
  - Done when: Every DialogueLine in every Scene maps to one DialogueSegment; segments include emotion/delivery from scene mood + character voice profile; estimated_duration_ms computed from text length; phoneme_stub is a deterministic stub (e.g. "PHN-<hash>"); DialogueSegmentCollection supports add/get_by_scene/get_by_character; new tests pass

- [x] Task 3: ElevenLabs TTS provider implementation
  - What: Create providers/elevenlabs_tts.py implementing VoiceProvider. Uses ElevenLabs API (voice_id from profile, text, stability/similarity settings). Falls back to a deterministic WAV stub (silence + phoneme metadata) when API key is missing. Add validate() that checks for ELEVENLABS_API_KEY env var.
  - Files: workspace/ai_movie_gen_suite/providers/elevenlabs_tts.py
  - Done when: generate() calls ElevenLabs API when key present; falls back to deterministic WAV bytes when key absent; validate() returns True/False based on env var; list_models() returns list of ElevenLabs voice IDs; new tests pass

- [x] Task 4: OpenAI TTS provider implementation
  - What: Create providers/openai_tts.py implementing VoiceProvider. Uses OpenAI TTS API (model=tts-1, voice from profile mapping, input text). Falls back to deterministic WAV stub when API key missing. Add voice mapping dict (e.g. "male_deep" -> "onyx", "female_soft" -> "nova").
  - Files: workspace/ai_movie_gen_suite/providers/openai_tts.py
  - Done when: generate() calls OpenAI TTS API when key present; falls back to deterministic WAV bytes when key absent; validate() returns True/False based on env var; list_models() returns OpenAI voice options; new tests pass

- [x] Task 5: Audio mixing pipeline
  - What: Create stages/audio/audio_mixer.py that takes DialogueSegmentCollection + SceneDescriptionCollection + AnimaticTimeline and produces a mixed audio timeline. For each segment: (1) generate TTS audio bytes via VoiceProvider, (2) apply emotion-based pitch/speed adjustments, (3) compute overlap with scene mood music cues, (4) produce AudioTrack objects with start_time_ms, duration_ms, volume_db, source_type. Add AudioMixResult with all tracks and total_duration_ms.
  - Files: workspace/ai_movie_gen_suite/stages/audio/audio_mixer.py
  - Done when: Each dialogue segment produces one AudioTrack; tracks have correct start_time_ms derived from animatic timeline; volume_db computed from scene mood (dialogue louder in action, softer in drama); mood music tracks interleaved; AudioMixResult contains all tracks + total_duration_ms; new tests pass

- [x] Task 6: Sound effects generator
  - What: Create stages/audio/sfx_generator.py that generates sound effect cues from scene descriptions. For each scene, analyze action keywords (e.g., "explosion", "footsteps", "door", "rain") and produce SFX cues with type, description, start_time_ms, duration_ms, volume_db. Add SFXCue model and SFXCollection model.
  - Files: workspace/ai_movie_gen_suite/models.py (add SFXCue, SFXCollection), workspace/ai_movie_gen_suite/stages/audio/sfx_generator.py
  - Done when: Action keywords in scene descriptions map to SFX types; SFX cues have start_time_ms from scene position; volume_db based on scene intensity; SFXCollection supports add/get_by_scene; new tests pass

- [x] Task 7: Audio composition orchestrator
  - What: Create stages/audio/audio_composer.py that orchestrates the full audio pipeline: takes Script + SceneDescriptionCollection + AnimaticTimeline + VoiceProfileRegistry and produces AudioCompositionResult (dialogue_tracks, sfx_tracks, music_tracks, total_duration_ms). Implements the full sequence: segment dialogue -> generate TTS -> generate SFX -> mix all tracks -> apply crossfades.
  - Files: workspace/ai_movie_gen_suite/stages/audio/audio_composer.py
  - Done when: Orchestrator calls segmenter, sfx_generator, and mixer in sequence; produces AudioCompositionResult with all track types; crossfades applied between tracks; new tests pass

- [x] Task 8: Export audio composition to project directory
  - What: Extend project_exporter.py to export audio composition artifacts: write dialogue_segments.json, sfx_cues.json, audio_mix.json, and audio_timeline.json to the project output directory. Add export_audio_composition() method.
  - Files: workspace/ai_movie_gen_suite/pipeline/project_exporter.py
  - Done when: export_audio_composition() writes all audio artifacts to project dir; dialogue_segments.json contains all segments; sfx_cues.json contains all SFX; audio_mix.json contains all tracks; audio_timeline.json contains timeline; existing tests still pass


<!-- 2 tasks trimmed by planner choice (option D) -->