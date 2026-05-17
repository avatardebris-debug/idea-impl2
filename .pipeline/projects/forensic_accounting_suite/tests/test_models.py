"""Tests for forensic_accounting_suite core models."""

import unittest
from datetime import date

from forensic_accounting_suite.core.models import (
    Company,
    CorporateRegistryEntry,
    ShippingManifest,
    ProcurementRecord,
    GovernmentContract,
    SEC_Filing,
)


class TestCompany(unittest.TestCase):
    def test_creation(self):
        c = Company(
            name="Acme Corp",
            registration_number="REG-001",
            incorporation_date=date(2020, 1, 1),
            registered_address="123 Main St",
            directors=["John Doe"],
            officers=["Jane Smith"],
            naics_code="5415",
            share_capital=100000.0,
            status="active",
        )
        self.assertEqual(c.name, "Acme Corp")
        self.assertEqual(c.registration_number, "REG-001")
        self.assertEqual(c.status, "active")

    def test_to_dict(self):
        c = Company(name="Test", registration_number="T1")
        d = c.to_dict()
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["registration_number"], "T1")

    def test_from_dict(self):
        d = {"name": "Test", "registration_number": "T1"}
        c = Company.from_dict(d)
        self.assertEqual(c.name, "Test")
        self.assertEqual(c.registration_number, "T1")


class TestCorporateRegistryEntry(unittest.TestCase):
    def test_creation(self):
        entry = CorporateRegistryEntry(
            registration_number="REG-001",
            company_name="Acme Corp",
            incorporation_date=date(2020, 1, 1),
            registered_address="123 Main St",
            directors=["John Doe"],
            officers=["Jane Smith"],
            naics_code="5415",
            share_capital=100000.0,
            status="active",
        )
        self.assertEqual(entry.registration_number, "REG-001")
        self.assertEqual(entry.company_name, "Acme Corp")
        self.assertEqual(len(entry.directors), 1)

    def test_to_dict(self):
        entry = CorporateRegistryEntry(
            registration_number="REG-001",
            company_name="Acme Corp",
        )
        d = entry.to_dict()
        self.assertEqual(d["registration_number"], "REG-001")
        self.assertEqual(d["company_name"], "Acme Corp")


class TestShippingManifest(unittest.TestCase):
    def test_creation(self):
        manifest = ShippingManifest(
            manifest_id="MAN-001",
            vessel_name="MV Ocean",
            departure_port="Port A",
            arrival_port="Port B",
            departure_date=date(2023, 1, 1),
            arrival_date=date(2023, 1, 15),
            cargo_description="Electronics",
            shipper_name="Shipper Co",
            consignee_name="Consignee Inc",
            total_value=50000.0,
            weight_kg=10000.0,
            hs_code="8517",
            origin_country="CN",
            destination_country="US",
        )
        self.assertEqual(manifest.manifest_id, "MAN-001")
        self.assertEqual(manifest.vessel_name, "MV Ocean")
        self.assertEqual(manifest.total_value, 50000.0)

    def test_to_dict(self):
        manifest = ShippingManifest(manifest_id="MAN-001")
        d = manifest.to_dict()
        self.assertEqual(d["manifest_id"], "MAN-001")


class TestProcurementRecord(unittest.TestCase):
    def test_creation(self):
        proc = ProcurementRecord(
            procurement_id="PROC-001",
            vendor_name="Vendor Co",
            vendor_address="456 Vendor St",
            vendor_registration_number="VREG-001",
            description="Office supplies",
            total_value=25000.0,
            award_date=date(2023, 6, 1),
            contract_start_date=date(2023, 6, 1),
            contract_end_date=date(2024, 6, 1),
            naics_code="423",
            funding_agency="Agency X",
        )
        self.assertEqual(proc.procurement_id, "PROC-001")
        self.assertEqual(proc.vendor_name, "Vendor Co")
        self.assertEqual(proc.total_value, 25000.0)

    def test_to_dict(self):
        proc = ProcurementRecord(procurement_id="PROC-001")
        d = proc.to_dict()
        self.assertEqual(d["procurement_id"], "PROC-001")


class TestGovernmentContract(unittest.TestCase):
    def test_creation(self):
        contract = GovernmentContract(
            contract_id="GC-001",
            contractor_name="Contractor Inc",
            contractor_address="789 Contract Ave",
            contractor_registration_number="CREG-001",
            description="Infrastructure project",
            total_value=1000000.0,
            award_date=date(2023, 3, 1),
            contract_start_date=date(2023, 3, 1),
            contract_end_date=date(2025, 3, 1),
            agency_name="Dept of Infrastructure",
            naics_code="23",
            funding_source="Federal",
        )
        self.assertEqual(contract.contract_id, "GC-001")
        self.assertEqual(contract.total_value, 1000000.0)

    def test_to_dict(self):
        contract = GovernmentContract(contract_id="GC-001")
        d = contract.to_dict()
        self.assertEqual(d["contract_id"], "GC-001")


class TestSECFiling(unittest.TestCase):
    def test_creation(self):
        filing = SEC_Filing(
            filing_id="SEC-001",
            company_name="Public Corp",
            filing_type="10-K",
            filing_date=date(2023, 3, 15),
            cik="0001234567",
            document_url="https://example.com/filing",
            revenue=50000000.0,
            net_income=5000000.0,
            total_assets=100000000.0,
            total_liabilities=50000000.0,
            shareholders_equity=50000000.0,
        )
        self.assertEqual(filing.filing_id, "SEC-001")
        self.assertEqual(filing.company_name, "Public Corp")
        self.assertEqual(filing.revenue, 50000000.0)

    def test_to_dict(self):
        filing = SEC_Filing(filing_id="SEC-001")
        d = filing.to_dict()
        self.assertEqual(d["filing_id"], "SEC-001")


if __name__ == "__main__":
    unittest.main()
