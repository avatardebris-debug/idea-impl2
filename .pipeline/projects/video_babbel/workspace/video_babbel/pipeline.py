"""VideoBabbel — end-to-end video translation pipeline."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from video_babbel.core import (
    IngestionError,
    QAError,
    SummarizationError,
    TranslationError,
    TranscriptionError,
    VideoBabbelError,
    get_logger,
)
from video_babbel.ingestor import VideoIngestor
from video_babbel.transcriber import Transcriber
from video_babbel.translator import Translator
from video_babbel.summarizer import Summarizer
from video_babbel.qa import QAEngine

logger = get_logger(__name__)


class VideoBabbel:
    """End-to-end video translation pipeline.

    Parameters
    ----------
    target_lang : str
        ISO 639-1 code for the target language.  Default is ``"es"``.
    whisper_model : str
        Whisper model size.  Default is ``"base"``.
    max_sentences : int
        Maximum number of sentences in the summary.  Default is 5.
    backend : str
        Translation backend.  Default is ``"google"``.
    """

    def __init__(
        self,
        target_lang: str = "es",
        whisper_model: str = "base",
        max_sentences: int = 5,
        backend: str = "google",
    ) -> None:
        self.target_lang = target_lang
        self.whisper_model = whisper_model
        self.max_sentences = max_sentences
        self.backend = backend
        logger.info(
            "Initializing VideoBabbel: %s → %s (whisper=%s, backend=%s)",
            "auto",
            target_lang,
            whisper_model,
            backend,
        )

    def process(self, video_path: str) -> Dict[str, Any]:
        """Process a video file through the full pipeline.

        Parameters
        ----------
        video_path : str
            Path to the input video file.

        Returns
        -------
        dict
            A dictionary containing ``transcript``, ``translation``,
            ``summary``, and ``qa`` keys.

        Raises
        ------
        VideoBabbelError
            If any stage of the pipeline fails.
        """
        logger.info("Processing video: %s", video_path)
        try:
            # Stage 1: Ingest
            ingestor = VideoIngestor(video_path)
            audio_path = ingestor.audio_path
            logger.info("Audio extracted to: %s", audio_path)

            # Stage 2: Transcribe
            transcriber = Transcriber(self.whisper_model)
            transcript = transcriber.transcribe(audio_path)
            logger.info("Transcription complete: %d segments", len(transcript))

            # Stage 3: Translate
            translator = Translator(self.target_lang, backend=self.backend)
            translation = translator.translate(" ".join(seg["text"] for seg in transcript))
            logger.info("Translation complete")

            # Stage 4: Summarize
            summarizer = Summarizer(self.max_sentences)
            summary = summarizer.summarize(transcript)
            logger.info("Summarization complete")

            # Stage 5: Q&A
            qa_engine = QAEngine(transcript)
            qa = qa_engine.answer("What is the main topic?")
            logger.info("Q&A complete")

            return {
                "transcript": transcript,
                "translation": translation,
                "summary": summary,
                "qa": qa,
            }
        except (IngestionError, TranscriptionError, TranslationError, SummarizationError, QAError) as exc:
            raise VideoBabbelError(str(exc)) from exc
        except Exception as exc:
            raise VideoBabbelError(f"Pipeline failed: {exc}") from exc
