"""Integration test for the full forensic accounting pipeline."""

import unittest
import json

from forensic_accounting_suite.pipeline import ForensicPipeline
from forensic_accounting_suite.core.models import CorporateRegistryEntry, ShippingManifest, ProcurementRecord
from datetime import date


class TestForensicPipeline(unittest.TestCase):
    def setUp(self):
        """Create test data for the pipeline."""
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
                registered_address="123 Main St",
                directors=["John Doe", "Bob Wilson"],
                officers=["Bob Wilson"],
                naics_code="5416",
                share_capital=50000.0,
                status="active",
            ),
            CorporateRegistryEntry(
                registration_number="SHELL-001",
                company_name="Shell Corp",
                incorporation_date=date(2022, 1, 1),
                registered_address="",
                directors=["John Doe"],
                officers=[],
                naics_code="",
                share_capital=500.0,
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
        ]
        self.procurements = [
            ProcurementRecord(
                procurement_id="PROC-001",
                vendor_name="Acme Corp",
                vendor_address="123 Main St",
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
                vendor_name="Shell Corp",
                vendor_address="789 Fake St",
                vendor_registration_number="SHELL-001",
                description="Consulting",
                total_value=500000.0,
                award_date=date(2023, 7, 1),
                contract_start_date=date(2023, 7, 1),
                contract_end_date=date(2024, 7, 1),
                naics_code="5415",
                funding_agency="Dept of Homeland Security",
            ),
        ]

    def test_run_pipeline_returns_dict(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        self.assertIsInstance(result, dict)

    def test_pipeline_result_has_all_sections(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        self.assertIn("summary", result)
        self.assertIn("anomalies", result)
        self.assertIn("correlation_links", result)
        self.assertIn("key_findings", result)

    def test_pipeline_detects_shell_company(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        anomaly_ids = [a["entity_id"] for a in result["anomalies"]]
        self.assertIn("SHELL-001", anomaly_ids)

    def test_pipeline_detects_correlation_links(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        self.assertGreater(len(result["correlation_links"]), 0)

    def test_pipeline_detects_value_outlier(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        anomaly_types = [a["anomaly_type"] for a in result["anomalies"]]
        self.assertIn("value_outlier", anomaly_types)

    def test_pipeline_text_report(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        text_report = pipeline.generate_text_report(result)
        self.assertIsInstance(text_report, str)
        self.assertIn("FORENSIC ACCOUNTING ANALYSIS REPORT", text_report)
        self.assertIn("SHELL-001", text_report)

    def test_pipeline_json_report(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        json_report = pipeline.generate_json_report(result)
        self.assertIsInstance(json_report, dict)
        self.assertIn("summary", json_report)

    def test_pipeline_empty_data(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=[],
            shipping_manifests=[],
            procurements=[],
        )
        self.assertEqual(result["summary"]["total_links"], 0)
        self.assertEqual(result["summary"]["total_anomalies"], 0)

    def test_pipeline_serializable_result(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        # Should not raise
        json_str = json.dumps(result)
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 0)

    def test_pipeline_key_findings(self):
        pipeline = ForensicPipeline()
        result = pipeline.run(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
        )
        findings = result["key_findings"]
        self.assertGreater(len(findings), 0)
        # Should mention shell companies
        self.assertTrue(
            any("shell" in f.lower() for f in findings),
            f"Expected shell company finding, got: {findings}",
        )


if __name__ == "__main__":
    unittest.main()
