"""DocsAI parsers module — registry and factory."""

from __future__ import annotations

from typing import Union

from docsai.parsers.python_parser import PythonParser
from docsai.parsers.typescript_parser import TypeScriptParser

_PARSER_REGISTRY: dict[str, type] = {
    "python": PythonParser,
    "typescript": TypeScriptParser,
    "tsx": TypeScriptParser,
}


def get_parser(language: str) -> Union[PythonParser, TypeScriptParser]:
    """Return a parser instance for the given language.

    Args:
        language: Language name (e.g. 'python', 'typescript', 'tsx').

    Raises:
        ValueError: If the language is not supported.
    """
    lang = language.lower()
    if lang not in _PARSER_REGISTRY:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Supported: {sorted(_PARSER_REGISTRY)}"
        )
    return _PARSER_REGISTRY[lang]()
