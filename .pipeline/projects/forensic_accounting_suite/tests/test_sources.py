"""Tests for data sources."""

import unittest
from datetime import date

from forensic_accounting_suite.sources.corporate_registry import CorporateRegistrySource
from forensic_accounting_suite.sources.shipping_manifests import ShippingManifestSource
from forensic_accounting_suite.sources.procurement import ProcurementSource


class TestCorporateRegistrySource(unittest.TestCase):
    def test_fetch_all_returns_list(self):
        source = CorporateRegistrySource()
        results = source.fetch_all()
        self.assertIsInstance(results, list)

    def test_fetch_all_has_entries(self):
        source = CorporateRegistrySource()
        results = source.fetch_all()
        self.assertGreater(len(results), 0)

    def test_entry_fields(self):
        source = CorporateRegistrySource()
        results = source.fetch_all()
        entry = results[0]
        self.assertIsNotNone(entry.registration_number)
        self.assertIsNotNone(entry.company_name)

    def test_fetch_by_registration(self):
        source = CorporateRegistrySource()
        results = source.fetch_all()
        first_reg = results[0].registration_number
        found = source.fetch_by_registration(first_reg)
        self.assertIsNotNone(found)
        self.assertEqual(found.registration_number, first_reg)

    def test_fetch_by_registration_not_found(self):
        source = CorporateRegistrySource()
        found = source.fetch_by_registration("NONEXISTENT")
        self.assertIsNone(found)


class TestShippingManifestSource(unittest.TestCase):
    def test_fetch_all_returns_list(self):
        source = ShippingManifestSource()
        results = source.fetch_all()
        self.assertIsInstance(results, list)

    def test_fetch_all_has_entries(self):
        source = ShippingManifestSource()
        results = source.fetch_all()
        self.assertGreater(len(results), 0)

    def test_entry_fields(self):
        source = ShippingManifestSource()
        results = source.fetch_all()
        entry = results[0]
        self.assertIsNotNone(entry.manifest_id)
        self.assertIsNotNone(entry.vessel_name)


class TestProcurementSource(unittest.TestCase):
    def test_fetch_all_returns_list(self):
        source = ProcurementSource()
        results = source.fetch_all()
        self.assertIsInstance(results, list)

    def test_fetch_all_has_entries(self):
        source = ProcurementSource()
        results = source.fetch_all()
        self.assertGreater(len(results), 0)

    def test_entry_fields(self):
        source = ProcurementSource()
        results = source.fetch_all()
        entry = results[0]
        self.assertIsNotNone(entry.procurement_id)
        self.assertIsNotNone(entry.vendor_name)


if __name__ == "__main__":
    unittest.main()
