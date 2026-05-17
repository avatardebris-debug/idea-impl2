"""Tests for core data models (Company, CorporateRegistryEntry, ShippingManifest,
ProcurementRecord, GovernmentContract, SEC_Filing)."""

import sys
import pathlib
import pytest
from datetime import date

# Ensure local imports work
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from forensic_accounting_suite.core.models import (
    Company,
    CorporateRegistryEntry,
    ShippingManifest,
    ProcurementRecord,
    GovernmentContract,
    SEC_Filing,
)


# ==================== Company ====================

class TestCompany:
    def test_create_minimal(self):
        c = Company(name="Test Corp")
        assert c.name == "Test Corp"
        assert c.registration_number is None
        assert c.tax_id is None
        assert c.directors == []
        assert c.addresses == []
        assert c.aliases == []
        assert c.linked_entities == []

    def test_create_full(self):
        c = Company(
            name="Full Corp",
            registration_number="REG-123",
            tax_id="TAX-456",
            addresses=["1 Main St"],
            directors=["Alice"],
            officers=["Bob"],
            country="US",
            industry="Tech",
            status="active",
            aliases=["FullCo"],
            linked_entities=["ENT-1"],
        )
        assert c.name == "Full Corp"
        assert c.registration_number == "REG-123"
        assert c.tax_id == "TAX-456"
        assert c.addresses == ["1 Main St"]
        assert c.directors == ["Alice"]
        assert c.officers == ["Bob"]
        assert c.country == "US"
        assert c.industry == "Tech"
        assert c.status == "active"
        assert c.aliases == ["FullCo"]
        assert c.linked_entities == ["ENT-1"]

    def test_to_dict(self):
        c = Company(name="Dict Corp", registration_number="REG-1")
        d = c.to_dict()
        assert d["name"] == "Dict Corp"
        assert d["registration_number"] == "REG-1"
        assert "directors" in d
        assert "aliases" in d

    def test_from_dict(self):
        data = {"name": "FromDict Corp", "registration_number": "REG-2"}
        c = Company.from_dict(data)
        assert c.name == "FromDict Corp"
        assert c.registration_number == "REG-2"

    def test_from_dict_ignores_extra(self):
        data = {"name": "Extra Corp", "registration_number": "REG-3", "extra_field": "ignored"}
        c = Company.from_dict(data)
        assert c.name == "Extra Corp"

    def test_default_empty_lists(self):
        c = Company(name="Default Corp")
        assert c.directors == []
        assert c.addresses == []
        assert c.officers == []
        assert c.aliases == []
        assert c.linked_entities == []


# ==================== CorporateRegistryEntry ====================

