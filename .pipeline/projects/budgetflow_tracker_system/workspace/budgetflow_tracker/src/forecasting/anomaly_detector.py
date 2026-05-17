"""Anomaly detection engine for BudgetFlow Tracker."""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database
from src.forecasting.models import AnomalyFlag

logger = logging.getLogger(__name__)


@dataclass
class _CategoryStats:
    """Running statistics for a category."""
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0  # For Welford's algorithm
    std: float = 0.0

    def update(self, value: float) -> None:
        """Update running statistics with a new value (Welford's online algorithm)."""
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2
        if self.count >= 2:
            self.std = math.sqrt(self.m2 / (self.count - 1))

    def z_score(self, value: float) -> float:
        """Calculate z-score for a value given current stats."""
        if self.std == 0 or self.count < 2:
            return 0.0
        return (value - self.mean) / self.std


class AnomalyDetector:
    """Detect anomalous transactions using statistical methods."""

    # Severity thresholds (in standard deviations)
    _SEVERITY_THRESHOLDS = {
        "low": 2.0,
        "medium": 3.0,
        "high": 4.0,
        "critical": 5.0,
    }

    def __init__(self, db: Database):
        self.db = db

    def detect_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        z_threshold: float = 3.0,
        min_samples: int = 5,
    ) -> list[AnomalyFlag]:
        """Detect anomalous transactions.

        Uses per-category statistical analysis to identify outliers.

        Args:
            start_date: Start of analysis window. Defaults to 365 days ago.
            end_date: End of analysis window. Defaults to today.
            z_threshold: Z-score threshold for flagging anomalies.
            min_samples: Minimum samples per category before flagging.

        Returns:
            List of AnomalyFlag objects sorted by deviation descending.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        # Fetch all transactions
        transactions = self.db.fetchall(
            """SELECT id, date, description, amount, category_name
               FROM transactions
               WHERE date >= ? AND date <= ?
               ORDER BY date ASC""",
            (start_date.isoformat(), end_date.isoformat()),
        )

        if not transactions:
            return []

        # Build per-category statistics (using first N-1 transactions as baseline)
        category_stats: dict[str, _CategoryStats] = defaultdict(_CategoryStats)
        transactions_by_category: dict[str, list[dict]] = defaultdict(list)

        for txn in transactions:
            cat = txn.get("category_name") or "Uncategorized"
            transactions_by_category[cat].append(txn)

        # Compute baseline stats for each category (first 70% as baseline)
        for cat, txns in transactions_by_category.items():
            baseline_count = max(min_samples, int(len(txns) * 0.7))
            for txn in txns[:baseline_count]:
                category_stats[cat].update(abs(txn["amount"]))

        # Detect anomalies in the remaining transactions
        anomalies: list[AnomalyFlag] = []
        for cat, txns in transactions_by_category.items():
            stats = category_stats[cat]
            if stats.count < min_samples:
                continue

            baseline_count = max(min_samples, int(len(txns) * 0.7))
            for txn in txns[baseline_count:]:
                amount = abs(txn["amount"])
                z_score = stats.z_score(amount)

                if abs(z_score) >= z_threshold:
                    severity = self._classify_severity(abs(z_score))
                    anomalies.append(AnomalyFlag(
                        transaction_id=txn.get("id"),
                        date=date.fromisoformat(txn["date"]),
                        description=txn.get("description") or "",
                        amount=txn["amount"],
                        category_name=txn.get("category_name"),
                        deviation_sigma=round(z_score, 2),
                        category_mean=round(stats.mean, 2),
                        category_std=round(stats.std, 2),
                        anomaly_type="amount_deviation",
                        severity=severity,
                    ))

        # Sort by absolute deviation descending
        anomalies.sort(key=lambda a: abs(a.deviation_sigma), reverse=True)

        logger.info("Detected %d anomalies (z_threshold=%.1f, min_samples=%d)",
                     len(anomalies), z_threshold, min_samples)
        return anomalies

    def detect_global_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        z_threshold: float = 3.0,
        min_samples: int = 5,
    ) -> list[AnomalyFlag]:
        """Detect global anomalies across all categories.

        Uses overall spending distribution to find outliers regardless of category.

        Args:
            start_date: Start of analysis window.
            end_date: End of analysis window.
            z_threshold: Z-score threshold.
            min_samples: Minimum samples before flagging.

        Returns:
            List of AnomalyFlag objects.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        transactions = self.db.fetchall(
            """SELECT id, date, description, amount, category_name
               FROM transactions
               WHERE date >= ? AND date <= ?
               ORDER BY date ASC""",
            (start_date.isoformat(), end_date.isoformat()),
        )

        if not transactions:
            return []

        # Compute global stats (first 70% as baseline)
        baseline_count = max(min_samples, int(len(transactions) * 0.7))
        global_stats = _CategoryStats()
        for txn in transactions[:baseline_count]:
            global_stats.update(abs(txn["amount"]))

        if global_stats.count < min_samples:
            return []

        # Detect anomalies
        anomalies: list[AnomalyFlag] = []
        for txn in transactions[baseline_count:]:
            amount = abs(txn["amount"])
            z_score = global_stats.z_score(amount)

            if abs(z_score) >= z_threshold:
                severity = self._classify_severity(abs(z_score))
                anomalies.append(AnomalyFlag(
                    transaction_id=txn.get("id"),
                    date=date.fromisoformat(txn["date"]),
                    description=txn.get("description") or "",
                    amount=txn["amount"],
                    category_name=txn.get("category_name"),
                    deviation_sigma=round(z_score, 2),
                    category_mean=round(global_stats.mean, 2),
                    category_std=round(global_stats.std, 2),
                    anomaly_type="global_outlier",
                    severity=severity,
                ))

        anomalies.sort(key=lambda a: abs(a.deviation_sigma), reverse=True)
        return anomalies

    def detect_daily_spending_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        z_threshold: float = 2.5,
        min_samples: int = 10,
    ) -> list[AnomalyFlag]:
        """Detect days with unusually high or low spending.

        Aggregates daily totals and finds outliers in the daily spending distribution.

        Args:
            start_date: Start of analysis window.
            end_date: End of analysis window.
            z_threshold: Z-score threshold.
            min_samples: Minimum days before flagging.

        Returns:
            List of AnomalyFlag objects.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        daily_totals = self.db.fetchall(
            """SELECT date,
                      SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                      SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses,
                      ABS(SUM(amount)) as net
               FROM transactions
               WHERE date >= ? AND date <= ?
               GROUP BY date
               ORDER BY date ASC""",
            (start_date.isoformat(), end_date.isoformat()),
        )

        if not daily_totals or len(daily_totals) < min_samples:
            return []

        # Use total spending (expenses) as the metric
        expenses_list = [d["expenses"] for d in daily_totals if d["expenses"] > 0]
        if not expenses_list:
            return []

        baseline_count = max(min_samples, int(len(expenses_list) * 0.7))
        stats = _CategoryStats()
        for amt in expenses_list[:baseline_count]:
            stats.update(amt)

        if stats.count < min_samples:
            return []

        anomalies: list[AnomalyFlag] = []
        for i, d in enumerate(daily_totals):
            if d["expenses"] <= 0:
                continue

            idx = expenses_list.index(d["expenses"])
            if idx >= baseline_count:
                z_score = stats.z_score(d["expenses"])
                if abs(z_score) >= z_threshold:
                    severity = self._classify_severity(abs(z_score))
                    anomalies.append(AnomalyFlag(
                        date=date.fromisoformat(d["date"]),
                        description="Daily spending anomaly",
                        amount=-d["expenses"],
                        category_name="Daily Total",
                        deviation_sigma=round(z_score, 2),
                        category_mean=round(stats.mean, 2),
                        category_std=round(stats.std, 2),
                        anomaly_type="daily_spending",
                        severity=severity,
                    ))

        anomalies.sort(key=lambda a: abs(a.deviation_sigma), reverse=True)
        return anomalies

    def _classify_severity(self, abs_z: float) -> str:
        """Classify anomaly severity based on z-score magnitude."""
        for severity, threshold in sorted(self._SEVERITY_THRESHOLDS.items(),
                                          key=lambda x: x[1], reverse=True):
            if abs_z >= threshold:
                return severity
        return "low"

    def get_category_baseline(self, category_name: str) -> dict:
        """Get baseline statistics for a category.

        Args:
            category_name: Category to analyze.

        Returns:
            Dict with count, mean, std, min, max.
        """
        txn = self.db.fetchone(
            """SELECT COUNT(*) as count,
                      AVG(ABS(amount)) as mean,
                      MIN(ABS(amount)) as min_amt,
                      MAX(ABS(amount)) as max_amt
               FROM transactions
               WHERE category_name = ?""",
            (category_name,),
        )

        if not txn or txn["count"] < 2:
            return {"count": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        # Calculate std
        amounts = self.db.fetchall(
            """SELECT ABS(amount) as amt
               FROM transactions
               WHERE category_name = ?""",
            (category_name,),
        )
        mean = txn["mean"]
        if amounts:
            variance = sum((a["amt"] - mean) ** 2 for a in amounts) / (len(amounts) - 1)
            std = math.sqrt(variance) if variance > 0 else 0.0
        else:
            std = 0.0

        return {
            "count": txn["count"],
            "mean": round(float(mean), 2),
            "std": round(std, 2),
            "min": round(float(txn["min_amt"]), 2),
            "max": round(float(txn["max_amt"]), 2),
        }
