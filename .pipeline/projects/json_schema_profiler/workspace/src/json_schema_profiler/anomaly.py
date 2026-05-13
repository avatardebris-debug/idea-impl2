"""Anomaly detection module for json_schema_profiler.

Detects per-field anomalies including:
- Null rate anomalies
- Numeric outliers (IQR method)
- Cardinality anomalies (high-cardinality strings)
- Numeric skew detection
"""

from __future__ import annotations

import math
from typing import Any


def detect_anomalies(
    data: Any,
    thresholds: dict[str, float] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Detect anomalies in the provided data.

    Args:
        data: A dict or list of dicts representing the dataset.
        thresholds: Optional threshold overrides.
            - null_rate: float (default 0.10) — null pct threshold
            - iqr_multiplier: float (default 1.5) — IQR multiplier for outliers
            - cardinality_threshold: int (default 50) — unique values threshold
            - skew_threshold: float (default 2.0) — |skew| threshold

    Returns:
        A dict keyed by field name, each value being a list of anomaly dicts.
        Each anomaly dict has keys: type, confidence, suggested_fix, details.
    """
    if thresholds is None:
        thresholds = {}

    null_rate_threshold = thresholds.get("null_rate", 0.10)
    iqr_multiplier = thresholds.get("iqr_multiplier", 1.5)
    cardinality_threshold = thresholds.get("cardinality_threshold", 50)
    skew_threshold = thresholds.get("skew_threshold", 2.0)

    # Normalize data to list of dicts
    objects = _normalize_data(data)

    if not objects:
        return {}

    # Collect all field names
    all_fields: set[str] = set()
    for obj in objects:
        all_fields.update(obj.keys())

    anomalies: dict[str, list[dict[str, Any]]] = {field: [] for field in sorted(all_fields)}

    for field in sorted(all_fields):
        values = [obj.get(field) for obj in objects]
        field_anomalies = _detect_field_anomalies(
            values, field, null_rate_threshold, iqr_multiplier,
            cardinality_threshold, skew_threshold,
        )
        anomalies[field] = field_anomalies

    return anomalies


def _normalize_data(data: Any) -> list[dict]:
    """Normalize input data to a list of dicts."""
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _detect_field_anomalies(
    values: list[Any],
    field: str,
    null_rate_threshold: float,
    iqr_multiplier: float,
    cardinality_threshold: int,
    skew_threshold: float,
) -> list[dict[str, Any]]:
    """Detect anomalies for a single field's values."""
    anomalies: list[dict[str, Any]] = []

    null_count = sum(1 for v in values if v is None)
    non_null = [v for v in values if v is not None]

    # 1. Null rate anomaly
    if len(values) > 0:
        null_pct = null_count / len(values)
        if null_pct > null_rate_threshold:
            anomalies.append({
                "type": "null_rate",
                "confidence": min(1.0, null_pct),
                "suggested_fix": f"Investigate why {null_pct:.1%} of values for '{field}' are null. Consider adding a default value or marking the field as required.",
                "details": {
                    "null_count": null_count,
                    "total_count": len(values),
                    "null_pct": round(null_pct, 4),
                    "threshold": null_rate_threshold,
                },
            })

    if not non_null:
        return anomalies

    # 2. Numeric outlier detection (IQR method)
    numeric_vals = _extract_numeric(non_null)
    if numeric_vals:
        outlier_anomaly = _detect_numeric_outliers(numeric_vals, field, iqr_multiplier)
        if outlier_anomaly:
            anomalies.append(outlier_anomaly)

    # 3. Cardinality anomaly (high-cardinality strings)
    string_vals = [v for v in non_null if isinstance(v, str)]
    if string_vals:
        unique_count = len(set(string_vals))
        if unique_count > cardinality_threshold:
            anomalies.append({
                "type": "cardinality",
                "confidence": min(1.0, unique_count / (cardinality_threshold * 2)),
                "suggested_fix": f"Field '{field}' has {unique_count} unique string values (>{cardinality_threshold}). Consider using a reference table or categorizing values.",
                "details": {
                    "unique_count": unique_count,
                    "total_count": len(string_vals),
                    "threshold": cardinality_threshold,
                },
            })

    # 4. Skew detection for numeric fields
    if numeric_vals and len(numeric_vals) >= 3:
        skew_anomaly = _detect_skew(numeric_vals, field, skew_threshold)
        if skew_anomaly:
            anomalies.append(skew_anomaly)

    return anomalies


def _extract_numeric(values: list[Any]) -> list[float]:
    """Extract numeric values from a list, excluding booleans."""
    result = []
    for v in values:
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            result.append(float(v))
    return result


def _detect_numeric_outliers(
    numeric_vals: list[float],
    field: str,
    iqr_multiplier: float,
) -> dict[str, Any] | None:
    """Detect numeric outliers using the IQR method."""
    if len(numeric_vals) < 4:
        return None

    sorted_vals = sorted(numeric_vals)
    n = len(sorted_vals)

    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    q1 = sorted_vals[q1_idx]
    q3 = sorted_vals[q3_idx]
    iqr = q3 - q1

    if iqr == 0:
        return None

    lower_bound = q1 - iqr_multiplier * iqr
    upper_bound = q3 + iqr_multiplier * iqr

    outliers = [v for v in numeric_vals if v < lower_bound or v > upper_bound]
    outlier_pct = len(outliers) / len(numeric_vals)

    if outlier_pct > 0.01:  # At least 1% outliers
        confidence = min(1.0, outlier_pct * 10)  # Scale up for confidence
        return {
            "type": "numeric_outlier",
            "confidence": round(confidence, 4),
            "suggested_fix": f"Field '{field}' has {len(outliers)} outlier values ({outlier_pct:.1%}). Review data collection or consider capping/extending bounds.",
            "details": {
                "outlier_count": len(outliers),
                "total_count": len(numeric_vals),
                "outlier_pct": round(outlier_pct, 4),
                "iqr": round(iqr, 4),
                "lower_bound": round(lower_bound, 4),
                "upper_bound": round(upper_bound, 4),
                "iqr_multiplier": iqr_multiplier,
            },
        }
    return None


def _detect_skew(
    numeric_vals: list[float],
    field: str,
    skew_threshold: float,
) -> dict[str, Any] | None:
    """Detect numeric skew using Fisher-Pearson coefficient."""
    n = len(numeric_vals)
    if n < 3:
        return None

    mean = sum(numeric_vals) / n
    if mean == 0:
        return None

    variance = sum((x - mean) ** 2 for x in numeric_vals) / n
    if variance == 0:
        return None

    std = math.sqrt(variance)
    if std == 0:
        return None

    # Fisher-Pearson skewness coefficient
    skew = (n / (n - 1)) * (
        sum(((x - mean) / std) ** 3 for x in numeric_vals) / n
    )

    if abs(skew) > skew_threshold:
        confidence = min(1.0, abs(skew) / (skew_threshold * 2))
        direction = "right" if skew > 0 else "left"
        return {
            "type": "skew",
            "confidence": round(confidence, 4),
            "suggested_fix": f"Field '{field}' has {direction}-skewed distribution (skew={skew:.3f}). Consider log transform or binning for normalization.",
            "details": {
                "skew": round(skew, 4),
                "mean": round(mean, 4),
                "std": round(std, 4),
                "threshold": skew_threshold,
                "direction": direction,
            },
        }
    return None


def _compute_skew(values: list[float]) -> float:
    """Compute Fisher-Pearson skewness coefficient."""
    n = len(values)
    if n < 3:
        return 0.0
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return (n / (n - 1)) * (sum(((x - mean) / std) ** 3 for x in values) / n)
