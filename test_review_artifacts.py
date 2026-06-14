"""Tests for review artifact helpers and message-bus shutdown handling."""

from pipeline.message_bus import Message, MessageBus
from pipeline.review_artifacts import review_artifacts_complete, validation_passed


def test_validation_passed() -> None:
    assert validation_passed("## Verdict: PASS\n")
    assert not validation_passed("## Verdict: FAIL\n")


def test_review_artifacts_complete_rejects_short_template() -> None:
    template = "## Blocking Bugs\nNone\n\n## Verdict\nPASS\n"
    assert not review_artifacts_complete(template)


def test_review_artifacts_complete_accepts_real_review() -> None:
    review = (
        "# Code Review\n\n"
        "## Blocking Bugs\nNone\n\n"
        "## Non-Blocking Notes\n- consider typing\n\n"
        "## Verdict\nPASS — tests green and player launches\n"
        + ("x" * 200)
    )
    assert review_artifacts_complete(review)


def test_has_active_work_ignores_shutdown_signals(tmp_path, monkeypatch) -> None:
    db_dir = tmp_path / "state"
    db_dir.mkdir()
    monkeypatch.setattr(
        "pipeline.message_bus.message_bus_db",
        lambda: db_dir / "messages.sqlite",
    )
    bus = MessageBus()
    bus.send(Message.create("runner", "idea_planner", type="signal", payload={"signal": "SHUTDOWN"}))
    assert not bus.has_active_work()
    assert bus.discard_stale_shutdowns() == 1


def test_dedupe_pending_tasks_keeps_newest(tmp_path, monkeypatch) -> None:
    db_dir = tmp_path / "state"
    db_dir.mkdir()
    monkeypatch.setattr(
        "pipeline.message_bus.message_bus_db",
        lambda: db_dir / "messages.sqlite",
    )
    bus = MessageBus()
    for phase in (2, 3, 4):
        bus.send(Message.create(
            "runner", "phase_planner", type="task",
            payload={"idea_slug": "movie_player", "phase": phase},
        ))
    assert bus.queue_depth("phase_planner") == 3
    removed = bus.dedupe_pending_tasks("phase_planner", ("idea_slug",))
    assert removed == 2
    assert bus.queue_depth("phase_planner") == 1
