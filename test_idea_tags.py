"""Tests for master_ideas [[tag]] parsing."""

from pipeline.idea_tags import parse_idea_tags, strip_idea_tags


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
