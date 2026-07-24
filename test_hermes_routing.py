"""Unit tests for Hermes Ollama / xAI routing (no real network)."""

from __future__ import annotations

import pipeline.hermes_runner as hr


def test_resolve_prefers_ollama_when_model_available(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    monkeypatch.setenv("PIPELINE_MODEL", "qwen3.6:35b-a3b-q4_K_M")

    route = hr.resolve_hermes_route(
        model="qwen3.6:35b-a3b-q4_K_M",
        ollama_check=lambda m: m == "qwen3.6:35b-a3b-q4_K_M",
    )
    assert route.action == "run"
    assert route.provider == "ollama"
    assert route.model == "qwen3.6:35b-a3b-q4_K_M"
    assert route.log_label == "using ollama"
    assert "/v1" in route.base_url or route.base_url.endswith("11434/v1")


def test_resolve_ollama_wins_even_when_xai_key_set(monkeypatch):
    """Policy: prefer Ollama when model is available, even with XAI_API_KEY present."""
    monkeypatch.setenv("XAI_API_KEY", "xai-should-not-be-used")
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    monkeypatch.setenv("PIPELINE_MODEL", "qwen3:6b")

    route = hr.resolve_hermes_route(
        model="qwen3:6b",
        ollama_check=lambda m: True,
    )
    assert route.action == "run"
    assert route.provider == "ollama"
    assert route.provider != "grok"
    assert route.log_label == "using ollama"
    assert route.api_key == "ollama"  # not the xAI key


def test_resolve_falls_back_to_xai_when_ollama_missing(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key")
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    monkeypatch.delenv("HERMES_GROK_MODEL", raising=False)
    monkeypatch.setenv("PIPELINE_MODEL", "qwen3.6:35b-a3b-q4_K_M")

    route = hr.resolve_hermes_route(
        model="qwen3.6:35b-a3b-q4_K_M",
        ollama_check=lambda _m: False,
    )
    assert route.action == "run"
    assert route.provider == "grok"
    assert route.model == "grok-3"  # Ollama-only name → default xAI model
    assert route.api_key == "xai-test-key"
    assert "api.x.ai" in route.base_url
    assert route.log_label == "using xai/grok"


def test_resolve_xai_uses_hermes_grok_model_env(monkeypatch):
    monkeypatch.setenv("GROK_API_KEY", "grok-alt-key")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.setenv("HERMES_GROK_MODEL", "grok-3-fast")

    route = hr.resolve_hermes_route(
        model="qwen3:6b",
        ollama_check=lambda _m: False,
    )
    assert route.action == "run"
    assert route.provider == "grok"
    assert route.model == "grok-3-fast"
    assert route.api_key == "grok-alt-key"


def test_resolve_xai_keeps_real_grok_model_name(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-key")
    monkeypatch.delenv("HERMES_GROK_MODEL", raising=False)

    route = hr.resolve_hermes_route(
        model="grok-3-mini",
        ollama_check=lambda _m: False,
    )
    assert route.action == "run"
    assert route.provider == "grok"
    assert route.model == "grok-3-mini"


def test_resolve_skip_when_no_ollama_and_no_key(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)

    route = hr.resolve_hermes_route(
        model="qwen3:6b",
        ollama_check=lambda _m: False,
    )
    assert route.action == "skip"
    assert "skip hermes" in route.reason
    assert "no ollama model" in route.reason
    assert "no xai key" in route.reason


def test_hermes_runner_run_skips_without_worker(monkeypatch):
    """Skip path must not call ensure_hermes / AIAgent."""
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)

    def _boom(*_a, **_k):
        raise AssertionError("should not build worker when skipped")

    monkeypatch.setattr(hr, "_build_worker", _boom)
    route = hr.HermesRoute(
        action="skip",
        reason="skip hermes: no ollama model and no xai key",
        log_label="skip hermes: no ollama model and no xai key",
    )
    runner = hr.HermesGoalRunner(route=route)
    result = runner.run(prompt="do stuff", goal_check="done?")
    assert result["status"] == "skipped"
    assert result["attempts"] == 0
    assert "skip hermes" in (result.get("reason") or "")


def test_looks_like_xai_model():
    assert hr._looks_like_xai_model("grok-3") is True
    assert hr._looks_like_xai_model("grok-3-fast") is True
    assert hr._looks_like_xai_model("qwen3.6:35b") is False
    assert hr._looks_like_xai_model("grok:latest") is False


def test_ollama_name_matches_tag_aliases():
    assert hr._ollama_name_matches("qwen3:6b", "qwen3:6b") is True
    assert hr._ollama_name_matches("qwen3:6b", "qwen3:6b:latest") is True
    assert hr._ollama_name_matches("qwen3:6b:latest", "qwen3:6b") is True
    assert hr._ollama_name_matches("QWEN3:6B", "qwen3:6b") is True
    # Must not partial-match different model families
    assert hr._ollama_name_matches("qwen3", "qwen3.5:7b") is False
    assert hr._ollama_name_matches("qwen3.5:7b", "qwen3:6b") is False


def test_hermes_route_repr_redacts_api_key():
    route = hr.HermesRoute(
        action="run",
        provider="grok",
        model="grok-3",
        base_url="https://api.x.ai/v1",
        api_key="xai-super-secret-key-value",
        reason="using xai/grok",
        log_label="using xai/grok",
    )
    text = repr(route)
    assert "xai-super-secret-key-value" not in text
    assert "api_key='***'" in text or 'api_key="***"' in text
    assert "grok-3" in text
    assert str(route) == repr(route)
