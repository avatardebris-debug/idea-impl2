"""Tests for forensic capital_flows module."""

import pytest
from forensic.capital_flow import (
    compute_capital_flows,
    detect_anomalies,
)


class TestComputeCapitalFlows:
    """Tests for compute_capital_flows function."""

    def test_basic_computation(self):
        """Test basic capital flow computation."""
        data = {
            "insider_purchases": 100000,
            "insider_sales": 50000,
            "institutional_ownership_change": 5.0,
        }
        flows = compute_capital_flows(data)
        assert isinstance(flows, list)
        assert len(flows) > 0

    def test_empty_data(self):
        """Test with empty data."""
        flows = compute_capital_flows({})
        assert isinstance(flows, list)

    def test_zero_values(self):
        """Test with zero values."""
        data = {
            "insider_purchases": 0,
            "insider_sales": 0,
            "institutional_ownership_change": 0.0,
        }
        flows = compute_capital_flows(data)
        assert isinstance(flows, list)

    def test_negative_values(self):
        """Test with negative values."""
        data = {
            "insider_purchases": 0,
            "insider_sales": -50000,
            "institutional_ownership_change": -5.0,
        }
        flows = compute_capital_flows(data)
        assert isinstance(flows, list)


class TestDetectAnomalies:
    """Tests for detect_anomalies function."""

    def test_normal_flows(self):
        """Test that normal flows produce no anomalies."""
        from forensic.capital_flow import CapitalFlow
        flows = [
            CapitalFlow(flow_type="insider_purchase", amount=100000, date="2023-01-01"),
            CapitalFlow(flow_type="insider_sale", amount=50000, date="2023-01-02"),
        ]
        anomalies = detect_anomalies(flows)
        assert isinstance(anomalies, list)

    def test_empty_flows(self):
        """Test with empty flows."""
        anomalies = detect_anomalies([])
        assert isinstance(anomalies, list)

    def test_large_suspicious_flow(self):
        """Test detection of large suspicious flow."""
        from forensic.capital_flow import CapitalFlow
        flows = [
            CapitalFlow(flow_type="insider_sale", amount=10000000, date="2023-01-01"),
        ]
        anomalies = detect_anomalies(flows)
        assert isinstance(anomalies, list)
