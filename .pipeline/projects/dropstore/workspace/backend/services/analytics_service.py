"""Analytics service for store metrics and reporting."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from backend.models.analytics import DailyMetrics, ProductPerformance, AnalyticsSnapshot
from backend.utils.database import async_session_factory


def _generate_snapshot_id() -> str:
    """Generate a unique snapshot ID."""
    return f"snap_{uuid.uuid4().hex[:12]}"


async def record_daily_metrics(
    store_id: str,
    date: datetime,
    page_views: int = 0,
    unique_visitors: int = 0,
    sessions: int = 0,
    bounce_rate: float = 0.0,
    revenue: float = 0.0,
    orders: int = 0,
    avg_order_value: float = 0.0,
    conversion_rate: float = 0.0,
    top_referrer: Optional[str] = None,
) -> DailyMetrics:
    """Record daily metrics for a store."""
    # Check if metrics already exist for this date
    async with async_session_factory() as session:
        existing = await session.execute(
            DailyMetrics.__table__.select().where(
                (DailyMetrics.store_id == store_id) &
                (DailyMetrics.date == date)
            )
        )
        existing_metrics = existing.scalar_one_or_none()

        if existing_metrics:
            # Update existing metrics
            existing_metrics.page_views = page_views
            existing_metrics.unique_visitors = unique_visitors
            existing_metrics.sessions = sessions
            existing_metrics.bounce_rate = bounce_rate
            existing_metrics.revenue = revenue
            existing_metrics.orders = orders
            existing_metrics.avg_order_value = avg_order_value
            existing_metrics.conversion_rate = conversion_rate
            existing_metrics.top_referrer = top_referrer
            await session.commit()
            await session.refresh(existing_metrics)
            return existing_metrics
        else:
            # Create new metrics
            metrics = DailyMetrics(
                store_id=store_id,
                date=date,
                page_views=page_views,
                unique_visitors=unique_visitors,
                sessions=sessions,
                bounce_rate=bounce_rate,
                revenue=revenue,
                orders=orders,
                avg_order_value=avg_order_value,
                conversion_rate=conversion_rate,
                top_referrer=top_referrer,
            )
            session.add(metrics)
            await session.commit()
            await session.refresh(metrics)
            return metrics


async def get_daily_metrics(
    store_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[DailyMetrics]:
    """Get daily metrics for a store within a date range."""
    async with async_session_factory() as session:
        query = DailyMetrics.__table__.select().where(DailyMetrics.store_id == store_id)
        if start_date:
            query = query.where(DailyMetrics.date >= start_date)
        if end_date:
            query = query.where(DailyMetrics.date <= end_date)
        query = query.order_by(DailyMetrics.date)
        metrics = await session.execute(query)
        return list(metrics.scalars().all())


async def get_aggregated_metrics(
    store_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get aggregated metrics for a store within a date range."""
    async with async_session_factory() as session:
        query = DailyMetrics.__table__.select().where(DailyMetrics.store_id == store_id)
        if start_date:
            query = query.where(DailyMetrics.date >= start_date)
        if end_date:
            query = query.where(DailyMetrics.date <= end_date)
        metrics = await session.execute(query)
        metrics_list = list(metrics.scalars().all())

        if not metrics_list:
            return {
                "total_revenue": 0.0,
                "total_orders": 0,
                "total_page_views": 0,
                "total_unique_visitors": 0,
                "total_sessions": 0,
                "avg_bounce_rate": 0.0,
                "avg_order_value": 0.0,
                "avg_conversion_rate": 0.0,
                "days_tracked": 0,
            }

        total_revenue = sum(m.revenue for m in metrics_list)
        total_orders = sum(m.orders for m in metrics_list)
        total_page_views = sum(m.page_views for m in metrics_list)
        total_unique_visitors = sum(m.unique_visitors for m in metrics_list)
        total_sessions = sum(m.sessions for m in metrics_list)
        avg_bounce_rate = sum(m.bounce_rate for m in metrics_list) / len(metrics_list)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
        avg_conversion_rate = sum(m.conversion_rate for m in metrics_list) / len(metrics_list)

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_page_views": total_page_views,
            "total_unique_visitors": total_unique_visitors,
            "total_sessions": total_sessions,
            "avg_bounce_rate": avg_bounce_rate,
            "avg_order_value": avg_order_value,
            "avg_conversion_rate": avg_conversion_rate,
            "days_tracked": len(metrics_list),
        }


