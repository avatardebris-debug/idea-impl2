# Phase 3 Tasks

- [ ] Task 1: Implement `StableDiffusionCharacterImageProvider`
  - What: Create a production-grade image provider that uses Stable Diffusion (via diffusers library) to generate reference images and scene renders with character consistency. The provider should support: (a) generating reference images from character descriptions using LoRA fine-tuning or ControlNet, (b) generating scene renders using the reference image as a conditioning input, (c) caching generated images to avoid redundant API calls.
  - Files: `consistent_character_developer/ai_consistent_char/image_provider.py` (append `StableDiffusionCharacterImageProvider`), `consistent_character_developer/requirements.txt` (add `diffusers`, `torch`, `transformers`, `accelerate`)
  - Done when: `StableDiffusionCharacterImageProvider` can generate a reference image from a character description; it can generate a scene render using a reference image as conditioning; generated images maintain character consistency across scenes; tests verify image generation and caching.

- [ ] Task 2: Implement `DALLECharacterImageProvider`
  - What: Create an alternative image provider that uses OpenAI's DALL-E API for image generation. This provider should: (a) generate reference images from character descriptions, (b) generate scene renders using image-to-image capabilities, (c) handle API rate limits and retries gracefully.
  - Files: `consistent_character_developer/ai_consistent_char/image_provider.py` (append `DALLECharacterImageProvider`)
  - Done when: `DALLECharacterImageProvider` can generate reference and scene images via OpenAI API; it handles API errors and retries; tests verify image generation (mocked API calls).

- [ ] Task 3: Add character consistency validation
  - What: Create a `CharacterConsistencyValidator` that compares generated character images against reference images using face recognition (e.g., face-recognition library or CLIP-based similarity). The validator should: (a) compute similarity scores between character images, (b) flag inconsistencies where similarity falls below a threshold, (c) suggest regeneration for low-scoring images.
  - Files: `consistent_character_developer/ai_consistent_char/consistency_validator.py` (new), `consistent_character_developer/tests/test_consistency_validator.py` (new)
  - Done when: `CharacterConsistencyValidator` can compare two character images and return a similarity score; it can validate a collection of renders against a reference; tests verify similarity computation and threshold-based flagging.

- [ ] Task 4: Implement video assembly pipeline
  - What: Create a `VideoAssemblyPipeline` that takes scene renders and assembles them into a video. The pipeline should: (a) accept a list of scene render paths, (b) add transitions between scenes, (c) add text overlays for scene headings and dialogue, (d) export to MP4 format using ffmpeg.
  - Files: `consistent_character_developer/ai_consistent_char/video_assembly.py` (new), `consistent_character_developer/tests/test_video_assembly.py` (new)
  - Done when: `VideoAssemblyPipeline` can assemble scene renders into a video with transitions and text overlays; exported video plays correctly; tests verify video creation and playback.

- [ ] Task 5: Enhance CLI with video generation
  - What: Extend the CLI to support video generation. Add `--generate-video` flag that triggers the video assembly pipeline after scene renders are complete. The CLI should: (a) accept `--video-output` for output path, (b) display progress during video assembly, (c) handle ffmpeg errors gracefully.
  - Files: `consistent_character_developer/ai_consistent_char/cli.py` (append video generation logic)
  - Done when: CLI accepts `--generate-video` flag; passing it triggers video assembly; CLI displays progress; video output is created successfully.

- [ ] Task 6: Add character voice generation
  - What: Create a `CharacterVoiceGenerator` that generates voice clips for each character using a TTS (text-to-speech) API or library. The generator should: (a) accept character voice notes and dialogue, (b) generate voice clips matching the character's voice profile, (c) synchronize voice clips with scene renders.
  - Files: `consistent_character_developer/ai_consistent_char/voice_generator.py` (new), `consistent_character_developer/tests/test_voice_generator.py` (new)
  - Done when: `CharacterVoiceGenerator` can generate voice clips for a character; voice clips match the character's voice profile; tests verify voice generation (mocked TTS calls).

- [ ] Task 7: Implement full end-to-end pipeline
  - What: Create a comprehensive end-to-end pipeline that ties together all components: script generation → character generation → reference image generation → scene rendering → consistency validation → voice generation → video assembly. The pipeline should: (a) accept a logline and genre, (b) produce a final video with consistent characters, (c) handle errors gracefully at each stage.
  - Files: `consistent_character_developer/ai_consistent_char/full_pipeline.py` (new), `consistent_character_developer/tests/test_full_pipeline.py` (new)
  - Done when: Full pipeline can generate a video from a logline; all stages execute successfully; tests verify end-to-end functionality.
