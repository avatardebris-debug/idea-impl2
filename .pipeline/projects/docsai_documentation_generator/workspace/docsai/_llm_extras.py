"""DocsAI-specific LLM interface helpers appended to llm_interface.py namespace."""

import os as _os
from typing import List as _List, Dict as _Dict, Any as _Any


def format_symbols_for_llm(symbols: _List[_Dict[str, _Any]]) -> str:
    """Format parsed symbols into a human-readable string for LLM consumption."""
    if not symbols:
        return "(no symbols found)"
    lines = []
    for sym in symbols:
        kind = sym.get("kind", "unknown")
        name = sym.get("name", "?")
        params = sym.get("params", [])
        ret = sym.get("return_type", "")
        doc = sym.get("docstring", "")
        param_str = ", ".join(
            f"{p['name']}: {p['type']}" if p.get("type") else p["name"]
            for p in params
        )
        sig = f"{kind} {name}({param_str})"
        if ret:
            sig += f" -> {ret}"
        lines.append(sig)
        if doc:
            lines.append(f'  """{doc}"""')
    return "\n".join(lines)


def build_prompt(symbols: _List[_Dict[str, _Any]], language: str) -> str:
    """Build a prompt string for README generation from symbols.

    Args:
        symbols: List of parsed symbol dicts.
        language: Source language name.

    Returns:
        A formatted prompt string with instructions and symbol data.
    """
    formatted = format_symbols_for_llm(symbols)
    return (
        f"Generate a README for a {language} project.\n\n"
        f"Instructions: Write a clear README with an overview, installation, "
        f"and API reference sections.\n\n"
        f"Public API symbols:\n{formatted}"
    )


class LLMInterface:
    """Simple LLM interface for DocsAI documentation generation.

    Wraps the provider-agnostic get_llm factory with a generate() method
    that takes a plain prompt string and returns a string response.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        temperature: float = 0.4,
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.api_key = self._get_api_key()
        self._llm = None  # lazy-init

    def _get_api_key(self):
        """Return the API key from the environment (if set)."""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "grok": "XAI_API_KEY",
        }
        env_var = key_map.get(self.provider)
        return _os.environ.get(env_var, "") if env_var else ""

    def _call_api(self, prompt: str) -> str:
        """Send prompt to the LLM and return the response text."""
        if self._llm is None:
            from docsai.llm_interface import get_llm
            self._llm = get_llm(
                provider=self.provider,
                model=self.model,
                temperature=self.temperature,
            )
        msg = self._llm.chat([{"role": "user", "content": prompt}])
        return msg.content

    def generate(self, prompt: str) -> str:
        """Generate a text response for the given prompt."""
        return self._call_api(prompt)


def generate_readme_content(
    symbols: _List[_Dict[str, _Any]],
    language: str,
    project_name: str,
) -> str:
    """Generate README content using the LLM interface."""
    llm = LLMInterface()
    prompt = f"Project: {project_name}\n\n" + build_prompt(symbols, language)
    return llm.generate(prompt)