async def record_product_performance(
    product_id: str,
    store_id: str,
    product_title: str,
    total_views: int = 0,
    total_add_to_cart: int = 0,
    total_purchases: int = 0,
    total_revenue: float = 0.0,
    total_profit: float = 0.0,
    avg_position: float = 0.0,
) -> ProductPerformance:
    """Record or update product performance metrics."""
    async with async_session_factory() as session:
        existing = await session.execute(
            ProductPerformance.__table__.select().where(
                (ProductPerformance.product_id == product_id) &
                (ProductPerformance.store_id == store_id)
            )
        )
        existing_perf = existing.scalar_one_or_none()

        if existing_perf:
            existing_perf.total_views = total_views
            existing_perf.total_add_to_cart = total_add_to_cart
            existing_perf.total_purchases = total_purchases
            existing_perf.total_revenue = total_revenue
            existing_perf.total_profit = total_profit
            existing_perf.avg_position = avg_position
            existing_perf.last_viewed_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(existing_perf)
            return existing_perf
        else:
            perf = ProductPerformance(
                product_id=product_id,
                store_id=store_id,
                product_title=product_title,
                total_views=total_views,
                total_add_to_cart=total_add_to_cart,
                total_purchases=total_purchases,
                total_revenue=total_revenue,
                total_profit=total_profit,
                avg_position=avg_position,
                last_viewed_at=datetime.now(timezone.utc),
            )
            session.add(perf)
            await session.commit()
            await session.refresh(perf)
            return perf


async def get_product_performance(product_id: str, store_id: str) -> Optional[ProductPerformance]:
    """Get product performance metrics."""
    async with async_session_factory() as session:
        perf = await session.execute(
            ProductPerformance.__table__.select().where(
                (ProductPerformance.product_id == product_id) &
                (ProductPerformance.store_id == store_id)
            )
        )
        return perf.scalar_one_or_none()


async def get_top_products(
    store_id: str,
    limit: int = 10,
    metric: str = "revenue",
) -> List[ProductPerformance]:
    """Get top performing products for a store."""
    async with async_session_factory() as session:
        if metric == "revenue":
            query = ProductPerformance.__table__.select().where(
                ProductPerformance.store_id == store_id
            ).order_by(ProductPerformance.total_revenue.desc()).limit(limit)
        elif metric == "purchases":
            query = ProductPerformance.__table__.select().where(
                ProductPerformance.store_id == store_id
            ).order_by(ProductPerformance.total_purchases.desc()).limit(limit)
        elif metric == "views":
            query = ProductPerformance.__table__.select().where(
                ProductPerformance.store_id == store_id
            ).order_by(ProductPerformance.total_views.desc()).limit(limit)
        else:
            query = ProductPerformance.__table__.select().where(
                ProductPerformance.store_id == store_id
            ).order_by(ProductPerformance.total_revenue.desc()).limit(limit)

        products = await session.execute(query)
        return list(products.scalars().all())


async def create_analytics_snapshot(
    store_id: str,
    period_start: datetime,
    period_end: datetime,
    total_revenue: float = 0.0,
    total_orders: int = 0,
    total_products_sold: int = 0,
    avg_order_value: float = 0.0,
    total_visitors: int = 0,
    conversion_rate: float = 0.0,
    top_categories: Optional[List[str]] = None,
    top_products: Optional[List[str]] = None,
) -> AnalyticsSnapshot:
    """Create an analytics snapshot for trend analysis."""
    snapshot_id = _generate_snapshot_id()

    snapshot = AnalyticsSnapshot(
        snapshot_id=snapshot_id,
        store_id=store_id,
        period_start=period_start,
        period_end=period_end,
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_products_sold=total_products_sold,
        avg_order_value=avg_order_value,
        total_visitors=total_visitors,
        conversion_rate=conversion_rate,
        top_categories=top_categories or [],
        top_products=top_products or [],
    )

    async with async_session_factory() as session:
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
    return snapshot


async def get_analytics_snapshots(
    store_id: str,
    limit: int = 30,
) -> List[AnalyticsSnapshot]:
    """Get analytics snapshots for a store."""
    async with async_session_factory() as session:
        snapshots = await session.execute(
            AnalyticsSnapshot.__table__.select().where(
                AnalyticsSnapshot.store_id == store_id
            ).order_by(AnalyticsSnapshot.period_start.desc()).limit(limit)
        )
        return list(snapshots.scalars().all())
