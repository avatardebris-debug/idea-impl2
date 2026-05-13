"""Main pipeline orchestrator for video_langfake."""

import os
import tempfile
import shutil
from typing import Optional

from video_langfake.audio import extract_audio, transcribe_audio, save_transcription, load_transcription
from video_langfake.translate import translate_text, save_translation, load_translation
from video_langfake.synthesize import synthesize_speech, generate_lip_params, apply_lip_sync
from video_langfake.exceptions import (
    PipelineError,
    AudioError,
    TranscriptionError,
    TranslationError,
    SynthesisError,
    LipSyncError,
    VideoError,
)


class VideoLangFake:
    """Main pipeline class that orchestrates video translation with lip-sync.

    Usage:
        pipeline = VideoLangFake()
        pipeline.process(
            video_path="input.mp4",
            target_language="es",
            output_path="output_es.mp4",
            source_language="en",
        )
    """

    def __init__(self):
        """Initialize the pipeline with a temporary working directory."""
        self._tmp_dir = tempfile.mkdtemp(prefix="video_langfake_")
        self._cleanup_handlers = []

    def process(
        self,
        video_path: str,
        target_language: str,
        output_path: str,
        source_language: str = None,
    ) -> str:
        """Run the full video translation pipeline.

        Steps:
            1. Extract audio from video
            2. Transcribe audio to text
            3. Translate text to target language
            4. Synthesize speech in target language
            5. Generate lip-sync parameters
            6. Apply lip-sync and produce final video

        Args:
            video_path: Path to the input video file.
            target_language: Target language code (e.g. 'es', 'fr', 'de').
            output_path: Path for the output video file.
            source_language: Optional source language code. If None, auto-detected.

        Returns:
            Path to the output video file.

        Raises:
            PipelineError: If any pipeline step fails.
        """
        # Validate inputs
        if not os.path.exists(video_path):
            raise PipelineError("validate", f"Input video not found: {video_path}")

        if not target_language:
            raise PipelineError("validate", "Target language must be specified")

        if not output_path:
            raise PipelineError("validate", "Output path must be specified")

        try:
            # Step 1: Extract audio
            audio_path = os.path.join(self._tmp_dir, "audio.wav")
            self._run_step("extract_audio", self._extract_audio, video_path, audio_path)

            # Step 2: Transcribe audio
            transcription_path = os.path.join(self._tmp_dir, "transcription.json")
            transcription = self._run_step(
                "transcribe",
                self._transcribe_audio,
                audio_path,
                source_language,
                transcription_path,
            )

            # Step 3: Translate text
            translation_path = os.path.join(self._tmp_dir, "translation.json")
            translation = self._run_step(
                "translate",
                self._translate_text,
                transcription,
                source_language,
                target_language,
                translation_path,
            )

            # Step 4: Synthesize speech
            synthesized_audio_path = os.path.join(self._tmp_dir, "synthesized.wav")
            self._run_step(
                "synthesize_speech",
                self._synthesize_speech,
                translation,
                synthesized_audio_path,
            )

            # Step 5: Generate lip-sync parameters
            lip_params_path = os.path.join(self._tmp_dir, "lip_params.json")
            self._run_step(
                "generate_lip_params",
                self._generate_lip_params,
                video_path,
                synthesized_audio_path,
                lip_params_path,
            )

            # Step 6: Apply lip-sync
            self._run_step(
                "apply_lip_sync",
                self._apply_lip_sync,
                video_path,
                synthesized_audio_path,
                lip_params_path,
                output_path,
            )

            return output_path

        except Exception as e:
            self.cleanup()
            raise PipelineError("process", f"Pipeline failed: {e}")

    def _run_step(self, step_name: str, func, *args, **kwargs):
        """Run a pipeline step with error handling."""
        try:
            return func(*args, **kwargs)
        except (AudioError, TranscriptionError, TranslationError,
                SynthesisError, LipSyncError, VideoError) as e:
            raise PipelineError(step_name, str(e), {"original_error": type(e).__name__})
        except Exception as e:
            raise PipelineError(step_name, f"Unexpected error: {e}")

    def _extract_audio(self, video_path: str, output_path: str) -> str:
        """Step 1: Extract audio from video."""
        return extract_audio(video_path, output_path)

    def _transcribe_audio(self, audio_path: str, source_lang: str, output_path: str) -> dict:
        """Step 2: Transcribe audio to text."""
        transcription = transcribe_audio(audio_path, source_lang)
        save_transcription(transcription, output_path)
        return transcription

    def _translate_text(self, transcription: dict, source_lang: str, target_lang: str, output_path: str) -> dict:
        """Step 3: Translate transcribed text."""
        src_lang = source_lang or "en"
        translation = translate_text(
            transcription["text"],
            source_lang=src_lang,
            target_lang=target_lang,
            segments=transcription.get("segments"),
        )
        save_translation(translation, output_path)
        return translation

    def _synthesize_speech(self, translation: dict, output_path: str) -> str:
        """Step 4: Synthesize speech from translated text."""
        return synthesize_speech(
            translation["translated_text"],
            translation["target_lang"],
            output_path,
        )

    def _generate_lip_params(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Step 5: Generate lip-sync parameters."""
        return generate_lip_params(video_path, audio_path, output_path)

    def _apply_lip_sync(self, video_path: str, audio_path: str, lip_params_path: str, output_path: str) -> str:
        """Step 6: Apply lip-sync and produce final video."""
        return apply_lip_sync(video_path, audio_path, lip_params_path, output_path)

    def cleanup(self):
        """Clean up temporary files."""
        try:
            if os.path.exists(self._tmp_dir):
                shutil.rmtree(self._tmp_dir, ignore_errors=True)
        except Exception:
            pass

    def __del__(self):
        """Ensure cleanup on garbage collection."""
        try:
            self.cleanup()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False
