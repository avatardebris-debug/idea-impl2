# API Reference

This document lists every public class, method, parameter, return type, and exception in the VideoBabbel package.

---

## Package: `video_babbel`

### `__all__`

```python
__all__ = [
    "VideoBabbel",
    "VideoIngestor",
    "Transcriber",
    "Translator",
    "Summarizer",
    "QAEngine",
    "sanitize_text",
    "get_logger",
    "VideoBabbelError",
    "IngestionError",
    "TranscriptionError",
    "TranslationError",
    "SummarizationError",
    "QAError",
]
```

---

## Module: `video_babbel.core`

### Exceptions

#### `class VideoBabbelError(Exception)`

Base exception for all VideoBabbel errors.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `message` | `str` | Error message | `"A VideoBabbel error occurred"` |

**Attributes:**
- `message: str` — The error message.

---

#### `class IngestionError(VideoBabbelError)`

Raised when video ingestion fails.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `message` | `str` | Error message | `"Video ingestion failed"` |
| `video_path` | `str \| None` | Path to the video that failed | `None` |

**Attributes:**
- `video_path: str \| None` — The video path (if available).

---

#### `class TranscriptionError(VideoBabbelError)`

Raised when transcription fails.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `message` | `str` | Error message | `"Transcription failed"` |

---

#### `class TranslationError(VideoBabbelError)`

Raised when translation fails.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `message` | `str` | Error message | `"Translation failed"` |
| `source_lang` | `str \| None` | Source language code | `None` |
| `target_lang` | `str \| None` | Target language code | `None` |

**Attributes:**
- `source_lang: str \| None`
- `target_lang: str \| None`

---

#### `class SummarizationError(VideoBabbelError)`

Raised when summarization fails.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `message` | `str` | Error message | `"Summarization failed"` |

---

#### `class QAError(VideoBabbelError)`

Raised when Q&A generation fails.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `message` | `str` | Error message | `"Q&A failed"` |

---

### Utilities

#### `def sanitize_text(text: str \| None) -> str`

Sanitize text by stripping whitespace and normalizing internal spacing.

| Parameter | Type | Description |
|------|---|---|
| `text` | `str \| None` | The raw text to sanitize. |

**Returns:** `str` — The sanitized text. Returns `""` if *text* is `None` or whitespace-only.

---

#### `def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger`

Return a configured logger.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `name` | `str` | Logger name (typically `__name__`) | — |
| `log_level` | `int` | Logging level | `logging.INFO` |

**Returns:** `logging.Logger` — A logger with a StreamHandler that writes to stderr.

---

## Module: `video_babbel.pipeline`

### `class VideoBabbel`

End-to-end video translation pipeline.

#### `__init__(target_lang: str = "es", whisper_model: str = "base", max_sentences: int = 5, backend: str = "google") -> None`

| Parameter | Type | Description | Default |
|------|---|---|---|
| `target_lang` | `str` | ISO 639-1 code for the target language | `"es"` |
| `whisper_model` | `str` | Whisper model size | `"base"` |
| `max_sentences` | `int` | Maximum number of sentences in the summary | `5` |
| `backend` | `str` | Translation backend (`"google"` or `"deepL"`) | `"google"` |

---

#### `def process(video_path: str) -> dict[str, Any]`

Process a video file through the full pipeline.

| Parameter | Type | Description |
|------|---|---|
| `video_path` | `str` | Path to the input video file. |

**Returns:** `dict[str, Any]` — A dictionary with keys:

| Key | Type | Description |
|---|---|---|
| `transcript` | `list[dict]` | List of transcript segments, each with `start`, `end`, `text` keys. |
| `translation` | `str` | Translated text. |
| `summary` | `str` | Summary text. |
| `qa` | `str` | Q&A answer text. |

**Raises:**
- `VideoBabbelError` — If any stage of the pipeline fails.

---

## Module: `video_babbel.ingestor`

### `class VideoIngestor`

Extracts audio from video files using ffmpeg.

#### `__init__(video_path: str) -> None`

| Parameter | Type | Description |
|------|---|---|
| `video_path` | `str` | Path to the input video file. |

**Raises:**
- `IngestionError` — If the video file cannot be read or ffmpeg fails.

---

#### `@property def audio_path(self) -> str`

Path to the extracted audio file.

**Returns:** `str` — Absolute path to the `.wav` audio file.

---

#### `def extract(self) -> str`

Extract audio from the video file.

**Returns:** `str` — Path to the extracted audio file.