class TestCorporateRegistryEntry:
    def test_create_minimal(self):
        e = CorporateRegistryEntry(company_name="Reg Corp", registration_number="REG-100")
        assert e.company_name == "Reg Corp"
        assert e.registration_number == "REG-100"
        assert e.status == "active"
        assert e.directors == []
        assert e.officers == []
        assert e.incorporation_date is None
        assert e.registered_address is None
        assert e.company_type is None
        assert e.jurisdiction is None
        assert e.share_capital is None
        assert e.naics_code is None
        assert e.source_db is None

    def test_create_full(self):
        e = CorporateRegistryEntry(
            company_name="Full Reg Corp",
            registration_number="REG-200",
            incorporation_date=date(2020, 1, 15),
            registered_address="100 Registry Ave",
            directors=["Dir1", "Dir2"],
            officers=["Off1"],
            company_type="Corporation",
            status="inactive",
            jurisdiction="Delaware",
            share_capital=50000,
            naics_code="5415",
            source_db="state_db",
        )
        assert e.company_name == "Full Reg Corp"
        assert e.status == "inactive"
        assert e.incorporation_date == date(2020, 1, 15)
        assert e.registered_address == "100 Registry Ave"
        assert e.directors == ["Dir1", "Dir2"]
        assert e.officers == ["Off1"]
        assert e.company_type == "Corporation"
        assert e.jurisdiction == "Delaware"
        assert e.share_capital == 50000
        assert e.naics_code == "5415"
        assert e.source_db == "state_db"

    def test_to_dict(self):
        e = CorporateRegistryEntry(company_name="Dict Reg", registration_number="REG-300")
        d = e.to_dict()
        assert d["company_name"] == "Dict Reg"
        assert d["registration_number"] == "REG-300"
        assert "status" in d
        assert "directors" in d

    def test_from_dict(self):
        data = {
            "company_name": "FromDict Reg",
            "registration_number": "REG-400",
            "status": "dissolved",
            "incorporation_date": "2019-06-01",
            "registered_address": "500 Fake St",
            "directors": ["Alice"],
            "officers": ["Bob"],
            "company_type": "LLC",
            "jurisdiction": "Delaware",
            "share_capital": 10000,
            "naics_code": "5416",
            "source_db": "federal_db",
        }
        e = CorporateRegistryEntry.from_dict(data)
        assert e.company_name == "FromDict Reg"
        assert e.status == "dissolved"
        assert e.incorporation_date == date(2019, 6, 1)
        assert e.registered_address == "500 Fake St"
        assert e.directors == ["Alice"]
        assert e.officers == ["Bob"]
        assert e.company_type == "LLC"
        assert e.jurisdiction == "Delaware"
        assert e.share_capital == 10000
        assert e.naics_code == "5416"
        assert e.source_db == "federal_db"

    def test_from_dict_missing_optional(self):
        data = {"company_name": "Minimal Reg", "registration_number": "REG-500"}
        e = CorporateRegistryEntry.from_dict(data)
        assert e.company_name == "Minimal Reg"
        assert e.status == "active"
        assert e.incorporation_date is None
        assert e.registered_address is None
        assert e.directors == []
        assert e.officers == []
        assert e.company_type is None
        assert e.jurisdiction is None
        assert e.share_capital is None
        assert e.naics_code is None
        assert e.source_db is None


# ==================== ShippingManifest ====================

class TestShippingManifest:
    def test_create_minimal(self):
        m = ShippingManifest(manifest_id="MAN-1")
        assert m.manifest_id == "MAN-1"
        assert m.vessel_name is None
        assert m.shipper is None
        assert m.consignee is None
        assert m.origin_port is None
        assert m.destination_port is None
        assert m.departure_date is None
        assert m.arrival_date is None
        assert m.cargo_description is None
        assert m.weight_kg is None
        assert m.hs_code is None
        assert m.declared_value is None
        assert m.currency is None
        assert m.sender_address is None
        assert m.receiver_address is None
        assert m.sender_company is None
        assert m.receiver_company is None
        assert m.source_db is None

    def test_create_full(self):
        m = ShippingManifest(
            manifest_id="MAN-2",
            vessel_name="MV Cargo",
            vessel_imo="IMO-123",
            shipper="ShipCo",
            consignee="ConsCo",
            origin_port="Port A",
            destination_port="Port B",
            departure_date=date(2023, 1, 10),
            arrival_date=date(2023, 1, 20),
            cargo_description="Electronics",
            weight_kg=5000,
            hs_code="8517",
            declared_value=100000,
            currency="USD",
            sender_address="1 Ship St",
            receiver_address="2 Cons Ave",
            sender_company="ShipCo Ltd",
            receiver_company="ConsCo Inc",
            source_db="customs_db",
        )
        assert m.manifest_id == "MAN-2"
        assert m.vessel_name == "MV Cargo"
        assert m.vessel_imo == "IMO-123"
        assert m.shipper == "ShipCo"
        assert m.consignee == "ConsCo"
        assert m.origin_port == "Port A"
        assert m.destination_port == "Port B"
        assert m.departure_date == date(2023, 1, 10)
        assert m.arrival_date == date(2023, 1, 20)
        assert m.cargo_description == "Electronics"
        assert m.weight_kg == 5000
        assert m.hs_code == "8517"
        assert m.declared_value == 100000
        assert m.currency == "USD"
        assert m.sender_address == "1 Ship St"
        assert m.receiver_address == "2 Cons Ave"
        assert m.sender_company == "ShipCo Ltd"
        assert m.receiver_company == "ConsCo Inc"
        assert m.source_db == "customs_db"

    def test_to_dict(self):
        m = ShippingManifest(manifest_id="MAN-3")
        d = m.to_dict()
        assert d["manifest_id"] == "MAN-3"
        assert "vessel_name" in d
        assert "cargo_description" in d

    def test_from_dict(self):
        data = {
            "manifest_id": "MAN-4",
            "vessel_name": "MV Ship",
            "shipper": "ShipCo",
            "consignee": "ConsCo",
            "origin_port": "Port C",
            "destination_port": "Port D",
            "departure_date": "2023-03-15",
            "arrival_date": "2023-03-25",
            "cargo_description": "Machinery",
            "weight_kg": 10000,
            "hs_code": "8471",
            "declared_value": 200000,
            "currency": "EUR",
            "sender_address": "3 Ship Rd",
            "receiver_address": "4 Cons Blvd",
            "sender_company": "ShipCo Global",
            "receiver_company": "ConsCo International",
            "source_db": "trade_db",
        }
        m = ShippingManifest.from_dict(data)
        assert m.manifest_id == "MAN-4"
        assert m.vessel_name == "MV Ship"
        assert m.shipper == "ShipCo"
        assert m.consignee == "ConsCo"
        assert m.origin_port == "Port C"
        assert m.destination_port == "Port D"
        assert m.departure_date == date(2023, 3, 15)
        assert m.arrival_date == date(2023, 3, 25)
        assert m.cargo_description == "Machinery"
        assert m.weight_kg == 10000
        assert m.hs_code == "8471"
        assert m.declared_value == 200000
        assert m.currency == "EUR"
        assert m.sender_address == "3 Ship Rd"
        assert m.receiver_address == "4 Cons Blvd"
        assert m.sender_company == "ShipCo Global"
        assert m.receiver_company == "ConsCo International"
        assert m.source_db == "trade_db"

    def test_from_dict_missing_optional(self):
        data = {"manifest_id": "MAN-5"}
        m = ShippingManifest.from_dict(data)
        assert m.manifest_id == "MAN-5"
        assert m.vessel_name is None
        assert m.shipper is None
        assert m.consignee is None
        assert m.origin_port is None
        assert m.destination_port is None
        assert m.departure_date is None
        assert m.arrival_date is None
        assert m.cargo_description is None
        assert m.weight_kg is None
        assert m.hs_code is None
        assert m.declared_value is None
        assert m.currency is None
        assert m.sender_address is None
        assert m.receiver_address is None
        assert m.sender_company is None
        assert m.receiver_company is None
        assert m.source_db is None


