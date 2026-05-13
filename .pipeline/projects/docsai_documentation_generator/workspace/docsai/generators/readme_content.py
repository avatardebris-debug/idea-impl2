"""LLM-powered content generator for README sections."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from docsai.llm_interface import get_llm

logger = logging.getLogger(__name__)


class ReadmeContentGenerator:
    """Generate README content sections using an LLM.

    Falls back to deterministic generation when no LLM is available
    (e.g., no API key configured).
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Initialize the content generator.

        Args:
            provider: LLM provider name (openai, claude, gemini, ollama, grok).
            model: Optional model override.
            temperature: Sampling temperature.
        """
        self._llm = None
        try:
            self._llm = get_llm(provider=provider, model=model, temperature=temperature)
        except Exception as exc:
            logger.warning(
                "ReadmeContentGenerator: LLM unavailable (%s). "
                "Falling back to deterministic content generation.",
                exc,
            )

    def _generate_description_deterministic(self, symbols: List[Dict[str, Any]]) -> str:
        """Generate a project description without LLM."""
        kinds = {}
        for sym in symbols:
            kind = sym.get("kind", "unknown")
            kinds[kind] = kinds.get(kind, 0) + 1
        kind_str = ", ".join(f"{count} {kind}s" for kind, count in sorted(kinds.items()))
        return (
            f"This project contains {len(symbols)} public symbols ({kind_str}). "
            "It provides a set of utilities and classes for its intended domain. "
            "Refer to the API documentation for detailed usage information."
        )

    def _generate_usage_deterministic(self, symbols: List[Dict[str, Any]]) -> str:
        """Generate usage examples without LLM."""
        examples = []
        for sym in symbols[:5]:
            name = sym.get("name", "Unknown")
            kind = sym.get("kind", "unknown")
            params = sym.get("params", [])
            param_str = ", ".join(p.get("name", "x") for p in params) if params else ""
            ret = sym.get("return_type", "")
            ret_str = f" -> {ret}" if ret else ""
            examples.append(f"    # {kind}: {name}({param_str}){ret_str}")
        if not examples:
            return "    # No symbols available for usage examples."
        return "\n".join(examples)

    def _generate_architecture_deterministic(self, symbols: List[Dict[str, Any]]) -> str:
        """Generate architecture notes without LLM."""
        files = set()
        for sym in symbols:
            f = sym.get("file", "")
            if f:
                files.add(f)
        file_str = ", ".join(sorted(files)) if files else "N/A"
        return (
            f"This project is organized across the following source files: {file_str}. "
            "Each file contains related symbols grouped by functionality."
        )

    def generate_project_description(
        self,
        symbols: List[Dict[str, Any]],
        project_name: str,
        language: str,
    ) -> str:
        """Generate a project overview/description using the LLM.

        Falls back to deterministic generation when no LLM is available.
        """
        if self._llm:
            symbols_summary = self._symbols_to_summary(symbols)
            prompt = (
                f"You are a technical documentation writer. Write a concise, "
                f"professional project description for a {language} project named "
                f"'{project_name}'.\n\n"
                f"Project symbols:\n{symbols_summary}\n\n"
                f"Write a 2-3 paragraph description that explains what the project does, "
                f"its main features, and who it's for. Use markdown formatting. "
                f"Do NOT include a title or heading — just the body text."
            )
            response = self._llm.chat([{"role": "user", "content": prompt}])
            return response.content.strip()
        return self._generate_description_deterministic(symbols)

    def generate_usage_examples(
        self,
        symbols: List[Dict[str, Any]],
        language: str,
    ) -> str:
        """Generate usage examples using the LLM.

        Falls back to deterministic generation when no LLM is available.
        """
        if self._llm:
            symbols_summary = self._symbols_to_summary(symbols)
            prompt = (
                f"You are a technical documentation writer. Write usage examples for a "
                f"{language} project. The project has the following public symbols:\n\n"
                f"{symbols_summary}\n\n"
                f"Write 3-5 practical code examples showing how to use the main classes "
                f"and functions. Use {language} syntax. Format as a markdown code block "
                f"with language tags. Include brief explanatory text before each example. "
                f"Do NOT include a title or heading — just the body text."
            )
            response = self._llm.chat([{"role": "user", "content": prompt}])
            return response.content.strip()
        return self._generate_usage_deterministic(symbols)

    def generate_architecture_notes(
        self,
        symbols: List[Dict[str, Any]],
        language: str,
    ) -> str:
        """Generate architecture notes and a text-based diagram using the LLM.

        Falls back to deterministic generation when no LLM is available.
        """
        if self._llm:
            symbols_summary = self._symbols_to_summary(symbols)
            prompt = (
                f"You are a technical documentation writer. Write architecture notes for a "
                f"{language} project. The project has the following public symbols:\n\n"
                f"{symbols_summary}\n\n"
                f"Write a brief architecture overview (2-3 paragraphs) describing the "
                f"project structure and design. Then include a simple text-based architecture "
                f"diagram using ASCII art that shows the relationships between the main "
                f"classes and modules. Use markdown formatting. "
                f"Do NOT include a title or heading — just the body text."
            )
            response = self._llm.chat([{"role": "user", "content": prompt}])
            return response.content.strip()
        return self._generate_architecture_deterministic(symbols)

    def _symbols_to_summary(self, symbols: List[Dict[str, Any]]) -> str:
        """Convert symbol list to a human-readable summary string."""
        lines = []
        for sym in symbols:
            name = sym.get("name", "unknown")
            kind = sym.get("kind", "unknown")
            doc = sym.get("docstring", "")
            first_line = doc.split("\n")[0] if doc else "No description"
            file = sym.get("file", "unknown")
            lines.append(f"- {name} ({kind}) — {first_line} [file: {file}]")
        return "\n".join(lines)