**Raises:**
- `IngestionError` — If extraction fails.

---

## Module: `video_babbel.transcriber`

### `class Transcriber`

Transcribes audio to text using OpenAI Whisper.

#### `__init__(model: str = "base") -> None`

| Parameter | Type | Description | Default |
|------|---|---|---|
| `model` | `str` | Whisper model size (`"tiny"`, `"base"`, `"small"`, `"medium"`, `"large"`) | `"base"` |

---

#### `def transcribe(audio_path: str) -> list[dict[str, Any]]`

Transcribe an audio file to text.

| Parameter | Type | Description |
|------|---|---|
| `audio_path` | `str` | Path to the input audio file. |

**Returns:** `list[dict[str, Any]]` — List of segment dicts, each with:

| Key | Type | Description |
|---|---|---|
| `start` | `float` | Start time in seconds. |
| `end` | `float` | End time in seconds. |
| `text` | `str` | Transcribed text. |

**Raises:**
- `TranscriptionError` — If transcription fails.

---

## Module: `video_babbel.translator`

### `class Translator`

Translates text between languages using Google Translate or DeepL.

#### `__init__(target_lang: str, backend: str = "google") -> None`

| Parameter | Type | Description |
|------|---|---|
| `target_lang` | `str` | ISO 639-1 target language code. |
| `backend` | `str` | Translation backend (`"google"` or `"deepL"`). |

**Raises:**
- `ValueError` — If *backend* is not `"google"` or `"deepL"`.

---

#### `def translate(text: str, source_lang: str = "auto") -> str`

Translate text to the target language.

| Parameter | Type | Description | Default |
|------|---|---|---|
| `text` | `str` | Text to translate. | — |
| `source_lang` | `str` | Source language code (`"auto"` for auto-detect). | `"auto"` |

**Returns:** `str` — Translated text.

**Raises:**
- `TranslationError` — If translation fails.

---

## Module: `video_babbel.summarizer`

### `class Summarizer`

Creates concise summaries of transcripts.

#### `__init__(max_sentences: int = 5) -> None`

| Parameter | Type | Description | Default |
|------|---|---|---|
| `max_sentences` | `int` | Maximum number of sentences in the summary. | `5` |

---

#### `def summarize(transcript: list[dict[str, Any]]) -> str`

Summarize a transcript.

| Parameter | Type | Description |
|------|---|---|
| `transcript` | `list[dict[str, Any]]` | List of transcript segment dicts. |

**Returns:** `str` — Summary text.

**Raises:**
- `SummarizationError` — If summarization fails.

---

## Module: `video_babbel.qa`

### `class QAEngine`

Answers questions based on transcript content.

#### `__init__(transcript: list[dict[str, Any]]) -> None`

| Parameter | Type | Description |
|------|---|---|
| `transcript` | `list[dict[str, Any]]` | List of transcript segment dicts. |

---

#### `def answer(question: str) -> str`

Answer a question based on the transcript.

| Parameter | Type | Description |
|------|---|---|
| `question` | `str` | The question to answer. |

**Returns:** `str` — Answer text.

**Raises:**
- `QAError` — If Q&A fails.

---

## Data Models

### `TranscriptSegment`

```python
@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
```

| Field | Type | Description |
|---|---|---|
| `start` | `float` | Start time in seconds. |
| `end` | `float` | End time in seconds. |
| `text` | `str` | Transcribed text. |

---

### `PipelineResult`

```python
@dataclass
class PipelineResult:
    transcript: list[TranscriptSegment]
    translation: str
    summary: str
    qa: str
```

| Field | Type | Description |
|---|---|---|
| `transcript` | `list[TranscriptSegment]` | List of transcript segments. |
| `translation` | `str` | Translated text. |
| `summary` | `str` | Summary text. |
| `qa` | `str` | Q&A answer text. |

---

## Supported Languages

| Code | Language |
|------|------|
| `en` | English |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |
| `ja` | Japanese |
| `ko` | Korean |
| `zh` | Chinese |
| `ru` | Russian |

---

## Error Hierarchy

```
VideoBabbelError
├── IngestionError
├── TranscriptionError
├── TranslationError
│   ├── GoogleTranslateError
│   └── DeepLError
├── SummarizationError
└── QAError
```

---

## Logging

All modules use the `get_logger()` utility. Set the log level to `logging.DEBUG` for verbose output:

```python
import logging
from video_babbel import get_logger

logger = get_logger(__name__, logging.DEBUG)
```

---

## Version

0.1.0
