"""Time-bucketing engine for grouping transactions into configurable intervals."""

from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database
from src.forecasting.models import IntervalType, TimeSeriesBucket

logger = logging.getLogger(__name__)


@dataclass
class _BucketConfig:
    """Internal configuration for a bucket interval."""
    interval_type: IntervalType
    start_date: date
    end_date: date


def _get_month_end(year: int, month: int) -> date:
    """Get the last day of a given month."""
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def _get_week_end(week_start: date) -> date:
    """Get the Sunday of the week starting on week_start (Monday)."""
    return week_start + timedelta(days=6)


def _get_quarter_end(year: int, quarter: int) -> date:
    """Get the last day of a given quarter (Q1=Mar, Q2=Jun, Q3=Sep, Q4=Dec)."""
    month = quarter * 3
    return _get_month_end(year, month)


def _get_quarter_start(year: int, quarter: int) -> date:
    """Get the first day of a given quarter."""
    month = (quarter - 1) * 3 + 1
    return date(year, month, 1)


def _get_bucket_for_date(
    target_date: date,
    interval_type: IntervalType,
) -> _BucketConfig:
    """Determine which bucket a target_date falls into.

    Args:
        target_date: The date to bucket.
        interval_type: The type of interval.

    Returns:
        _BucketConfig with start and end dates.
    """
    if interval_type == IntervalType.DAILY:
        return _BucketConfig(
            interval_type=interval_type,
            start_date=target_date,
            end_date=target_date,
        )

    if interval_type == IntervalType.WEEKLY:
        # Weeks start on Monday
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        return _BucketConfig(
            interval_type=interval_type,
            start_date=week_start,
            end_date=_get_week_end(week_start),
        )

    if interval_type == IntervalType.MONTHLY:
        return _BucketConfig(
            interval_type=interval_type,
            start_date=date(target_date.year, target_date.month, 1),
            end_date=_get_month_end(target_date.year, target_date.month),
        )

    if interval_type == IntervalType.QUARTERLY:
        quarter = (target_date.month - 1) // 3 + 1
        return _BucketConfig(
            interval_type=interval_type,
            start_date=_get_quarter_start(target_date.year, quarter),
            end_date=_get_quarter_end(target_date.year, quarter),
        )

    raise ValueError(f"Unsupported interval type: {interval_type}")


class TimeBucketEngine:
    """Engine for bucketing transactions into time intervals."""

    def __init__(self, db: Database):
        self.db = db

    def get_buckets(
        self,
        interval_type: IntervalType,
        start_date: date,
        end_date: date,
    ) -> list[TimeSeriesBucket]:
        """Get all buckets in the given date range.

        Args:
            interval_type: Type of interval (daily, weekly, monthly, quarterly).
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).

        Returns:
            List of TimeSeriesBucket objects sorted by start_date.
        """
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        # Generate all bucket configs in range
        buckets = self._generate_bucket_configs(interval_type, start_date, end_date)

        # Fetch transaction totals for each bucket
        results = []
        for bucket in buckets:
            bucket_data = self._fetch_bucket_data(bucket)
            results.append(bucket_data)

        return results

    def _generate_bucket_configs(
        self,
        interval_type: IntervalType,
        start_date: date,
        end_date: date,
    ) -> list[_BucketConfig]:
        """Generate all bucket configs spanning start_date to end_date."""
        configs: list[_BucketConfig] = []
        current = start_date

        while current <= end_date:
            bucket = _get_bucket_for_date(current, interval_type)
            # Only add if this bucket overlaps with our range
            if bucket.start_date <= end_date and bucket.end_date >= start_date:
                configs.append(bucket)
            # Move to next bucket
            if interval_type == IntervalType.DAILY:
                current += timedelta(days=1)
            elif interval_type == IntervalType.WEEKLY:
                current += timedelta(weeks=1)
            elif interval_type == IntervalType.MONTHLY:
                # Advance to next month
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)
            elif interval_type == IntervalType.QUARTERLY:
                quarter = (current.month - 1) // 3 + 1
                next_quarter = quarter + 1
                if next_quarter > 4:
                    next_quarter = 1
                    current = date(current.year + 1, 1, 1)
                else:
                    current = _get_quarter_start(current.year, next_quarter)
            else:
                raise ValueError(f"Unsupported interval type: {interval_type}")

        return configs

    def _fetch_bucket_data(self, bucket: _BucketConfig) -> TimeSeriesBucket:
        """Fetch transaction data for a single bucket."""
        query = """
            SELECT
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expenses,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= ? AND date <= ?
        """
        row = self.db.fetchone(query, (bucket.start_date.isoformat(), bucket.end_date.isoformat()))

        total_income = float(row["total_income"]) if row and row["total_income"] else 0.0
        total_expenses = float(row["total_expenses"]) if row and row["total_expenses"] else 0.0

        return TimeSeriesBucket(
            interval_type=bucket.interval_type,
            start_date=bucket.start_date,
            end_date=bucket.end_date,
            total_income=total_income,
            total_expenses=total_expenses,
            net_flow=total_income - total_expenses,
            transaction_count=int(row["transaction_count"]) if row and row["transaction_count"] else 0,
        )

    def get_daily_buckets(self, start_date: date, end_date: date) -> list[TimeSeriesBucket]:
        """Shortcut for daily bucketing."""
        return self.get_buckets(IntervalType.DAILY, start_date, end_date)

    def get_weekly_buckets(self, start_date: date, end_date: date) -> list[TimeSeriesBucket]:
        """Shortcut for weekly bucketing."""
        return self.get_buckets(IntervalType.WEEKLY, start_date, end_date)

    def get_monthly_buckets(self, start_date: date, end_date: date) -> list[TimeSeriesBucket]:
        """Shortcut for monthly bucketing."""
        return self.get_buckets(IntervalType.MONTHLY, start_date, end_date)

    def get_quarterly_buckets(self, start_date: date, end_date: date) -> list[TimeSeriesBucket]:
        """Shortcut for quarterly bucketing."""
        return self.get_buckets(IntervalType.QUARTERLY, start_date, end_date)
