"""Tests for UniversalRouter — all adapters, both strategies, metrics."""

import json
import pytest
from universal_llm_router.router import (
    UniversalRouter, RouteConfig, RouteStrategy,
    MockAdapter, OllamaAdapter, OpenAIAdapter,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ok_adapter(response="ok"):
    return MockAdapter(response=response)

def make_fail_adapter():
    class AlwaysFail:
        def call(self, s, u):
            raise ConnectionError("provider down")
    return AlwaysFail()


# ---------------------------------------------------------------------------
# MockAdapter
# ---------------------------------------------------------------------------

def test_mock_adapter_basic():
    a = MockAdapter(response="hello")
    result = a.call("sys", "user")
    data = json.loads(result)
    assert data["raw"] == "hello"
    assert a.call_count == 1


# ---------------------------------------------------------------------------
# Fallback strategy
# ---------------------------------------------------------------------------

def test_fallback_uses_first_healthy():
    router = UniversalRouter(
        routes=[
            RouteConfig("good", make_ok_adapter("first")),
            RouteConfig("good2", make_ok_adapter("second")),
        ],
        strategy=RouteStrategy.FALLBACK,
    )
    result = json.loads(router.call("sys", "user"))
    assert result["raw"] == "first"
    assert router.metrics.successes == 1


def test_fallback_skips_failed_and_uses_next():
    router = UniversalRouter(
        routes=[
            RouteConfig("bad", make_fail_adapter()),
            RouteConfig("good", make_ok_adapter("backup")),
        ],
        strategy=RouteStrategy.FALLBACK,
    )
    result = json.loads(router.call("sys", "user"))
    assert result["raw"] == "backup"
    assert router.metrics.failures["bad"] == 1
    assert router.metrics.successes == 1


def test_fallback_raises_when_all_fail():
    router = UniversalRouter(
        routes=[
            RouteConfig("bad1", make_fail_adapter()),
            RouteConfig("bad2", make_fail_adapter()),
        ],
        strategy=RouteStrategy.FALLBACK,
    )
    with pytest.raises(RuntimeError, match="All 2 routes exhausted"):
        router.call("sys", "user")
    assert router.metrics.successes == 0


# ---------------------------------------------------------------------------
# Round-robin strategy
# ---------------------------------------------------------------------------

def test_round_robin_distributes():
    a1 = MockAdapter("provider_a")
    a2 = MockAdapter("provider_b")
    router = UniversalRouter(
        routes=[
            RouteConfig("a", a1),
            RouteConfig("b", a2),
        ],
        strategy=RouteStrategy.ROUND_ROBIN,
    )
    results = [json.loads(router.call("s", "u"))["raw"] for _ in range(4)]
    assert results == ["provider_a", "provider_b", "provider_a", "provider_b"]
    assert a1.call_count == 2
    assert a2.call_count == 2


def test_round_robin_skips_failed():
    a1 = MockAdapter("good")
    router = UniversalRouter(
        routes=[
            RouteConfig("bad", make_fail_adapter()),
            RouteConfig("good", a1),
        ],
        strategy=RouteStrategy.ROUND_ROBIN,
    )
    # First call starts at index 0 (bad), should fall through to index 1 (good)
    result = json.loads(router.call("s", "u"))
    assert result["raw"] == "good"


# ---------------------------------------------------------------------------
# generate() convenience method
# ---------------------------------------------------------------------------

def test_generate_method():
    router = UniversalRouter(
        routes=[RouteConfig("m", MockAdapter("gen_result"))],
    )
    result = json.loads(router.generate("hello world"))
    assert result["raw"] == "gen_result"


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def test_metrics_avg_latency_empty():
    router = UniversalRouter(routes=[RouteConfig("m", MockAdapter())])
    assert router.metrics.avg_latency() == 0.0


def test_metrics_summary_after_calls():
    router = UniversalRouter(
        routes=[
            RouteConfig("bad", make_fail_adapter()),
            RouteConfig("good", MockAdapter()),
        ],
        strategy=RouteStrategy.FALLBACK,
    )
    router.call("s", "u")
    s = router.metrics.summary()
    # requests counts per-route attempts: 1 failure + 1 success = 2
    assert s["requests"] == 2
    assert s["successes"] == 1
    assert s["failures"]["bad"] == 1
    assert s["avg_latency_s"] >= 0.0


# ---------------------------------------------------------------------------
# Validate no-routes error
# ---------------------------------------------------------------------------

def test_empty_routes_raises():
    with pytest.raises(ValueError, match="At least one route"):
        UniversalRouter(routes=[])
