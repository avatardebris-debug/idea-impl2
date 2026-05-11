"""Rule Builder UI — Flask application entry point."""

import os
import sys
from pathlib import Path

# Add the workspace directory to the Python path so we can import the triage engine
workspace_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(workspace_dir))

from flask import Flask, jsonify, request, send_from_directory
from rule_engine.models import Rule, Condition, Action
from rule_engine.engine import RuleEngine

app = Flask(__name__, static_folder='static', template_folder='templates')

# In-memory rule store
rules_store: dict[str, dict] = {}
rule_counter = 0


def _rule_to_dict(rule: Rule) -> dict:
    """Convert a Rule object to a dictionary for JSON serialization."""
    return {
        'id': rule.id,
        'name': rule.name,
        'priority': rule.priority,
        'enabled': rule.enabled,
        'conditions': [
            {
                'field': c.field,
                'operator': c.operator,
                'value': c.value
            } for c in rule.conditions
        ],
        'actions': [
            {
                'type': a.type,
                'target': a.target
            } for a in rule.actions
        ]
    }


def _dict_to_rule(data: dict) -> Rule:
    """Convert a dictionary to a Rule object."""
    conditions = []
    for c in data.get('conditions', []):
        conditions.append(Condition(
            field=c['field'],
            operator=c['operator'],
            value=c['value']
        ))

    actions = []
    for a in data.get('actions', []):
        actions.append(Action(
            type=a['type'],
            target=a['target']
        ))

    return Rule(
        id=data.get('id'),
        name=data.get('name', ''),
        priority=data.get('priority', 50),
        enabled=data.get('enabled', True),
        conditions=conditions,
        actions=actions
    )


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory(app.template_folder, 'index.html')


@app.route('/rules', methods=['GET'])
def get_rules():
    """Return all rules as a list."""
    return jsonify(list(rules_store.values()))


@app.route('/rules', methods=['POST'])
def create_rule():
    """Create a new rule."""
    global rule_counter
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'error': 'Rule name is required'}), 400

    rule_counter += 1
    rule_id = f'rule_{rule_counter}'
    rule = _dict_to_rule({
        'id': rule_id,
        'name': data['name'].strip(),
        'priority': data.get('priority', 50),
        'enabled': data.get('enabled', True),
        'conditions': data.get('conditions', []),
        'actions': data.get('actions', [])
    })

    rules_store[rule_id] = _rule_to_dict(rule)
    return jsonify(rules_store[rule_id]), 201


@app.route('/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id: str):
    """Return a single rule."""
    rule = rules_store.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    return jsonify(rule)


@app.route('/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id: str):
    """Update an existing rule."""
    if rule_id not in rules_store:
        return jsonify({'error': 'Rule not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    rule = _dict_to_rule({
        'id': rule_id,
        'name': data.get('name', ''),
        'priority': data.get('priority', 50),
        'enabled': data.get('enabled', True),
        'conditions': data.get('conditions', []),
        'actions': data.get('actions', [])
    })

    rules_store[rule_id] = _rule_to_dict(rule)
    return jsonify(rules_store[rule_id])


@app.route('/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id: str):
    """Delete a rule."""
    if rule_id not in rules_store:
        return jsonify({'error': 'Rule not found'}), 404

    del rules_store[rule_id]
    return '', 204


@app.route('/rules/import', methods=['POST'])
def import_rules():
    """Import multiple rules."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    imported = []
    if isinstance(data, list):
        for item in data:
            rule = _dict_to_rule(item)
            rule_counter += 1
            rule_id = f'rule_{rule_counter}'
            rule.id = rule_id
            rules_store[rule_id] = _rule_to_dict(rule)
            imported.append(rules_store[rule_id])
    elif isinstance(data, dict):
        rule = _dict_to_rule(data)
        rule_counter += 1
        rule_id = f'rule_{rule_counter}'
        rule.id = rule_id
        rules_store[rule_id] = _rule_to_dict(rule)
        imported.append(rules_store[rule_id])

    return jsonify(imported), 201


@app.route('/rules/export', methods=['GET'])
def export_rules():
    """Export all rules as JSON."""
    return jsonify(list(rules_store.values()))


@app.route('/triage', methods=['POST'])
def triage():
    """Triage a message using the engine."""
    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({'error': 'Message is required'}), 400

    # Build a RuleEngine with current rules
    engine_rules = []
    for rule in rules_store.values():
        r = Rule(
            id=rule['id'],
            name=rule['name'],
            priority=rule['priority'],
            enabled=rule['enabled'],
            conditions=rule['conditions'],
            actions=rule['actions']
        )
        engine_rules.append(r)

    engine = RuleEngine(rules=engine_rules)
    actions = engine.evaluate(data['message'])
    return jsonify({
        'matched_rule': None,
        'priority': None,
        'category': None,
        'actions': [{'type': a.type, 'target': a.target} for a in actions]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
