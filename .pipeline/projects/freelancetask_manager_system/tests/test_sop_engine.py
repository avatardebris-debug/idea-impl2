"""Tests for SOP engine."""

import pytest
import json
import os
import tempfile
from core.service_offering import ServiceOffering
from sop_engine.template_manager import TemplateManager
from sop_engine.scope_extractor import ScopeExtractor
from sop_engine.pricing_calculator import PricingCalculator


class TestTemplateManager:
    def setup_method(self):
        self.manager = TemplateManager()
        self.test_sop_data = {
            "title": "Test SOP",
            "description": "A test SOP",
            "deliverables": ["Deliverable 1", "Deliverable 2"],
            "timeline": {
                "total_days": 10,
                "milestones": [
                    {
                        "title": "Milestone 1",
                        "description": "First milestone",
                        "deadline_days": 5,
                        "deliverables": ["Deliverable A"]
                    }
                ]
            },
            "pricing": [
                {"name": "Basic", "price": 100, "description": "Basic tier"},
                {"name": "Pro", "price": 500, "description": "Pro tier"}
            ],
            "requirements": ["Req 1"],
            "assumptions": ["Assumption 1"],
            "risks": ["Risk 1"],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

    def test_create_and_list(self):
        offering = ServiceOffering.from_dict(self.test_sop_data)
        name = self.manager.create(offering)
        assert name == "Test SOP"

        sops = self.manager.list_all()
        assert len(sops) >= 1
        assert any(s.title == "Test SOP" for s in sops)

    def test_get_existing(self):
        offering = ServiceOffering.from_dict(self.test_sop_data)
        name = self.manager.create(offering)
        retrieved = self.manager.get(name)
        assert retrieved.title == "Test SOP"
        assert retrieved.version == "1.0"

    def test_get_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            self.manager.get("Nonexistent SOP")

    def test_edit(self):
        offering = ServiceOffering.from_dict(self.test_sop_data)
        name = self.manager.create(offering)

        updated = self.manager.edit(name, {"title": "Updated SOP"})
        assert updated.title == "Updated SOP"
        assert updated.version == "1.1"

        # Verify persistence
        retrieved = self.manager.get(name)
        assert retrieved.title == "Updated SOP"

    def test_delete(self):
        offering = ServiceOffering.from_dict(self.test_sop_data)
        name = self.manager.create(offering)

        self.manager.delete(name)
        with pytest.raises(FileNotFoundError):
            self.manager.get(name)

    def test_load_benchmarks(self):
        # Should load sample_sops.json from benchmarks
        sops = self.manager.list_all()
        assert len(sops) >= 3  # At least the 3 sample SOPs


class TestScopeExtractor:
    def test_extract(self):
        offering = ServiceOffering.from_dict({
            "title": "Test Service",
            "description": "Test",
            "deliverables": ["Del 1", "Del 2"],
            "timeline": {
                "total_days": 15,
                "milestones": [
                    {
                        "title": "M1",
                        "description": "First",
                        "deadline_days": 5,
                        "deliverables": ["Del A"]
                    },
                    {
                        "title": "M2",
                        "description": "Second",
                        "deadline_days": 15,
                        "deliverables": ["Del B", "Del C"]
                    }
                ]
            },
            "pricing": [{"name": "Basic", "price": 100, "description": ""}],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })

        extractor = ScopeExtractor()
        scope = extractor.extract(offering)

        assert scope["total_days"] == 15
        assert len(scope["deliverables"]) == 2
        assert len(scope["milestones"]) == 2
        assert scope["milestones"][0]["title"] == "M1"
        assert scope["milestones"][0]["deadline_days"] == 5


class TestPricingCalculator:
    def test_calculate(self):
        offering = ServiceOffering.from_dict({
            "title": "Test Service",
            "description": "Test",
            "deliverables": [],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [
                {"name": "Basic", "price": 100, "description": "Basic"},
                {"name": "Pro", "price": 500, "description": "Pro"},
                {"name": "Enterprise", "price": 1000, "description": "Enterprise"}
            ],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })

        calc = PricingCalculator()
        pricing = calc.calculate(offering)

        assert pricing["min_price"] == 100
        assert pricing["max_price"] == 1000
        assert pricing["avg_price"] == 533.33
        assert len(pricing["tiers"]) == 3

    def test_recommend_tier_budget_match(self):
        offering = ServiceOffering.from_dict({
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
        })

        calc = PricingCalculator()
        tier = calc.recommend_tier(offering, 500)
        assert tier.name == "Pro"

    def test_recommend_tier_budget_low(self):
        offering = ServiceOffering.from_dict({
            "title": "Test Service",
            "description": "Test",
            "deliverables": [],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [
                {"name": "Basic", "price": 100, "description": ""},
                {"name": "Pro", "price": 500, "description": ""}
            ],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })

        calc = PricingCalculator()
        tier = calc.recommend_tier(offering, 50)
        assert tier is None

    def test_recommend_tier_budget_high(self):
        offering = ServiceOffering.from_dict({
            "title": "Test Service",
            "description": "Test",
            "deliverables": [],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [
                {"name": "Basic", "price": 100, "description": ""},
                {"name": "Pro", "price": 500, "description": ""}
            ],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })

        calc = PricingCalculator()
        tier = calc.recommend_tier(offering, 1000)
        assert tier.name == "Pro"
