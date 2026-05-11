"""Tests for RuleStore JSON persistence."""

import json
import os
import tempfile
import pytest
from rule_engine.models import Action, Condition, Rule
from rule_engine.store import RuleStore, RuleStoreError


class TestRuleStoreSaveLoad:
    def test_save_and_load_round_trip(self):
        rules = [
            Rule(
                id="r1",
                name="Test Rule",
                conditions=[Condition(field="subject", operator="contains", value="invoice")],
                actions=[Action(type="tag", target="billing")],
                priority=5,
                enabled=True,
            )
        ]
        store = RuleStore()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            store.save(rules, filepath)
            loaded = store.load(filepath)
            assert len(loaded) == 1
            assert loaded[0].id == "r1"
            assert loaded[0].name == "Test Rule"
            assert loaded[0].priority == 5
            assert loaded[0].enabled is True
            assert len(loaded[0].conditions) == 1
            assert loaded[0].conditions[0].field == "subject"
            assert loaded[0].conditions[0].operator == "contains"
            assert loaded[0].conditions[0].value == "invoice"
            assert len(loaded[0].actions) == 1
            assert loaded[0].actions[0].type == "tag"
            assert loaded[0].actions[0].target == "billing"
        finally:
            os.unlink(filepath)

    def test_save_creates_parent_dirs(self):
        rules = [
            Rule(
                id="r1",
                name="Test",
                conditions=[],
                actions=[],
                priority=1,
                enabled=True,
            )
        ]
        store = RuleStore()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "sub", "dir", "rules.json")
            store.save(rules, filepath)
            assert os.path.exists(filepath)

    def test_save_multiple_rules(self):
        rules = [
            Rule(
                id="r1",
                name="Rule 1",
                conditions=[Condition(field="subject", operator="equals", value="a")],
                actions=[Action(type="tag", target="a")],
                priority=1,
                enabled=True,
            ),
            Rule(
                id="r2",
                name="Rule 2",
                conditions=[Condition(field="body", operator="contains", value="b")],
                actions=[Action(type="route", target="b")],
                priority=2,
                enabled=False,
            ),
        ]
        store = RuleStore()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            store.save(rules, filepath)
            loaded = store.load(filepath)
            assert len(loaded) == 2
            assert loaded[0].id == "r1"
            assert loaded[1].id == "r2"
            assert loaded[1].enabled is False
        finally:
            os.unlink(filepath)

    def test_load_empty_file(self):
        store = RuleStore()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            filepath = f.name

        try:
            loaded = store.load(filepath)
            assert loaded == []
        finally:
            os.unlink(filepath)

    def test_load_nonexistent_file(self):
        store = RuleStore()
        with pytest.raises(RuleStoreError, match="File not found"):
            store.load("/nonexistent/path/rules.json")

    def test_load_invalid_json(self):
        store = RuleStore()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json content")
            filepath = f.name

        try:
            with pytest.raises(RuleStoreError, match="Invalid JSON"):
                store.load(filepath)
        finally:
            os.unlink(filepath)

    def test_load_invalid_structure(self):
        store = RuleStore()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"not": "a list"}')
            filepath = f.name

        try:
            with pytest.raises(RuleStoreError, match="expected a list"):
                store.load(filepath)
        finally:
            os.unlink(filepath)

    def test_unicode_round_trip(self):
        rules = [
            Rule(
                id="r1",
                name="日本語ルール",
                conditions=[Condition(field="subject", operator="contains", value="日本語")],
                actions=[Action(type="tag", target="日本語タグ")],
                priority=1,
                enabled=True,
            )
        ]
        store = RuleStore()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            filepath = f.name

        try:
            store.save(rules, filepath)
            loaded = store.load(filepath)
            assert loaded[0].name == "日本語ルール"
            assert loaded[0].conditions[0].value == "日本語"
            assert loaded[0].actions[0].target == "日本語タグ"
        finally:
            os.unlink(filepath)
