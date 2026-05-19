"""
extraction — Turn source material into a structured recipe or step-by-step sequence.

Input:  raw text (article, transcript, summarizer output, etc.)
Output: structured JSON with steps, ingredients/components, and metadata

Usage:
    python -m extraction "path/to/text.txt" --output recipe.json
    echo "..." | python -m extraction - --topic "how to pickle vegetables"
    python -m extraction - --text "First, boil water. Then add salt..." --format steps
"""
from __future__ import annotations

from extraction.extractor import extract, _fallback_extract

__version__ = "0.1.0"

__all__ = ["extract", "_fallback_extract"]
