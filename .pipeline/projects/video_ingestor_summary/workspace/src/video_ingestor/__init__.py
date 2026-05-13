"""Video Ingestor — Video ingestion, transcription, and Q&A pipeline."""

__version__ = "0.1.0"

from .chunker import TextChunker, Chunk
from .embeddings import EmbeddingGenerator
from .llm_harness import LLMHarness
from .models import TranscriptSegment
from .question_answering import QuestionAnswerer, QandAError
from .storage import Storage
from .summarizer import Summarizer, SummarizationError
from .vector_store import VectorStore

__all__ = [
    "TextChunker",
    "Chunk",
    "EmbeddingGenerator",
    "LLMHarness",
    "TranscriptSegment",
    "QuestionAnswerer",
    "QandAError",
    "Storage",
    "Summarizer",
    "SummarizationError",
    "VectorStore",
]