# ==================== ProcurementRecord ====================

class TestProcurementRecord:
    def test_create_minimal(self):
        p = ProcurementRecord(
            procurement_id="PROC-1",
            vendor_name="Vendor Corp",
            total_value=500000,
        )
        assert p.procurement_id == "PROC-1"
        assert p.vendor_name == "Vendor Corp"
        assert p.total_value == 500000
        assert p.contract_number is None
        assert p.vendor_registration_number is None
        assert p.vendor_address is None
        assert p.vendor_directors == []
        assert p.item_description is None
        assert p.quantity is None
        assert p.unit_price is None
        assert p.currency is None
        assert p.award_date is None
        assert p.delivery_date is None
        assert p.procuring_entity is None
        assert p.procuring_entity_address is None
        assert p.source_db is None

    def test_create_full(self):
        p = ProcurementRecord(
            procurement_id="PROC-2",
            contract_number="CON-100",
            vendor_name="Full Vendor",
            vendor_registration_number="REG-500",
            vendor_address="1 Vendor St",
            vendor_directors=["Dir1"],
            item_description="Laptops",
            quantity=100,
            unit_price=5000,
            total_value=500000,
            currency="USD",
            award_date=date(2023, 4, 1),
            delivery_date=date(2023, 5, 1),
            procuring_entity="Agency X",
            procuring_entity_address="2 Agency Ave",
            source_db="procurement_db",
        )
        assert p.procurement_id == "PROC-2"
        assert p.contract_number == "CON-100"
        assert p.vendor_name == "Full Vendor"
        assert p.vendor_registration_number == "REG-500"
        assert p.vendor_address == "1 Vendor St"
        assert p.vendor_directors == ["Dir1"]
        assert p.item_description == "Laptops"
        assert p.quantity == 100
        assert p.unit_price == 5000
        assert p.total_value == 500000
        assert p.currency == "USD"
        assert p.award_date == date(2023, 4, 1)
        assert p.delivery_date == date(2023, 5, 1)
        assert p.procuring_entity == "Agency X"
        assert p.procuring_entity_address == "2 Agency Ave"
        assert p.source_db == "procurement_db"

    def test_to_dict(self):
        p = ProcurementRecord(
            procurement_id="PROC-3",
            vendor_name="Dict Vendor",
            total_value=100000,
        )
        d = p.to_dict()
        assert d["procurement_id"] == "PROC-3"
        assert d["vendor_name"] == "Dict Vendor"
        assert "total_value" in d
        assert "vendor_directors" in d

    def test_from_dict(self):
        data = {
            "procurement_id": "PROC-4",
            "contract_number": "CON-200",
            "vendor_name": "FromDict Vendor",
            "vendor_registration_number": "REG-600",
            "vendor_address": "3 Vendor Rd",
            "vendor_directors": ["Alice", "Bob"],
            "item_description": "Servers",
            "quantity": 10,
            "unit_price": 50000,
            "total_value": 500000,
            "currency": "USD",
            "award_date": "2023-06-01",
            "delivery_date": "2023-07-01",
            "procuring_entity": "Agency Y",
            "procuring_entity_address": "4 Agency Blvd",
            "source_db": "gov_procurement_db",
        }
        p = ProcurementRecord.from_dict(data)
        assert p.procurement_id == "PROC-4"
        assert p.contract_number == "CON-200"
        assert p.vendor_name == "FromDict Vendor"
        assert p.vendor_registration_number == "REG-600"
        assert p.vendor_address == "3 Vendor Rd"
        assert p.vendor_directors == ["Alice", "Bob"]
        assert p.item_description == "Servers"
        assert p.quantity == 10
        assert p.unit_price == 50000
        assert p.total_value == 500000
        assert p.currency == "USD"
        assert p.award_date == date(2023, 6, 1)
        assert p.delivery_date == date(2023, 7, 1)
        assert p.procuring_entity == "Agency Y"
        assert p.procuring_entity_address == "4 Agency Blvd"
        assert p.source_db == "gov_procurement_db"

    def test_from_dict_missing_optional(self):
        data = {
            "procurement_id": "PROC-5",
            "vendor_name": "Minimal Vendor",
            "total_value": 200000,
        }
        p = ProcurementRecord.from_dict(data)
        assert p.procurement_id == "PROC-5"
        assert p.vendor_name == "Minimal Vendor"
        assert p.total_value == 200000
        assert p.contract_number is None
        assert p.vendor_registration_number is None
        assert p.vendor_address is None
        assert p.vendor_directors == []
        assert p.item_description is None
        assert p.quantity is None
        assert p.unit_price is None
        assert p.currency is None
        assert p.award_date is None
        assert p.delivery_date is None
        assert p.procuring_entity is None
        assert p.procuring_entity_address is None
        assert p.source_db is None


