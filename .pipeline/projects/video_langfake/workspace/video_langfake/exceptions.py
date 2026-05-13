"""Custom exceptions for video_langfake."""


class VideoLangFakeError(Exception):
    """Base exception for all video_langfake errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PipelineError(VideoLangFakeError):
    """Raised when a pipeline step fails."""

    def __init__(self, step: str, message: str, details: dict = None):
        self.step = step
        super().__init__(f"Pipeline step '{step}' failed: {message}", details)


class AudioError(VideoLangFakeError):
    """Raised when audio processing fails."""

    def __init__(self, operation: str, message: str, details: dict = None):
        self.operation = operation
        super().__init__(f"Audio operation '{operation}' failed: {message}", details)


class TranscriptionError(AudioError):
    """Raised when transcription fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__("transcription", message, details)


class TranslationError(VideoLangFakeError):
    """Raised when text translation fails."""

    def __init__(self, source_lang: str, target_lang: str, message: str, details: dict = None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        super().__init__(
            f"Translation from '{source_lang}' to '{target_lang}' failed: {message}",
            details,
        )


class SynthesisError(VideoLangFakeError):
    """Raised when speech synthesis fails."""

    def __init__(self, text: str, message: str, details: dict = None):
        self.text = text
        super().__init__(f"Speech synthesis failed for text '{text[:50]}...': {message}", details)


class LipSyncError(VideoLangFakeError):
    """Raised when lip-sync processing fails."""

    def __init__(self, operation: str, message: str, details: dict = None):
        self.operation = operation
        super().__init__(f"Lip-sync operation '{operation}' failed: {message}", details)


class VideoError(VideoLangFakeError):
    """Raised when video processing fails."""

    def __init__(self, operation: str, message: str, details: dict = None):
        self.operation = operation
        super().__init__(f"Video operation '{operation}' failed: {message}", details)


class ConfigurationError(VideoLangFakeError):
    """Raised when configuration is invalid."""

    def __init__(self, config_key: str, message: str, details: dict = None):
        self.config_key = config_key
        super().__init__(f"Configuration error for '{config_key}': {message}", details)
