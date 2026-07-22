"""Field rework budget → deeper_work_needed."""

from __future__ import annotations

import json
import time

from pipeline.field_rework_budget import (
    STATUS_DEEPER_WORK_NEEDED,
    begin_field_rework_attempt,
    end_field_rework_attempt,
    mark_deeper_work_needed,
    maybe_park_if_over_budget,
    measure_tokens_for_slug,
    rework_over_budget,
)


def test_attempts_cap(monkeypatch):
    monkeypatch.setenv("FIELD_REWORK_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("FIELD_REWORK_MAX_MINUTES", "999")
    st = {"field_rework_attempts": 2, "field_rework_minutes": 1.0}
    assert rework_over_budget(st) is True
    st2, parked = maybe_park_if_over_budget(st)
    assert parked
    assert st2["status"] == STATUS_DEEPER_WORK_NEEDED


def test_minutes_cap(monkeypatch):
    monkeypatch.setenv("FIELD_REWORK_MAX_ATTEMPTS", "99")
    monkeypatch.setenv("FIELD_REWORK_MAX_MINUTES", "10")
    st = {"field_rework_attempts": 1, "field_rework_minutes": 10.0}
    assert rework_over_budget(st) is True


def test_begin_end_accumulates(monkeypatch):
    monkeypatch.setenv("FIELD_REWORK_MAX_ATTEMPTS", "10")
    monkeypatch.setenv("FIELD_REWORK_MAX_MINUTES", "999")
    st = begin_field_rework_attempt({})
    assert st["field_rework_attempts"] == 1
    assert "field_rework_attempt_started_at" in st
    # Force start in the past via iso already set — end still non-negative
    st = end_field_rework_attempt(st)
    assert st["field_rework_minutes"] >= 0
    assert "field_rework_attempt_started_at" not in st


def test_under_budget_not_parked(monkeypatch):
    monkeypatch.setenv("FIELD_REWORK_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("FIELD_REWORK_MAX_MINUTES", "45")
    monkeypatch.setenv("FIELD_REWORK_MAX_TOKENS", "2500000")
    st = {
        "field_rework_attempts": 1,
        "field_rework_minutes": 5.0,
        "field_rework_tokens": 1000,
    }
    st2, parked = maybe_park_if_over_budget(st)
    assert not parked
    assert st2.get("status") != STATUS_DEEPER_WORK_NEEDED


def test_tokens_cap(monkeypatch):
    monkeypatch.setenv("FIELD_REWORK_MAX_ATTEMPTS", "99")
    monkeypatch.setenv("FIELD_REWORK_MAX_MINUTES", "999")
    monkeypatch.setenv("FIELD_REWORK_MAX_TOKENS", "2500000")
    st = {
        "field_rework_attempts": 1,
        "field_rework_minutes": 1.0,
        "field_rework_tokens": 2_500_000,
    }
    assert rework_over_budget(st) is True
    st2, parked = maybe_park_if_over_budget(st)
    assert parked
    assert st2["status"] == STATUS_DEEPER_WORK_NEEDED
    assert "tokens=" in st2.get("deeper_work_reason", "")


def test_max_tokens_parses_underscore(monkeypatch):
    from pipeline.field_rework_budget import rework_max_tokens

    monkeypatch.setenv("FIELD_REWORK_MAX_TOKENS", "2_500_000")
    assert rework_max_tokens() == 2_500_000
    monkeypatch.setenv("FIELD_REWORK_MAX_TOKENS", "2.5e6")
    assert rework_max_tokens() == 2_500_000


def test_measure_tokens_prefers_llm_calls_not_double_count(tmp_path, monkeypatch):
    """Same logical call in agent_timing + llm_calls must count once (llm wins)."""
    state = tmp_path / "state"
    metrics = tmp_path / "metrics"
    state.mkdir()
    metrics.mkdir()
    ts = time.time() - 10
    slug = "tok_slug"
    # Same 1000-token call recorded in both stores (classic agent path)
    (state / "agent_timing.jsonl").write_text(
        json.dumps({"slug": slug, "ts": ts, "tokens": 1000}) + "\n",
        encoding="utf-8",
    )
    (metrics / "llm_calls.jsonl").write_text(
        json.dumps({"slug": slug, "ts_unix": ts, "tokens": 1000}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "pipeline.paths.state_dir", lambda: state, raising=False
    )
    # paths may be imported lazily inside measure — patch module functions
    import pipeline.paths as paths_mod

    monkeypatch.setattr(paths_mod, "state_dir", lambda: state)
    monkeypatch.setattr(paths_mod, "metrics_dir", lambda: metrics)

    got = measure_tokens_for_slug(slug, since_unix=ts - 60)
    assert got == 1000  # not 2000


def test_measure_tokens_skips_untimestamped_llm_when_since_set(tmp_path, monkeypatch):
    metrics = tmp_path / "metrics"
    state = tmp_path / "state"
    metrics.mkdir()
    state.mkdir()
    slug = "untimestamped"
    # No ts / ts_unix — must be skipped when since is set
    (metrics / "llm_calls.jsonl").write_text(
        json.dumps({"slug": slug, "tokens": 5000}) + "\n",
        encoding="utf-8",
    )
    import pipeline.paths as paths_mod

    monkeypatch.setattr(paths_mod, "metrics_dir", lambda: metrics)
    monkeypatch.setattr(paths_mod, "state_dir", lambda: state)

    got = measure_tokens_for_slug(slug, since_unix=time.time() - 100)
    assert got == 0


def test_end_noop_when_no_active_attempt_and_no_double_park_tokens(monkeypatch, tmp_path):
    """end after stamps cleared must not re-sum all-history tokens."""
    monkeypatch.setenv("FIELD_REWORK_MAX_ATTEMPTS", "99")
    monkeypatch.setenv("FIELD_REWORK_MAX_MINUTES", "999")
    monkeypatch.setenv("FIELD_REWORK_MAX_TOKENS", "99999999")

    state_d = tmp_path / "state"
    metrics = tmp_path / "metrics"
    state_d.mkdir()
    metrics.mkdir()
    slug = "park_slug"
    # Historical tokens outside "this attempt" window would inflate if since=0
    old_ts = time.time() - 10_000
    (metrics / "llm_calls.jsonl").write_text(
        json.dumps({"slug": slug, "ts_unix": old_ts, "tokens": 7777}) + "\n",
        encoding="utf-8",
    )
    import pipeline.paths as paths_mod

    monkeypatch.setattr(paths_mod, "metrics_dir", lambda: metrics)
    monkeypatch.setattr(paths_mod, "state_dir", lambda: state_d)

    st = begin_field_rework_attempt({"slug": slug, "field_rework_tokens": 100})
    # Stamp a recent start so window excludes old_ts
    st["field_rework_attempt_started_unix"] = time.time() - 5
    st = end_field_rework_attempt(st, slug=slug)
    tokens_after_first = int(st["field_rework_tokens"])
    assert tokens_after_first == 100  # window empty → no add
    assert "field_rework_attempt_started_at" not in st

    # Second end (as mark_deeper_work_needed would do) must be a no-op
    st2 = end_field_rework_attempt(st, slug=slug)
    assert int(st2["field_rework_tokens"]) == tokens_after_first

    st3 = mark_deeper_work_needed(st2, reason="test", slug=slug)
    assert st3["status"] == STATUS_DEEPER_WORK_NEEDED
    assert int(st3["field_rework_tokens"]) == tokens_after_first