# ==================== GovernmentContract ====================

class TestGovernmentContract:
    def test_create_minimal(self):
        gc = GovernmentContract(
            contract_id="GC-1",
            agency="DOD",
            contractor_name="DefenseCo",
            contract_value=1000000,
        )
        assert gc.contract_id == "GC-1"
        assert gc.agency == "DOD"
        assert gc.contractor_name == "DefenseCo"
        assert gc.contract_value == 1000000
        assert gc.contract_number is None
        assert gc.agency_address is None
        assert gc.contractor_registration_number is None
        assert gc.contractor_address is None
        assert gc.contractor_directors == []
        assert gc.currency is None
        assert gc.award_date is None
        assert gc.end_date is None
        assert gc.description is None
        assert gc.contract_type is None
        assert gc.source_db is None

    def test_create_full(self):
        gc = GovernmentContract(
            contract_id="GC-2",
            contract_number="CON-300",
            agency="DOE",
            agency_address="1 Energy St",
            contractor_name="Energy Corp",
            contractor_registration_number="REG-700",
            contractor_address="2 Energy Ave",
            contractor_directors=["Dir1"],
            contract_value=5000000,
            currency="USD",
            award_date=date(2023, 5, 1),
            end_date=date(2028, 4, 30),
            description="Nuclear Research",
            contract_type="cost_plus",
            source_db="contract_db",
        )
        assert gc.contract_id == "GC-2"
        assert gc.contract_number == "CON-300"
        assert gc.agency == "DOE"
        assert gc.agency_address == "1 Energy St"
        assert gc.contractor_name == "Energy Corp"
        assert gc.contractor_registration_number == "REG-700"
        assert gc.contractor_address == "2 Energy Ave"
        assert gc.contractor_directors == ["Dir1"]
        assert gc.contract_value == 5000000
        assert gc.currency == "USD"
        assert gc.award_date == date(2023, 5, 1)
        assert gc.end_date == date(2028, 4, 30)
        assert gc.description == "Nuclear Research"
        assert gc.contract_type == "cost_plus"
        assert gc.source_db == "contract_db"

    def test_to_dict(self):
        gc = GovernmentContract(
            contract_id="GC-3",
            agency="VA",
            contractor_name="HealthCo",
            contract_value=200000,
        )
        d = gc.to_dict()
        assert d["contract_id"] == "GC-3"
        assert d["agency"] == "VA"
        assert "contractor_name" in d
        assert "contractor_directors" in d

    def test_from_dict(self):
        data = {
            "contract_id": "GC-4",
            "contract_number": "CON-400",
            "agency": "USDA",
            "agency_address": "3 Farm St",
            "contractor_name": "FarmCo",
            "contractor_registration_number": "REG-800",
            "contractor_address": "4 Farm Ave",
            "contractor_directors": ["Alice"],
            "contract_value": 350000,
            "currency": "USD",
            "award_date": "2023-09-01",
            "end_date": "2024-08-31",
            "description": "Agricultural Equipment",
            "contract_type": "fixed_price",
            "source_db": "gov_contract_db",
        }
        gc = GovernmentContract.from_dict(data)
        assert gc.contract_id == "GC-4"
        assert gc.contract_number == "CON-400"
        assert gc.agency == "USDA"
        assert gc.agency_address == "3 Farm St"
        assert gc.contractor_name == "FarmCo"
        assert gc.contractor_registration_number == "REG-800"
        assert gc.contractor_address == "4 Farm Ave"
        assert gc.contractor_directors == ["Alice"]
        assert gc.contract_value == 350000
        assert gc.currency == "USD"
        assert gc.award_date == date(2023, 9, 1)
        assert gc.end_date == date(2024, 8, 31)
        assert gc.description == "Agricultural Equipment"
        assert gc.contract_type == "fixed_price"
        assert gc.source_db == "gov_contract_db"

    def test_from_dict_missing_optional(self):
        data = {
            "contract_id": "GC-5",
            "agency": "Navy",
            "contractor_name": "NavalCo",
            "contract_value": 800000,
        }
        gc = GovernmentContract.from_dict(data)
        assert gc.contract_id == "GC-5"
        assert gc.agency == "Navy"
        assert gc.contractor_name == "NavalCo"
        assert gc.contract_value == 800000
        assert gc.contract_number is None
        assert gc.agency_address is None
        assert gc.contractor_registration_number is None
        assert gc.contractor_address is None
        assert gc.contractor_directors == []
        assert gc.currency is None
        assert gc.award_date is None
        assert gc.end_date is None
        assert gc.description is None
        assert gc.contract_type is None
        assert gc.source_db is None


