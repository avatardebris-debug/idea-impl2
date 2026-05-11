"""Integration tests for the rule_builder_ui Flask API."""

import json
import sys
import os
import uuid

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from rule_builder_ui.app import app, _store, _get_store_path, _load_rules, _save_rules


@pytest.fixture(autouse=True)
def _reset_store():
    """Reset the store before each test."""
    path = _get_store_path()
    _store.save([], path)
    yield
    # Clean up after
    _store.save([], path)


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestRuleCRUD:
    """Test CRUD operations for rules."""

    def test_create_rule(self, client):
        """Test creating a new rule."""
        rule_data = {
            'name': 'Test Rule',
            'priority': 75,
            'enabled': True,
            'conditions': [
                {'field': 'subject', 'operator': 'contains', 'value': 'urgent'}
            ],
            'actions': [
                {'type': 'set_priority', 'target': 'high'}
            ]
        }
        response = client.post('/rules', json=rule_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Test Rule'
        assert data['priority'] == 75
        assert data['enabled'] is True
        assert len(data['conditions']) == 1
        assert len(data['actions']) == 1

    def test_create_rule_requires_name(self, client):
        """Test that creating a rule without a name fails."""
        rule_data = {
            'priority': 50,
            'enabled': True,
            'conditions': [],
            'actions': []
        }
        response = client.post('/rules', json=rule_data)
        assert response.status_code == 400
        data = response.get_json()
        assert 'name' in data['error'].lower()

    def test_get_all_rules(self, client):
        """Test getting all rules."""
        # Create two rules
        for i in range(2):
            client.post('/rules', json={
                'name': f'Rule {i}',
                'priority': 50,
                'enabled': True,
                'conditions': [],
                'actions': []
            })

        response = client.get('/rules')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_get_rule(self, client):
        """Test getting a single rule."""
        # Create a rule
        response = client.post('/rules', json={
            'name': 'Get Me',
            'priority': 60,
            'enabled': True,
            'conditions': [],
            'actions': []
        })
        rule_id = response.get_json()['id']

        response = client.get(f'/rules/{rule_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Get Me'

    def test_get_rule_not_found(self, client):
        """Test getting a non-existent rule."""
        response = client.get('/rules/nonexistent')
        assert response.status_code == 404

    def test_update_rule(self, client):
        """Test updating a rule."""
        # Create a rule
        response = client.post('/rules', json={
            'name': 'Original',
            'priority': 50,
            'enabled': True,
            'conditions': [],
            'actions': []
        })
        rule_id = response.get_json()['id']

        # Update it
        update_data = {
            'name': 'Updated',
            'priority': 80,
            'enabled': False,
            'conditions': [{'field': 'body', 'operator': 'contains', 'value': 'test'}],
            'actions': [{'type': 'notify', 'target': 'admin@example.com'}]
        }
        response = client.put(f'/rules/{rule_id}', json=update_data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated'
        assert data['priority'] == 80
        assert data['enabled'] is False
        assert len(data['conditions']) == 1
        assert len(data['actions']) == 1

    def test_update_rule_not_found(self, client):
        """Test updating a non-existent rule."""
        response = client.put('/rules/nonexistent', json={'name': 'X'})
        assert response.status_code == 404

    def test_delete_rule(self, client):
        """Test deleting a rule."""
        # Create a rule
        response = client.post('/rules', json={
            'name': 'Delete Me',
            'priority': 50,
            'enabled': True,
            'conditions': [],
            'actions': []
        })
        rule_id = response.get_json()['id']

        response = client.delete(f'/rules/{rule_id}')
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f'/rules/{rule_id}')
        assert response.status_code == 404

    def test_delete_rule_not_found(self, client):
        """Test deleting a non-existent rule."""
        response = client.delete('/rules/nonexistent')
        assert response.status_code == 404


class TestImportExport:
    """Test import and export functionality."""

    def test_import_rules_list(self, client):
        """Test importing a list of rules."""
        rules_data = [
            {
                'name': 'Rule 1',
                'priority': 50,
                'enabled': True,
                'conditions': [],
                'actions': []
            },
            {
                'name': 'Rule 2',
                'priority': 75,
                'enabled': False,
                'conditions': [{'field': 'subject', 'operator': 'equals', 'value': 'test'}],
                'actions': [{'type': 'auto_resolve', 'target': ''}]
            }
        ]
        response = client.post('/rules/import', json=rules_data)
        assert response.status_code == 201
        data = response.get_json()
        assert len(data) == 2
        assert data[0]['name'] == 'Rule 1'
        assert data[1]['name'] == 'Rule 2'

    def test_import_rules_dict(self, client):
        """Test importing a single rule as a dict."""
        rule_data = {
            'name': 'Single Rule',
            'priority': 60,
            'enabled': True,
            'conditions': [],
            'actions': []
        }
        response = client.post('/rules/import', json=rule_data)
        assert response.status_code == 201
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['name'] == 'Single Rule'

    def test_import_rules_invalid(self, client):
        """Test importing invalid data."""
        response = client.post('/rules/import', json='not json')
        assert response.status_code == 400

    def test_export_rules(self, client):
        """Test exporting all rules."""
        # Create some rules
        for i in range(3):
            client.post('/rules', json={
                'name': f'Export Rule {i}',
                'priority': 50,
                'enabled': True,
                'conditions': [],
                'actions': []
            })

        response = client.get('/rules/export')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3


class TestTriage:
    """Test the triage endpoint."""

    def test_triage_basic(self, client):
        """Test basic triage functionality."""
        # Create a rule that matches
        client.post('/rules', json={
            'name': 'Match Rule',
            'priority': 90,
            'enabled': True,
            'conditions': [{'field': 'subject', 'operator': 'contains', 'value': 'urgent'}],
            'actions': [{'type': 'set_priority', 'target': 'high'}]
        })

        response = client.post('/triage', json={
            'message': {
                'subject': 'urgent request',
                'from': 'test@example.com',
                'body': 'Please help',
                'has_attachment': False,
                'priority_header': 'normal'
            }
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'actions' in data
        assert 'matched_rule' in data

    def test_triage_no_match(self, client):
        """Test triage with no matching rules."""
        response = client.post('/triage', json={
            'message': {
                'subject': 'normal email',
                'from': 'test@example.com',
                'body': 'Just a regular email',
                'has_attachment': False,
                'priority_header': 'normal'
            }
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['actions'] == []
        assert data['matched_rule'] is None

    def test_triage_invalid_input(self, client):
        """Test triage with invalid input."""
        response = client.post('/triage', json={})
        assert response.status_code == 400

    def test_triage_multiple_rules(self, client):
        """Test triage with multiple matching rules."""
        # Create multiple rules
        client.post('/rules', json={
            'name': 'Rule 1',
            'priority': 50,
            'enabled': True,
            'conditions': [{'field': 'subject', 'operator': 'contains', 'value': 'test'}],
            'actions': [{'type': 'tag', 'target': 'test-tag'}]
        })
        client.post('/rules', json={
            'name': 'Rule 2',
            'priority': 75,
            'enabled': True,
            'conditions': [{'field': 'from', 'operator': 'equals', 'value': 'test@example.com'}],
            'actions': [{'type': 'route', 'target': 'team@example.com'}]
        })

        response = client.post('/triage', json={
            'message': {
                'subject': 'test email',
                'from': 'test@example.com',
                'body': 'Testing',
                'has_attachment': False,
                'priority_header': 'normal'
            }
        })
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['actions']) == 2


class TestPersistence:
    """Test that rules persist across requests."""

    def test_persistence(self, client):
        """Test that rules persist after creation."""
        # Create a rule
        client.post('/rules', json={
            'name': 'Persistent Rule',
            'priority': 50,
            'enabled': True,
            'conditions': [],
            'actions': []
        })

        # Get it back
        response = client.get('/rules')
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['name'] == 'Persistent Rule'

    def test_persistence_across_requests(self, client):
        """Test that rules persist across multiple requests."""
        # Create a rule
        client.post('/rules', json={
            'name': 'Cross Request Rule',
            'priority': 60,
            'enabled': True,
            'conditions': [],
            'actions': []
        })

        # Get all rules
        response = client.get('/rules')
        data = response.get_json()
        assert len(data) == 1

        # Delete it
        rule_id = data[0]['id']
        client.delete(f'/rules/{rule_id}')

        # Verify it's gone
        response = client.get('/rules')
        data = response.get_json()
        assert len(data) == 0
