"""Tests for master_ideas [[tag]] and --mission/--values parsing."""

from pipeline.idea_tags import is_steering_line, parse_idea_tags, strip_idea_tags


def test_parse_goal_system_mission_values():
    line = (
        "Build pour tool — requires: sim — "
        "[[system] house_robots] [[mission] automate construction] "
        "[[values] hard: obey_law] [[goal] pour_batch_1]"
    )
    tags = parse_idea_tags(line)
    assert tags["goal_id"] == "pour_batch_1"
    assert tags["system_id"] == "house_robots"
    assert "automate construction" in tags["mission"][0]
    assert tags["values"][0]["kind"] == "hard"
    assert "obey_law" in tags["values"][0]["rule"]
    cleaned = strip_idea_tags(line)
    assert "[[goal]" not in cleaned


def test_strip_preserves_requires():
    text = "desc requires: foo [[system] x]"
    assert "requires: foo" in strip_idea_tags(text)


def test_mission_flag_steering():
    line = "Develop abundance tools gently. [[mission] increase human flourishing] --mission"
    assert is_steering_line(f"- [x] **[increase human flourishing]** — {line}")
    tags = parse_idea_tags(line, title="increase human flourishing")
    assert tags["steering"] == "mission"
    assert any("flourishing" in m.lower() for m in tags["mission"])
    assert "--mission" not in strip_idea_tags(line)


def test_values_and_hardvalue_flags():
    soft = parse_idea_tags("preference for peace --values", title="peace")
    assert soft["steering"] == "values"
    assert soft["values"][0]["kind"] == "soft"
    assert "peace" in soft["values"][0]["rule"].lower()

    hard = parse_idea_tags("never violate consent --hardvalue", title="consent")
    assert hard["steering"] == "hardvalue"
    assert hard["values"][0]["kind"] == "hard"
