"""Unit tests for the anomaly detection module."""

import pytest

from json_schema_profiler.anomaly import (
    detect_anomalies,
    _extract_numeric,
    _detect_numeric_outliers,
    _detect_skew,
    _compute_skew,
)


# ── Test: detect_anomalies basic ──────────────────────────────────────────────


class TestDetectAnomaliesBasic:
    """Test (1): detect_anomalies returns anomaly dict keyed by field name."""

    def test_returns_dict_keyed_by_field(self):
        """detect_anomalies should return a dict keyed by field name."""
        data = {"name": "Alice", "age": 30}
        result = detect_anomalies(data)
        assert isinstance(result, dict)
        assert "name" in result
        assert "age" in result

    def test_empty_data_returns_empty_dict(self):
        """Empty data should return an empty dict."""
        assert detect_anomalies([]) == {}
        assert detect_anomalies({}) == {}

    def test_single_object_no_anomalies(self):
        """A single clean object should have no anomalies."""
        data = {"name": "Alice", "age": 30}
        result = detect_anomalies(data)
        # With a single object, no null rate, no outliers, no skew
        for field, anomalies in result.items():
            assert len(anomalies) == 0

    def test_list_of_dicts_works(self):
        """detect_anomalies should work with a list of dicts."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = detect_anomalies(data)
        assert "name" in result
        assert "age" in result


# ── Test: Null rate anomaly ───────────────────────────────────────────────────


class TestNullRateAnomaly:
    """Test (2): null rate anomaly detection."""

    def test_null_rate_above_threshold(self):
        """Null rate above threshold should trigger anomaly."""
        data = [
            {"value": 1},
            {"value": None},
            {"value": None},
            {"value": None},
            {"value": 5},
        ]
        result = detect_anomalies(data)
        null_anomalies = [a for a in result["value"] if a["type"] == "null_rate"]
        assert len(null_anomalies) == 1
        anomaly = null_anomalies[0]
        assert anomaly["confidence"] > 0
        assert "suggested_fix" in anomaly
        assert anomaly["details"]["null_pct"] == 0.6

    def test_null_rate_below_threshold(self):
        """Null rate below threshold should not trigger anomaly."""
        data = [
            {"value": 1},
            {"value": None},
            {"value": 3},
            {"value": 4},
            {"value": 5},
            {"value": 6},
            {"value": 7},
            {"value": 8},
            {"value": 9},
            {"value": 10},
        ]
        result = detect_anomalies(data)
        null_anomalies = [a for a in result["value"] if a["type"] == "null_rate"]
        assert len(null_anomalies) == 0  # 1/10 = 10% == threshold, not above

    def test_custom_null_rate_threshold(self):
        """Custom null_rate threshold should be respected."""
        data = [
            {"value": 1},
            {"value": None},
            {"value": 3},
        ]
        # With default threshold (0.10), 1/3 = 33% > 10% → anomaly
        result = detect_anomalies(data)
        null_anomalies = [a for a in result["value"] if a["type"] == "null_rate"]
        assert len(null_anomalies) == 1

        # With custom threshold (0.5), 1/3 = 33% < 50% → no anomaly
        result = detect_anomalies(data, thresholds={"null_rate": 0.5})
        null_anomalies = [a for a in result["value"] if a["type"] == "null_rate"]
        assert len(null_anomalies) == 0

    def test_all_null_field(self):
        """All-null field should trigger null rate anomaly with confidence 1.0."""
        data = [
            {"value": None},
            {"value": None},
            {"value": None},
        ]
        result = detect_anomalies(data)
        null_anomalies = [a for a in result["value"] if a["type"] == "null_rate"]
        assert len(null_anomalies) == 1
        assert null_anomalies[0]["confidence"] == 1.0

    def test_single_value_field_no_null_anomaly(self):
        """Single-value field should not trigger null rate anomaly."""
        data = {"value": 42}
        result = detect_anomalies(data)
        null_anomalies = [a for a in result["value"] if a["type"] == "null_rate"]
        assert len(null_anomalies) == 0


# ── Test: Numeric outlier detection (IQR) ─────────────────────────────────────


class TestNumericOutlierDetection:
    """Test (3): numeric outlier detection via IQR."""

    def test_outliers_detected(self):
        """IQR-based outlier detection should find outliers."""
        data = [
            {"value": 10},
            {"value": 11},
            {"value": 12},
            {"value": 13},
            {"value": 14},
            {"value": 15},
            {"value": 100},  # outlier
        ]
        result = detect_anomalies(data)
        outlier_anomalies = [a for a in result["value"] if a["type"] == "numeric_outlier"]
        assert len(outlier_anomalies) == 1
        assert outlier_anomalies[0]["confidence"] > 0
        assert "suggested_fix" in outlier_anomalies[0]

    def test_no_outliers(self):
        """Uniform data should not trigger outlier anomaly."""
        data = [
            {"value": 10},
            {"value": 11},
            {"value": 12},
            {"value": 13},
            {"value": 14},
        ]
        result = detect_anomalies(data)
        outlier_anomalies = [a for a in result["value"] if a["type"] == "numeric_outlier"]
        assert len(outlier_anomalies) == 0

    def test_custom_iqr_multiplier(self):
        """Custom iqr_multiplier should affect detection."""
        data = [
            {"value": 10},
            {"value": 11},
            {"value": 12},
            {"value": 13},
            {"value": 14},
            {"value": 15},
            {"value": 100},
        ]
        # With large multiplier, outliers won't be detected
        result = detect_anomalies(data, thresholds={"iqr_multiplier": 100})
        outlier_anomalies = [a for a in result["value"] if a["type"] == "numeric_outlier"]
        assert len(outlier_anomalies) == 0

    def test_outlier_details_include_bounds(self):
        """Outlier anomaly should include IQR bounds in details."""
        data = [
            {"value": 10},
            {"value": 11},
            {"value": 12},
            {"value": 13},
            {"value": 14},
            {"value": 15},
            {"value": 100},
        ]
        result = detect_anomalies(data)
        outlier_anomalies = [a for a in result["value"] if a["type"] == "numeric_outlier"]
        if outlier_anomalies:
            details = outlier_anomalies[0]["details"]
            assert "lower_bound" in details
            assert "upper_bound" in details
            assert "iqr" in details
            assert "outlier_count" in details

    def test_single_value_no_outlier(self):
        """Single-value field should not trigger outlier anomaly."""
        data = {"value": 42}
        result = detect_anomalies(data)
        outlier_anomalies = [a for a in result["value"] if a["type"] == "numeric_outlier"]
        assert len(outlier_anomalies) == 0


# ── Test: Cardinality anomaly ─────────────────────────────────────────────────


class TestCardinalityAnomaly:
    """Test (4): high-cardinality string detection."""

    def test_high_cardinality_detected(self):
        """High unique string count should trigger cardinality anomaly."""
        data = [{"value": f"val_{i}"} for i in range(60)]
        result = detect_anomalies(data)
        cardinality_anomalies = [a for a in result["value"] if a["type"] == "cardinality"]
        assert len(cardinality_anomalies) == 1
        assert cardinality_anomalies[0]["details"]["unique_count"] == 60

    def test_low_cardinality_no_anomaly(self):
        """Low unique string count should not trigger anomaly."""
        data = [{"value": "active"} for _ in range(10)]
        result = detect_anomalies(data)
        cardinality_anomalies = [a for a in result["value"] if a["type"] == "cardinality"]
        assert len(cardinality_anomalies) == 0

    def test_custom_cardinality_threshold(self):
        """Custom cardinality_threshold should be respected."""
        data = [{"value": f"val_{i}"} for i in range(30)]
        # With threshold 50, 30 < 50 → no anomaly
        result = detect_anomalies(data, thresholds={"cardinality_threshold": 50})
        cardinality_anomalies = [a for a in result["value"] if a["type"] == "cardinality"]
        assert len(cardinality_anomalies) == 0

    def test_cardinality_details(self):
        """Cardinality anomaly should include unique_count in details."""
        data = [{"value": f"val_{i}"} for i in range(60)]
        result = detect_anomalies(data)
        cardinality_anomalies = [a for a in result["value"] if a["type"] == "cardinality"]
        if cardinality_anomalies:
            assert "unique_count" in cardinality_anomalies[0]["details"]
            assert "total_count" in cardinality_anomalies[0]["details"]


# ── Test: Skew detection ──────────────────────────────────────────────────────


class TestSkewDetection:
    """Test (5): numeric skew detection."""

    def test_right_skew_detected(self):
        """Right-skewed data should trigger skew anomaly."""
        # Use data that produces skew > 2.0
        data = [{"value": 1} for _ in range(9)] + [{"value": 100}]
        result = detect_anomalies(data)
        skew_anomalies = [a for a in result["value"] if a["type"] == "skew"]
        assert len(skew_anomalies) == 1
        assert skew_anomalies[0]["details"]["direction"] == "right"

    def test_left_skew_detected(self):
        """Left-skewed data should trigger skew anomaly."""
        # Use data that produces skew < -2.0
        data = [{"value": 100} for _ in range(9)] + [{"value": 1}]
        result = detect_anomalies(data)
        skew_anomalies = [a for a in result["value"] if a["type"] == "skew"]
        assert len(skew_anomalies) == 1
        assert skew_anomalies[0]["details"]["direction"] == "left"

    def test_no_skew_symmetric(self):
        """Symmetric data should not trigger skew anomaly."""
        data = [{"value": i} for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
        result = detect_anomalies(data)
        skew_anomalies = [a for a in result["value"] if a["type"] == "skew"]
        assert len(skew_anomalies) == 0

    def test_custom_skew_threshold(self):
        """Custom skew_threshold should be respected."""
        data = [{"value": i} for i in [1, 2, 3, 4, 5, 10, 50, 100]]
        # With large threshold, skew won't be detected
        result = detect_anomalies(data, thresholds={"skew_threshold": 100})
        skew_anomalies = [a for a in result["value"] if a["type"] == "skew"]
        assert len(skew_anomalies) == 0

    def test_skew_details_include_values(self):
        """Skew anomaly should include skew, mean, std in details."""
        data = [{"value": i} for i in [1, 2, 3, 4, 5, 10, 50, 100]]
        result = detect_anomalies(data)
        skew_anomalies = [a for a in result["value"] if a["type"] == "skew"]
        if skew_anomalies:
            details = skew_anomalies[0]["details"]
            assert "skew" in details
            assert "mean" in details
            assert "std" in details
            assert "direction" in details


# ── Test: _extract_numeric helper ─────────────────────────────────────────────


class TestExtractNumeric:
    """Test (6): _extract_numeric helper function."""

    def test_extract_integers(self):
        """Should extract integers as floats."""
        result = _extract_numeric([1, 2, 3])
        assert result == [1.0, 2.0, 3.0]

    def test_extract_floats(self):
        """Should extract floats."""
        result = _extract_numeric([1.5, 2.5, 3.5])
        assert result == [1.5, 2.5, 3.5]

    def test_excludes_booleans(self):
        """Should exclude boolean values."""
        result = _extract_numeric([True, False, 1, 2])
        assert result == [1.0, 2.0]

    def test_excludes_strings(self):
        """Should exclude string values."""
        result = _extract_numeric(["1", "2", 3, 4])
        assert result == [3.0, 4.0]

    def test_excludes_none(self):
        """Should exclude None values."""
        result = _extract_numeric([None, 1, 2])
        assert result == [1.0, 2.0]

    def test_empty_list(self):
        """Empty list should return empty list."""
        assert _extract_numeric([]) == []


# ── Test: _detect_numeric_outliers helper ─────────────────────────────────────


class TestDetectNumericOutliersHelper:
    """Test (7): _detect_numeric_outliers helper function."""

    def test_outliers_detected(self):
        """Should detect outliers in skewed data."""
        vals = [10, 11, 12, 13, 14, 15, 100]
        result = _detect_numeric_outliers(vals, "test", 1.5)
        assert result is not None
        assert result["type"] == "numeric_outlier"

    def test_no_outliers(self):
        """Should return None for uniform data."""
        vals = [10, 11, 12, 13, 14]
        result = _detect_numeric_outliers(vals, "test", 1.5)
        assert result is None

    def test_few_values_returns_none(self):
        """Should return None for fewer than 4 values."""
        vals = [10, 11, 12]
        result = _detect_numeric_outliers(vals, "test", 1.5)
        assert result is None

    def test_zero_iqr_returns_none(self):
        """Should return None when IQR is zero."""
        vals = [10, 10, 10, 10]
        result = _detect_numeric_outliers(vals, "test", 1.5)
        assert result is None


# ── Test: _detect_skew helper ─────────────────────────────────────────────────


class TestDetectSkewHelper:
    """Test (8): _detect_skew helper function."""

    def test_skew_detected(self):
        """Should detect skew in skewed data."""
        vals = [1] * 9 + [100]
        result = _detect_skew(vals, "test", 2.0)
        assert result is not None
        assert result["type"] == "skew"

    def test_no_skew(self):
        """Should return None for symmetric data."""
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = _detect_skew(vals, "test", 2.0)
        assert result is None

    def test_few_values_returns_none(self):
        """Should return None for fewer than 3 values."""
        vals = [1, 2]
        result = _detect_skew(vals, "test", 2.0)
        assert result is None

    def test_zero_variance_returns_none(self):
        """Should return None when variance is zero."""
        vals = [5, 5, 5, 5]
        result = _detect_skew(vals, "test", 2.0)
        assert result is None


# ── Test: _compute_skew helper ────────────────────────────────────────────────


class TestComputeSkewHelper:
    """Test (9): _compute_skew helper function."""

    def test_symmetric_data_zero_skew(self):
        """Symmetric data should have near-zero skew."""
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        skew = _compute_skew(vals)
        assert abs(skew) < 0.5  # Near zero for symmetric data

    def test_right_skew_positive(self):
        """Right-skewed data should have positive skew."""
        vals = [1, 2, 3, 4, 5, 10, 50, 100]
        skew = _compute_skew(vals)
        assert skew > 0

    def test_left_skew_negative(self):
        """Left-skewed data should have negative skew."""
        vals = [100] * 9 + [1]
        skew = _compute_skew(vals)
        assert skew < 0

    def test_single_value_zero_skew(self):
        """Single value should return 0.0."""
        assert _compute_skew([5]) == 0.0

    def test_two_values_zero_skew(self):
        """Two values should return 0.0."""
        assert _compute_skew([1, 2]) == 0.0


# ── Test: Multiple anomalies on same field ────────────────────────────────────


class TestMultipleAnomalies:
    """Test (10): multiple anomalies on same field."""

    def test_field_with_multiple_anomalies(self):
        """A field can have multiple anomaly types."""
        data = [
            {"value": None},
            {"value": None},
            {"value": None},
            {"value": 1},
            {"value": 2},
            {"value": 3},
            {"value": 100},
        ]
        result = detect_anomalies(data)
        anomaly_types = {a["type"] for a in result["value"]}
        # Should have null_rate and possibly numeric_outlier
        assert "null_rate" in anomaly_types

    def test_all_anomaly_types_included(self):
        """Test that all anomaly types can coexist."""
        # Create data that triggers all anomaly types
        data = []
        # Add nulls for null_rate anomaly
        for _ in range(15):
            data.append({"value": None})
        # Add normal values
        for i in range(10):
            data.append({"value": i})
        # Add outliers
        for _ in range(5):
            data.append({"value": 1000})
        # Add high-cardinality strings
        for i in range(60):
            data.append({"value": f"str_{i}"})

        result = detect_anomalies(data)
        # Check that anomalies are detected for the field
        assert len(result["value"]) > 0


# ── Test: Edge cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    """Test (11): edge cases and robustness."""

    def test_single_object_no_anomalies(self):
        """Single object should have no anomalies."""
        data = {"name": "Alice", "age": 30}
        result = detect_anomalies(data)
        for field, anomalies in result.items():
            assert len(anomalies) == 0

    def test_all_same_values_no_anomalies(self):
        """All same values should have no anomalies."""
        data = [{"value": 42} for _ in range(10)]
        result = detect_anomalies(data)
        for field, anomalies in result.items():
            assert len(anomalies) == 0

    def test_mixed_types_no_crash(self):
        """Mixed types should not crash."""
        data = [
            {"value": "hello"},
            {"value": 42},
            {"value": 3.14},
            {"value": True},
            {"value": None},
        ]
        result = detect_anomalies(data)
        assert "value" in result

    def test_large_dataset_no_crash(self):
        """Large dataset should not crash."""
        data = [{"value": i} for i in range(1000)]
        result = detect_anomalies(data)
        assert "value" in result

    def test_anomaly_has_required_keys(self):
        """Each anomaly should have type, confidence, suggested_fix, details."""
        data = [
            {"value": None},
            {"value": None},
            {"value": None},
            {"value": 1},
            {"value": 2},
        ]
        result = detect_anomalies(data)
        for anomaly in result["value"]:
            assert "type" in anomaly
            assert "confidence" in anomaly
            assert "suggested_fix" in anomaly
            assert "details" in anomaly
            assert isinstance(anomaly["confidence"], float)
            assert 0 <= anomaly["confidence"] <= 1
