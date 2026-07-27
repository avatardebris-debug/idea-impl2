"""llm_route — dotenv + Ollama/xAI auto selection."""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_resolve_prefers_grok_when_ollama_missing_and_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.delenv("PIPELINE_PROVIDER", raising=False)
    monkeypatch.delenv("PIPELINE_MODEL", raising=False)
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key-not-real-00000000")
    monkeypatch.delenv("GROK_API_KEY", raising=False)

    from pipeline.llm_route import resolve_pipeline_llm

    p, m, reason = resolve_pipeline_llm(
        None, "qwen3.6:35b-a3b-q4_K_M", ollama_check=lambda _m: False
    )
    assert p == "grok"
    assert m.startswith("grok")
    assert "xai" in reason or "grok" in reason


def test_resolve_prefers_ollama_when_model_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key-not-real-00000000")

    from pipeline.llm_route import resolve_pipeline_llm

    p, m, reason = resolve_pipeline_llm(
        None, "gemma4:latest", ollama_check=lambda model: model == "gemma4:latest"
    )
    assert p == "ollama"
    assert m == "gemma4:latest"
    assert "ollama" in reason


def test_explicit_grok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    from pipeline.llm_route import resolve_pipeline_llm

    p, m, _ = resolve_pipeline_llm("grok", "qwen3.6:35b")  # Ollama name → rewrite
    assert p == "grok"
    assert m == "grok-3"  # not pass qwen to xAI


def test_no_backend_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    from pipeline.llm_route import resolve_pipeline_llm

    with pytest.raises(ValueError, match="No LLM backend"):
        resolve_pipeline_llm(None, "missing-model", ollama_check=lambda _m: False)


def test_soft_ollama_falls_to_grok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key-not-real-00000000")
    from pipeline.llm_route import resolve_pipeline_llm

    p, m, reason = resolve_pipeline_llm(
        "ollama",
        "qwen3.6:35b-a3b-q4_K_M",
        soft_ollama=True,
        ollama_check=lambda _m: False,
    )
    assert p == "grok"
    assert m.startswith("grok")


def test_hard_ollama_stays_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key-not-real-00000000")
    from pipeline.llm_route import resolve_pipeline_llm

    p, m, reason = resolve_pipeline_llm(
        "ollama",
        "qwen3.6:35b-a3b-q4_K_M",
        soft_ollama=False,
        ollama_check=lambda _m: False,
    )
    assert p == "ollama"
    assert "qwen" in m
