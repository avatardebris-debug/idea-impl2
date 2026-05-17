"""Tests for correlation engine."""

import unittest
from datetime import date

from forensic_accounting_suite.engine.correlation import CorrelationEngine, CorrelationLink
from forensic_accounting_suite.core.models import CorporateRegistryEntry, ShippingManifest, ProcurementRecord


class TestCorrelationEngine(unittest.TestCase):
    def setUp(self):
        """Create test data with known relationships."""
        self.registry_entries = [
            CorporateRegistryEntry(
                registration_number="REG-001",
                company_name="Acme Corp",
                incorporation_date=date(2020, 1, 1),
                registered_address="123 Main St",
                directors=["John Doe", "Jane Smith"],
                officers=["Jane Smith"],
                naics_code="5415",
                share_capital=100000.0,
                status="active",
            ),
            CorporateRegistryEntry(
                registration_number="REG-002",
                company_name="Beta LLC",
                incorporation_date=date(2021, 6, 1),
                registered_address="123 Main St",  # Same address
                directors=["John Doe", "Bob Wilson"],  # Shared director
                officers=["Bob Wilson"],
                naics_code="5416",
                share_capital=50000.0,
                status="active",
            ),
            CorporateRegistryEntry(
                registration_number="REG-003",
                company_name="Gamma Inc",
                incorporation_date=date(2022, 3, 1),
                registered_address="456 Oak Ave",
                directors=["Alice Brown"],
                officers=["Alice Brown"],
                naics_code="5417",
                share_capital=200000.0,
                status="active",
            ),
        ]
        self.shipping_manifests = [
            ShippingManifest(
                manifest_id="MAN-001",
                vessel_name="MV Ocean",
                departure_port="Port A",
                arrival_port="Port B",
                departure_date=date(2023, 1, 1),
                arrival_date=date(2023, 1, 15),
                cargo_description="Electronics",
                shipper_name="Acme Corp",
                consignee_name="Delta Trading",
                total_value=50000.0,
                weight_kg=10000.0,
                hs_code="8517",
                origin_country="CN",
                destination_country="US",
            ),
            ShippingManifest(
                manifest_id="MAN-002",
                vessel_name="MV Ocean",  # Same vessel
                departure_port="Port C",
                arrival_port="Port D",
                departure_date=date(2023, 2, 1),
                arrival_date=date(2023, 2, 15),
                cargo_description="Machinery",
                shipper_name="Acme Corp",  # Same shipper
                consignee_name="Epsilon Ltd",
                total_value=75000.0,
                weight_kg=15000.0,
                hs_code="84",
                origin_country="DE",
                destination_country="US",
            ),
        ]
        self.procurements = [
            ProcurementRecord(
                procurement_id="PROC-001",
                vendor_name="Acme Corp",  # Matches registry entry
                vendor_address="123 Main St",  # Same address as REG-001
                vendor_registration_number="REG-001",
                description="IT consulting",
                total_value=250000.0,
                award_date=date(2023, 6, 1),
                contract_start_date=date(2023, 6, 1),
                contract_end_date=date(2024, 6, 1),
                naics_code="5415",
                funding_agency="Dept of Technology",
            ),
            ProcurementRecord(
                procurement_id="PROC-002",
                vendor_name="Beta LLC",  # Matches registry entry
                vendor_address="789 Pine Rd",
                vendor_registration_number="REG-002",
                description="Security services",
                total_value=150000.0,
                award_date=date(2023, 7, 1),
                contract_start_date=date(2023, 7, 1),
                contract_end_date=date(2024, 7, 1),
                naics_code="5616",
                funding_agency="Dept of Homeland Security",
            ),
        ]

    def test_find_all_links_returns_list(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        links = engine.find_all_links()
        self.assertIsInstance(links, list)
        self.assertGreater(len(links), 0)

    def test_shared_director_link(self):
        engine = CorrelationEngine(registry_entries=self.registry_entries)
        links = engine.find_all_links()
        director_links = [l for l in links if l.link_type == "shared_director"]
        self.assertGreater(len(director_links), 0)
        # REG-001 and REG-002 share "John Doe"
        found = False
        for link in director_links:
            if "REG-001" in link.source_entity and "REG-002" in link.target_entity:
                found = True
                break
        self.assertTrue(found, "Expected shared director link between REG-001 and REG-002")

    def test_shared_address_link(self):
        engine = CorrelationEngine(registry_entries=self.registry_entries)
        links = engine.find_all_links()
        address_links = [l for l in links if l.link_type == "shared_address"]
        self.assertGreater(len(address_links), 0)
        # REG-001 and REG-002 share "123 Main St"
        found = False
        for link in address_links:
            if "REG-001" in link.source_entity and "REG-002" in link.target_entity:
                found = True
                break
        self.assertTrue(found, "Expected shared address link between REG-001 and REG-002")

    def test_same_vessel_link(self):
        engine = CorrelationEngine(shipping_manifests=self.shipping_manifests)
        links = engine.find_all_links()
        vessel_links = [l for l in links if l.link_type == "same_vessel"]
        self.assertGreater(len(vessel_links), 0)
        found = False
        for link in vessel_links:
            if "MAN-001" in link.source_entity and "MAN-002" in link.target_entity:
                found = True
                break
        self.assertTrue(found, "Expected same vessel link between MAN-001 and MAN-002")

    def test_same_shipper_link(self):
        engine = CorrelationEngine(shipping_manifests=self.shipping_manifests)
        links = engine.find_all_links()
        shipper_links = [l for l in links if l.link_type == "same_shipper"]
        self.assertGreater(len(shipper_links), 0)

    def test_company_is_vendor_link(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            procurements=self.procurements,
        )
        links = engine.find_all_links()
        vendor_links = [l for l in links if l.link_type == "company_is_vendor"]
        self.assertGreater(len(vendor_links), 0)
        # Acme Corp should link to PROC-001
        found = False
        for link in vendor_links:
            if "REG-001" in link.source_entity and "PROC-001" in link.target_entity:
                found = True
                break
        self.assertTrue(found, "Expected company_is_vendor link between REG-001 and PROC-001")

    def test_company_is_shipper_link(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
        )
        links = engine.find_all_links()
        shipper_links = [l for l in links if l.link_type == "company_is_shipper"]
        self.assertGreater(len(shipper_links), 0)

    def test_shared_address_cross_source(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            procurements=self.procurements,
        )
        links = engine.find_all_links()
        cross_address_links = [l for l in links if l.link_type == "shared_address"]
        # REG-001 address "123 Main St" matches PROC-001 vendor address
        found = False
        for link in cross_address_links:
            if "REG-001" in link.source_entity and "PROC-001" in link.target_entity:
                found = True
                break
        self.assertTrue(found, "Expected cross-source shared address link")

    def test_find_links_for_company(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        links = engine.find_links_for_company("Acme Corp")
        self.assertGreater(len(links), 0)
        # All links should mention Acme Corp
        for link in links:
            self.assertTrue(
                "acme" in link.source_entity.lower() or "acme" in link.target_entity.lower(),
                f"Link should mention Acme Corp: {link}",
            )

    def test_find_links_for_company_not_found(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        links = engine.find_links_for_company("Nonexistent Corp")
        self.assertEqual(len(links), 0)

    def test_no_links_with_empty_data(self):
        engine = CorrelationEngine(
            registry_entries=[],
            shipping_manifests=[],
            procurements=[],
        )
        links = engine.find_all_links()
        self.assertEqual(len(links), 0)

    def test_link_has_all_fields(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        links = engine.find_all_links()
        if links:
            link = links[0]
            self.assertIsNotNone(link.link_type)
            self.assertIsNotNone(link.source_entity)
            self.assertIsNotNone(link.target_entity)
            self.assertIsNotNone(link.confidence)
            self.assertIsNotNone(link.description)

    def test_confidence_scores(self):
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        links = engine.find_all_links()
        for link in links:
            self.assertGreaterEqual(link.confidence, 0.0)
            self.assertLessEqual(link.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
