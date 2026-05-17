"""Tests for anomaly detection."""

import unittest
from datetime import date

from forensic_accounting_suite.engine.anomaly_detection import AnomalyDetector, Anomaly
from forensic_accounting_suite.core.models import CorporateRegistryEntry, ProcurementRecord


class TestAnomalyDetector(unittest.TestCase):
    def setUp(self):
        """Create test data with known anomalies."""
        self.shell_company = CorporateRegistryEntry(
            registration_number="SHELL-001",
            company_name="Shell Corp",
            incorporation_date=date(2022, 1, 1),
            registered_address="",  # No address
            directors=["John Doe"],  # Minimal directors
            officers=[],  # No officers
            naics_code="",
            share_capital=500.0,  # Very low
            status="active",
        )
        self.normal_company = CorporateRegistryEntry(
            registration_number="NORMAL-001",
            company_name="Normal Corp",
            incorporation_date=date(2010, 1, 1),
            registered_address="123 Main St",
            directors=["John Doe", "Jane Smith", "Bob Wilson"],
            officers=["Jane Smith", "Bob Wilson"],
            naics_code="5415",
            share_capital=100000.0,
            status="active",
        )
        self.rapid_company = CorporateRegistryEntry(
            registration_number="RAPID-001",
            company_name="Rapid Corp",
            incorporation_date=date(2023, 1, 1),
            registered_address="456 Oak Ave",
            directors=["Alice Brown"],
            officers=["Alice Brown"],
            naics_code="5415",
            share_capital=10000.0,
            status="active",
        )
        self.procurements = [
            ProcurementRecord(
                procurement_id="PROC-001",
                vendor_name="Shell Corp",
                vendor_address="789 Fake St",
                vendor_registration_number="SHELL-001",
                description="Consulting",
                total_value=500000.0,
                award_date=date(2023, 6, 1),
                contract_start_date=date(2023, 6, 1),
                contract_end_date=date(2024, 6, 1),
                naics_code="5415",
                funding_agency="Dept of Technology",
            ),
            ProcurementRecord(
                procurement_id="PROC-002",
                vendor_name="Normal Corp",
                vendor_address="123 Main St",
                vendor_registration_number="NORMAL-001",
                description="IT services",
                total_value=100000.0,
                award_date=date(2023, 7, 1),
                contract_start_date=date(2023, 7, 1),
                contract_end_date=date(2024, 7, 1),
                naics_code="5415",
                funding_agency="Dept of Technology",
            ),
            ProcurementRecord(
                procurement_id="PROC-003",
                vendor_name="Rapid Corp",
                vendor_address="456 Oak Ave",
                vendor_registration_number="RAPID-001",
                description="Software development",
                total_value=200000.0,
                award_date=date(2023, 3, 1),  # 2 months after incorporation
                contract_start_date=date(2023, 3, 1),
                contract_end_date=date(2024, 3, 1),
                naics_code="5415",
                funding_agency="Dept of Technology",
            ),
            ProcurementRecord(
                procurement_id="PROC-004",
                vendor_name="Another Corp",
                vendor_address="100 Other St",
                vendor_registration_number="ANOTHER-001",
                description="Hardware",
                total_value=100000.0,
                award_date=date(2023, 8, 1),
                contract_start_date=date(2023, 8, 1),
                contract_end_date=date(2024, 8, 1),
                naics_code="5415",
                funding_agency="Dept of Technology",
            ),
            ProcurementRecord(
                procurement_id="PROC-005",
                vendor_name="Yet Another Corp",
                vendor_address="200 Yet St",
                vendor_registration_number="YET-001",
                description="Supplies",
                total_value=100000.0,
                award_date=date(2023, 9, 1),
                contract_start_date=date(2023, 9, 1),
                contract_end_date=date(2024, 9, 1),
                naics_code="5415",
                funding_agency="Dept of Technology",
            ),
        ]

    def test_detect_all_returns_list(self):
        detector = AnomalyDetector(
            registry_entries=[self.shell_company, self.normal_company],
            procurements=self.procurements,
        )
        anomalies = detector.detect_all()
        self.assertIsInstance(anomalies, list)
        self.assertGreater(len(anomalies), 0)

    def test_shell_company_detected(self):
        detector = AnomalyDetector(
            registry_entries=[self.shell_company],
        )
        anomalies = detector.detect_all()
        shell_anomalies = [a for a in anomalies if a.anomaly_type == "shell_company_indicator"]
        self.assertGreater(len(shell_anomalies), 0)
        # Should be high severity (3+ indicators)
        for a in shell_anomalies:
            self.assertEqual(a.entity_id, "SHELL-001")

    def test_normal_company_not_flagged_as_shell(self):
        detector = AnomalyDetector(
            registry_entries=[self.normal_company],
        )
        anomalies = detector.detect_all()
        shell_anomalies = [a for a in anomalies if a.anomaly_type == "shell_company_indicator"]
        self.assertEqual(len(shell_anomalies), 0)

    def test_value_outliers_detected(self):
        detector = AnomalyDetector(
            procurements=self.procurements,
        )
        anomalies = detector.detect_all()
        outlier_anomalies = [a for a in anomalies if a.anomaly_type == "value_outlier"]
        # PROC-001 ($500k) should be an outlier vs the others ($100k)
        self.assertGreater(len(outlier_anomalies), 0)

    def test_rapid_formation_detected(self):
        detector = AnomalyDetector(
            registry_entries=[self.rapid_company],
            procurements=self.procurements,
        )
        anomalies = detector.detect_all()
        rapid_anomalies = [a for a in anomalies if a.anomaly_type == "rapid_formation_contract"]
        self.assertGreater(len(rapid_anomalies), 0)
        for a in rapid_anomalies:
            self.assertEqual(a.entity_id, "RAPID-001")

    def test_minimal_disclosure_detected(self):
        detector = AnomalyDetector(
            registry_entries=[self.shell_company],
        )
        anomalies = detector.detect_all()
        disclosure_anomalies = [a for a in anomalies if a.anomaly_type == "minimal_disclosure"]
        self.assertGreater(len(disclosure_anomalies), 0)

    def test_anomaly_to_dict(self):
        anomaly = Anomaly(
            entity_type="company",
            entity_id="TEST-001",
            anomaly_type="test_type",
            severity="high",
            description="Test description",
            details={"key": "value"},
        )
        d = anomaly.to_dict()
        self.assertEqual(d["entity_type"], "company")
        self.assertEqual(d["entity_id"], "TEST-001")
        self.assertEqual(d["anomaly_type"], "test_type")
        self.assertEqual(d["severity"], "high")
        self.assertEqual(d["description"], "Test description")
        self.assertEqual(d["details"], {"key": "value"})

    def test_no_anomalies_with_normal_data(self):
        normal = CorporateRegistryEntry(
            registration_number="NORM-001",
            company_name="Normal Corp",
            incorporation_date=date(2010, 1, 1),
            registered_address="123 Main St",
            directors=["John Doe", "Jane Smith"],
            officers=["Jane Smith"],
            naics_code="5415",
            share_capital=100000.0,
            status="active",
        )
        normal_procurements = [
            ProcurementRecord(
                procurement_id="PROC-001",
                vendor_name="Normal Corp",
                vendor_address="123 Main St",
                vendor_registration_number="NORM-001",
                description="IT services",
                total_value=100000.0,
                award_date=date(2023, 6, 1),
                contract_start_date=date(2023, 6, 1),
                contract_end_date=date(2024, 6, 1),
                naics_code="5415",
                funding_agency="Dept of Technology",
            ),
        ]
        detector = AnomalyDetector(
            registry_entries=[normal],
            procurements=normal_procurements,
        )
        anomalies = detector.detect_all()
        # Should have no shell company or rapid formation anomalies
        shell_anomalies = [a for a in anomalies if a.anomaly_type == "shell_company_indicator"]
        rapid_anomalies = [a for a in anomalies if a.anomaly_type == "rapid_formation_contract"]
        self.assertEqual(len(shell_anomalies), 0)
        self.assertEqual(len(rapid_anomalies), 0)

    def test_empty_data_no_anomalies(self):
        detector = AnomalyDetector(
            registry_entries=[],
            procurements=[],
        )
        anomalies = detector.detect_all()
        self.assertEqual(len(anomalies), 0)

    def test_severity_levels(self):
        detector = AnomalyDetector(
            registry_entries=[self.shell_company],
        )
        anomalies = detector.detect_all()
        for anomaly in anomalies:
            self.assertIn(anomaly.severity, ["low", "medium", "high", "critical"])


if __name__ == "__main__":
    unittest.main()