# ==================== SEC_Filing ====================

class TestSECFiling:
    def test_create_minimal(self):
        sf = SEC_Filing(
            filing_id="SEC-1",
            company_name="Public Corp",
            filing_type="10-K",
        )
        assert sf.filing_id == "SEC-1"
        assert sf.company_name == "Public Corp"
        assert sf.filing_type == "10-K"
        assert sf.accession_number is None
        assert sf.company_cik is None
        assert sf.filing_date is None
        assert sf.period_end_date is None
        assert sf.document_url is None
        assert sf.sic_code is None
        assert sf.industry is None
        assert sf.revenue is None
        assert sf.net_income is None
        assert sf.total_assets is None
        assert sf.total_liabilities is None
        assert sf.shareholders_equity is None
        assert sf.filing_text_summary is None
        assert sf.source_db is None

    def test_create_full(self):
        sf = SEC_Filing(
            filing_id="SEC-2",
            accession_number="0001234567-23-000001",
            company_name="TechPublic Inc",
            company_cik="0001234567",
            filing_type="10-Q",
            filing_date=date(2023, 6, 15),
            period_end_date=date(2023, 6, 30),
            document_url="https://sec.gov/filings/SEC-2",
            sic_code="7372",
            industry="Software",
            revenue=15000000,
            net_income=2000000,
            total_assets=50000000,
            total_liabilities=20000000,
            shareholders_equity=30000000,
            filing_text_summary="Revenue up 10%",
            source_db="sec_edgar",
        )
        assert sf.filing_id == "SEC-2"
        assert sf.accession_number == "0001234567-23-000001"
        assert sf.company_name == "TechPublic Inc"
        assert sf.company_cik == "0001234567"
        assert sf.filing_type == "10-Q"
        assert sf.filing_date == date(2023, 6, 15)
        assert sf.period_end_date == date(2023, 6, 30)
        assert sf.document_url == "https://sec.gov/filings/SEC-2"
        assert sf.sic_code == "7372"
        assert sf.industry == "Software"
        assert sf.revenue == 15000000
        assert sf.net_income == 2000000
        assert sf.total_assets == 50000000
        assert sf.total_liabilities == 20000000
        assert sf.shareholders_equity == 30000000
        assert sf.filing_text_summary == "Revenue up 10%"
        assert sf.source_db == "sec_edgar"

    def test_to_dict(self):
        sf = SEC_Filing(
            filing_id="SEC-3",
            company_name="Finance Corp",
            filing_type="8-K",
        )
        d = sf.to_dict()
        assert d["filing_id"] == "SEC-3"
        assert d["company_name"] == "Finance Corp"
        assert "filing_type" in d
        assert "filing_date" in d

    def test_from_dict(self):
        data = {
            "filing_id": "SEC-4",
            "accession_number": "0001234567-23-000002",
            "company_name": "Retail Corp",
            "company_cik": "0001234567",
            "filing_type": "10-K",
            "filing_date": "2023-12-31",
            "period_end_date": "2023-12-31",
            "document_url": "https://sec.gov/filings/SEC-4",
            "sic_code": "5311",
            "industry": "Retail",
            "revenue": 100000000,
            "net_income": 10000000,
            "total_assets": 200000000,
            "total_liabilities": 80000000,
            "shareholders_equity": 120000000,
            "filing_text_summary": "Strong year",
            "source_db": "sec_edgar",
        }
        sf = SEC_Filing.from_dict(data)
        assert sf.filing_id == "SEC-4"
        assert sf.accession_number == "0001234567-23-000002"
        assert sf.company_name == "Retail Corp"
        assert sf.company_cik == "0001234567"
        assert sf.filing_type == "10-K"
        assert sf.filing_date == date(2023, 12, 31)
        assert sf.period_end_date == date(2023, 12, 31)
        assert sf.document_url == "https://sec.gov/filings/SEC-4"
        assert sf.sic_code == "5311"
        assert sf.industry == "Retail"
        assert sf.revenue == 100000000
        assert sf.net_income == 10000000
        assert sf.total_assets == 200000000
        assert sf.total_liabilities == 80000000
        assert sf.shareholders_equity == 120000000
        assert sf.filing_text_summary == "Strong year"
        assert sf.source_db == "sec_edgar"

    def test_from_dict_missing_optional(self):
        data = {
            "filing_id": "SEC-5",
            "company_name": "Simple Corp",
            "filing_type": "10-Q",
        }
        sf = SEC_Filing.from_dict(data)
        assert sf.filing_id == "SEC-5"
        assert sf.company_name == "Simple Corp"
        assert sf.filing_type == "10-Q"
        assert sf.accession_number is None
        assert sf.company_cik is None
        assert sf.filing_date is None
        assert sf.period_end_date is None
        assert sf.document_url is None
        assert sf.sic_code is None
        assert sf.industry is None
        assert sf.revenue is None
        assert sf.net_income is None
        assert sf.total_assets is None
        assert sf.total_liabilities is None
        assert sf.shareholders_equity is None
        assert sf.filing_text_summary is None
        assert sf.source_db is None
