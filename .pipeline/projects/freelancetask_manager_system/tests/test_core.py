"""Tests for core data models."""

import pytest
from core.service_offering import ServiceOffering
from core.client_profile import ClientProfile


class TestServiceOffering:
    def test_valid_creation(self):
        data = {
            "title": "Test Service",
            "description": "A test service",
            "deliverables": ["Deliverable 1"],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [{"name": "Basic", "price": 100, "description": "Basic tier"}],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        offering = ServiceOffering.from_dict(data)
        assert offering.title == "Test Service"
        assert offering.version == "1.0"
        assert len(offering.pricing) == 1
        assert offering.pricing[0].price == 100

    def test_validation_missing_title(self):
        data = {
            "description": "Missing title",
            "deliverables": [],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        errors = ServiceOffering.validate(data)
        assert any("title" in e for e in errors)

    def test_validation_missing_pricing(self):
        data = {
            "title": "Test Service",
            "description": "Missing pricing",
            "deliverables": [],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        errors = ServiceOffering.validate(data)
        assert any("pricing" in e for e in errors)

    def test_validation_invalid_price(self):
        data = {
            "title": "Test Service",
            "description": "Invalid price",
            "deliverables": [],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [{"name": "Basic", "price": -100, "description": "Negative price"}],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        errors = ServiceOffering.validate(data)
        assert any("price" in e for e in errors)

    def test_get_pricing_range(self):
        data = {
            "title": "Test Service",
            "description": "Test",
            "deliverables": [],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [
                {"name": "Basic", "price": 100, "description": ""},
                {"name": "Pro", "price": 500, "description": ""},
                {"name": "Enterprise", "price": 1000, "description": ""}
            ],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        offering = ServiceOffering.from_dict(data)
        min_p, max_p = offering.get_pricing_range()
        assert min_p == 100
        assert max_p == 1000


class TestClientProfile:
    def test_valid_creation(self):
        data = {
            "name": "Test Client",
            "email": "test@example.com",
            "industry": "Tech",
            "company_size": "10-50",
            "budget_range": "$1000-$5000",
            "needs": ["Need 1"],
            "pain_points": ["Pain 1"],
            "goals": ["Goal 1"],
            "decision_maker": "John Doe",
            "timeline_preference": "2-4 weeks",
            "notes": "Test notes"
        }
        client = ClientProfile.from_dict(data)
        assert client.name == "Test Client"
        assert client.email == "test@example.com"

    def test_validation_missing_name(self):
        data = {
            "email": "test@example.com",
            "industry": "Tech",
            "company_size": "10-50",
            "budget_range": "$1000-$5000",
            "needs": [],
            "pain_points": [],
            "goals": [],
            "decision_maker": "John Doe",
            "timeline_preference": "2-4 weeks",
            "notes": ""
        }
        errors = ClientProfile.validate(data)
        assert any("name" in e for e in errors)

    def test_validation_missing_email(self):
        data = {
            "name": "Test Client",
            "industry": "Tech",
            "company_size": "10-50",
            "budget_range": "$1000-$5000",
            "needs": [],
            "pain_points": [],
            "goals": [],
            "decision_maker": "John Doe",
            "timeline_preference": "2-4 weeks",
            "notes": ""
        }
        errors = ClientProfile.validate(data)
        assert any("email" in e for e in errors)

    def test_budget_to_range(self):
        data = {
            "name": "Test Client",
            "email": "test@example.com",
            "industry": "Tech",
            "company_size": "10-50",
            "budget_range": "$5000-$15000",
            "needs": [],
            "pain_points": [],
            "goals": [],
            "decision_maker": "John Doe",
            "timeline_preference": "2-4 weeks",
            "notes": ""
        }
        client = ClientProfile.from_dict(data)
        min_b, max_b = client.get_budget_range()
        assert min_b == 5000
        assert max_b == 15000
