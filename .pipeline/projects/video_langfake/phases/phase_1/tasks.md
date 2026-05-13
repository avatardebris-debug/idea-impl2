# Phase 1 Tasks

- [x] Task 1: Project scaffold and package setup
  - What: Create the Python package structure with __init__.py, setup.py, and requirements.txt. Define the top-level package `video_langfake` with submodules for each core component.
  - Files: video_langfake/__init__.py, video_langfake/cli.py, video_langfake/audio.py, video_langfake/lip_sync.py, video_langfake/translator.py, video_langfake/pipeline.py, setup.py, requirements.txt
  - Done when: `pip install -e .` succeeds and `from video_langfake import VideoLangFake` is importable without errors.

- [x] Task 2: Audio extraction and speech-to-text module
  - What: Build `audio.py` with a function `extract_audio(video_path)` that extracts the audio track from a video file, and `transcribe_audio(audio_path, language)` that uses a speech-to-text model (e.g., Whisper) to transcribe the audio into text in the source language.
  - Files: video_langfake/audio.py
  - Done when: Given a sample video file, `extract_audio` produces a valid WAV/MP3 file, and `transcribe_audio` returns a text string with word-level timestamps.

- [x] Task 3: Text translation module
  - What: Build `translator.py` with a function `translate_text(text, source_lang, target_lang)` that translates the transcribed text from the source language to the target language, preserving timing information for later lip-sync alignment.
  - Files: video_langfake/translator.py
  - Done when: Given English text, `translate_text` returns a translated string in the target language with aligned segment timing data.

- [x] Task 4: Speech synthesis and lip-sync generation module
  - What: Build `lip_sync.py` with functions `synthesize_speech(translated_text, target_lang, output_path)` to generate spoken audio in the target language, and `generate_lip_params(video_path, target_audio)` to compute lip-sync parameters (e.g., viseme sequences or mouth landmark offsets) that align the original speaker's lip movements to the translated audio.
  - Files: video_langfake/lip_sync.py
  - Done when: Given translated text and a target language, `synthesize_speech` produces a valid audio file, and `generate_lip_params` outputs a parameter file (e.g., JSON or numpy array) describing per-frame lip adjustments.

- [x] Task 5: Video compositing and output pipeline
  - What: Build `pipeline.py` with a class `VideoLangFake` that orchestrates the full pipeline: extract audio → transcribe → translate → synthesize → lip-sync → composite. The class should have a method `process(video_path, target_language, output_path)` that runs the full chain and produces a translated video with altered lip movements.
  - Files: video_langfake/pipeline.py
  - Done when: `VideoLangFake().process("input.mp4", "es", "output.mp4")` runs end-to-end (with mock/fake models if needed) and produces an output video file with translated audio and lip-sync adjustments applied.