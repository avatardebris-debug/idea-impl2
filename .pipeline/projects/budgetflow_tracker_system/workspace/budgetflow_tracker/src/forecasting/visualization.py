"""Visualization module for BudgetFlow Tracker."""

from __future__ import annotations

import io
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from src.forecasting.models import (
    CashFlowProjection,
    CategoryProjection,
    ChartOutput,
    ForecastPoint,
)

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates static chart images using matplotlib."""

    def __init__(self, width: int = 800, height: int = 600, dpi: int = 100):
        self.width = width
        self.height = height
        self.dpi = dpi

    def generate_trend_chart(
        self,
        dates: list[date],
        values: list[float],
        title: str = "Spending Trend",
        output_path: Optional[str] = None,
    ) -> ChartOutput:
        """Generate a line chart showing spending trends over time."""
        fig, ax = plt.subplots(figsize=(self.width / self.dpi, self.height / self.dpi))
        ax.plot(dates, values, marker="o", markersize=3, linewidth=1.5, color="#2196F3")
        ax.fill_between(dates, values, alpha=0.15, color="#2196F3")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel("Amount ($)", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha="right")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            logger.info(f"Trend chart saved to {output_path}")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self.dpi, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return ChartOutput(
            chart_type="trend",
            output_path=output_path or "",
            width=self.width,
            height=self.height,
            title=title,
            data_points=len(dates),
        )

    def generate_category_chart(
        self,
        categories: list[CategoryProjection],
        title: str = "Spending by Category",
        output_path: Optional[str] = None,
    ) -> ChartOutput:
        """Generate a pie chart showing spending distribution by category."""
        if not categories:
            raise ValueError("No categories to chart")

        labels = [c.category_name for c in categories]
        sizes = [float(c.daily_forecasts[-1].predicted_value) if c.daily_forecasts else 0 for c in categories]
        colors = plt.cm.Set3(range(len(categories)))

        fig, ax = plt.subplots(figsize=(self.width / self.dpi, self.height / self.dpi))
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
            textprops={"fontsize": 9},
        )
        for autotext in autotexts:
            autotext.set_fontsize(8)
        ax.set_title(title, fontsize=14, fontweight="bold")
        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            logger.info(f"Category chart saved to {output_path}")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self.dpi, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return ChartOutput(
            chart_type="category_pie",
            output_path=output_path or "",
            width=self.width,
            height=self.height,
            title=title,
            data_points=len(categories),
        )

    def generate_forecast_chart(
        self,
        projection: CashFlowProjection,
        output_path: Optional[str] = None,
    ) -> ChartOutput:
        """Generate a combined historical + forecast chart."""
        fig, ax = plt.subplots(figsize=(self.width / self.dpi, self.height / self.dpi))

        # Historical data
        hist_dates = []
        hist_values = []
        for fp in projection.daily_forecasts:
            # This is a bit hacky - we need actual historical data
            # For now, use the forecast points as a proxy
            pass

        # Use the daily forecasts as the main visualization
        forecast_dates = [fp.date for fp in projection.daily_forecasts]
        forecast_values = [float(fp.predicted_value) for fp in projection.daily_forecasts]
        lower_bounds = [float(fp.lower_bound) for fp in projection.daily_forecasts]
        upper_bounds = [float(fp.upper_bound) for fp in projection.daily_forecasts]

        ax.plot(forecast_dates, forecast_values, marker="o", markersize=3, linewidth=2, color="#4CAF50", label="Forecast")
        ax.fill_between(forecast_dates, lower_bounds, upper_bounds, alpha=0.2, color="#4CAF50", label="95% Confidence Interval")

        ax.set_title("Cash Flow Forecast", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel("Amount ($)", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha="right")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            logger.info(f"Forecast chart saved to {output_path}")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self.dpi, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return ChartOutput(
            chart_type="forecast",
            output_path=output_path or "",
            width=self.width,
            height=self.height,
            title="Cash Flow Forecast",
            data_points=len(forecast_dates),
        )

    def generate_all_charts(
        self,
        projection: CashFlowProjection,
        output_dir: Optional[str] = None,
    ) -> list[ChartOutput]:
        """Generate all available charts for a projection."""
        charts: list[ChartOutput] = []

        # Generate trend chart (using daily totals from historical data)
        # For simplicity, use the forecast data as a proxy
        if projection.daily_forecasts:
            dates = [fp.date for fp in projection.daily_forecasts]
            values = [float(fp.predicted_value) for fp in projection.daily_forecasts]
            trend_chart = self.generate_trend_chart(
                dates, values, "Projected Daily Spending",
                output_path=f"{output_dir}/trend.png" if output_dir else None,
            )
            charts.append(trend_chart)

        # Generate category chart
        if projection.category_projections:
            category_chart = self.generate_category_chart(
                projection.category_projections,
                output_path=f"{output_dir}/categories.png" if output_dir else None,
            )
            charts.append(category_chart)

        # Generate forecast chart
        forecast_chart = self.generate_forecast_chart(
            projection,
            output_path=f"{output_dir}/forecast.png" if output_dir else None,
        )
        charts.append(forecast_chart)

        return charts
