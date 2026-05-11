"""Flask application with CRUD API endpoints for rules."""

from __future__ import annotations

import json
import uuid
from flask import Flask, jsonify, request

from rule_engine.models import Rule, Condition, Action
from rule_engine.store import RuleStore
from rule_builder_ui.validation import RuleForm

app = Flask(__name__)

# In-memory store for the Flask app (backed by RuleStore on disk)
_store = RuleStore()
_store_path = None


def _get_store_path():
    """Get or initialize the store path."""
    global _store_path
    if _store_path is None:
        _store_path = "rules.json"
    return _store_path


def _load_rules():
    """Load rules from the store."""
    path = _get_store_path()
    try:
        return _store.load(path)
    except Exception:
        return []


def _save_rules(rules):
    """Save rules to the store."""
    path = _get_store_path()
    _store.save(rules, path)


def _normalize_action(action: dict) -> dict:
    """Normalize an action dict to use 'target' instead of 'value' if needed."""
    if "value" in action and "target" not in action:
        return {**action, "target": action["value"]}
    return action


def _normalize_actions(actions: list[dict]) -> list[dict]:
    """Normalize a list of action dicts."""
    return [_normalize_action(a) for a in actions]


@app.route("/rules", methods=["POST"])
def create_rule():
    """Create a new rule."""
    form = RuleForm(request.json)
    if not form.is_valid():
        return jsonify({"error": "; ".join(form.errors)}), 400

    # Normalize actions to use 'target' instead of 'value' if needed
    raw_actions = form.data.get("actions", [])
    normalized_actions = _normalize_actions(raw_actions)

    rule = Rule(
        id=str(uuid.uuid4()),
        name=form.data["name"],
        priority=form.data.get("priority", 0),
        enabled=form.data.get("enabled", True),
        conditions=[Condition.from_dict(c) for c in form.data.get("conditions", [])],
        actions=[Action.from_dict(a) for a in normalized_actions],
    )

    rules = _load_rules()
    rules.append(rule)
    _save_rules(rules)

    return jsonify(rule.to_dict()), 201


@app.route("/rules", methods=["GET"])
def get_rules():
    """Get all rules."""
    rules = _load_rules()
    return jsonify([r.to_dict() for r in rules])


@app.route("/rules/<rule_id>", methods=["GET"])
def get_rule(rule_id):
    """Get a single rule by ID."""
    rules = _load_rules()
    for rule in rules:
        if rule.id == rule_id:
            return jsonify(rule.to_dict())
    return jsonify({"error": "Rule not found"}), 404


@app.route("/rules/<rule_id>", methods=["PUT"])
def update_rule(rule_id):
    """Update a rule."""
    rules = _load_rules()
    rule_exists = any(r.id == rule_id for r in rules)
    if not rule_exists:
        return jsonify({"error": "Rule not found"}), 404

    form = RuleForm(request.json)
    if not form.is_valid():
        return jsonify({"error": "; ".join(form.errors)}), 400

    for i, rule in enumerate(rules):
        if rule.id == rule_id:
            # Normalize actions to use 'target' instead of 'value' if needed
            raw_actions = form.data.get("actions", [])
            normalized_actions = _normalize_actions(raw_actions)

            rules[i] = Rule(
                id=rule.id,
                name=form.data["name"],
                priority=form.data.get("priority", 0),
                enabled=form.data.get("enabled", True),
                conditions=[Condition.from_dict(c) for c in form.data.get("conditions", [])],
                actions=[Action.from_dict(a) for a in normalized_actions],
            )
            _save_rules(rules)
            return jsonify(rules[i].to_dict())
    return jsonify({"error": "Rule not found"}), 404


@app.route("/rules/<rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    """Delete a rule."""
    rules = _load_rules()
    new_rules = [r for r in rules if r.id != rule_id]
    if len(new_rules) == len(rules):
        return jsonify({"error": "Rule not found"}), 404
    _save_rules(new_rules)
    return "", 204


@app.route("/rules/import", methods=["POST"])
def import_rules():
    """Import rules from a list or single rule dict."""
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400
    if not isinstance(data, (list, dict)):
        return jsonify({"error": "Data must be a list or a single rule object"}), 400
    if not isinstance(data, list):
        data = [data]

    imported = []
    for rule_data in data:
        if not isinstance(rule_data, dict):
            return jsonify({"error": "Each rule must be a dictionary"}), 400
        form = RuleForm(rule_data)
        if not form.is_valid():
            return jsonify({"error": "; ".join(form.errors)}), 400

        # Normalize actions to use 'target' instead of 'value' if needed
        raw_actions = form.data.get("actions", [])
        normalized_actions = _normalize_actions(raw_actions)

        rule = Rule(
            id=str(uuid.uuid4()),
            name=form.data["name"],
            priority=form.data.get("priority", 0),
            enabled=form.data.get("enabled", True),
            conditions=[Condition.from_dict(c) for c in form.data.get("conditions", [])],
            actions=[Action.from_dict(a) for a in normalized_actions],
        )
        imported.append(rule)

    rules = _load_rules()
    rules.extend(imported)
    _save_rules(rules)

    return jsonify([r.to_dict() for r in imported]), 201


@app.route("/rules/export", methods=["GET"])
def export_rules():
    """Export all rules as a list."""
    rules = _load_rules()
    return jsonify([r.to_dict() for r in rules])


@app.route("/triage", methods=["POST"])
def triage():
    """Triage an email against all rules."""
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    message = data["message"]
    rules = _load_rules()

    # Evaluate rules in priority order (higher priority first)
    enabled_rules = [r for r in rules if r.enabled]
    enabled_rules.sort(key=lambda r: r.priority, reverse=True)

    matched_rule = None
    all_actions = []
    for rule in enabled_rules:
        all_match = True
        for condition in rule.conditions:
            field_value = message.get(condition.field)
            if not condition.evaluate(field_value):
                all_match = False
                break
        if all_match:
            if matched_rule is None:
                matched_rule = rule
            all_actions.extend([a.to_dict() for a in rule.actions])

    return jsonify({
        "matched_rule": matched_rule.to_dict() if matched_rule else None,
        "actions": all_actions,
        "priority": matched_rule.priority if matched_rule else 50,
    })


if __name__ == "__main__":
    app.run(debug=True)
