"""Mock competitor price data sources for testing."""

from datetime import datetime
from typing import List

from .models import CompetitorPrice


class MockAPISource:
    """A mock competitor source that returns hardcoded prices.

    Simulates an API that provides competitor pricing data.
    """

    @property
    def source_name(self) -> str:
        """Return the lowercase source name for PriceSnapshot.source."""
        return "mock_api"

    def fetch_prices(self, product_id: str) -> List[CompetitorPrice]:
        """Return hardcoded competitor prices for the given product_id.

        Args:
            product_id: The product identifier to fetch prices for.

        Returns:
            A list of at least 2 CompetitorPrice entries with different
            competitor names and prices.
        """
        return [
            CompetitorPrice(
                product_id=product_id,
                competitor_name="CompetitorA",
                price=9.99,
                last_updated=datetime.now(),
            ),
            CompetitorPrice(
                product_id=product_id,
                competitor_name="CompetitorB",
                price=10.49,
                last_updated=datetime.now(),
            ),
        ]


class MockCSVSource:
    """A mock competitor source that parses inline CSV strings.

    Simulates a CSV-based data source where prices are embedded as
    comma-separated values.
    """

    @property
    def source_name(self) -> str:
        """Return the lowercase source name for PriceSnapshot.source."""
        return "mock_csv"

    def __init__(self, csv_data: str = ""):
        """Initialize with optional CSV data.

        Args:
            csv_data: CSV string with header row. Expected format:
                      competitor_name,price
                      CompX,12.99
                      CompY,13.49
        """
        self.csv_data = csv_data

    def fetch_prices(self, product_id: str) -> List[CompetitorPrice]:
        """Parse inline CSV data and return CompetitorPrice objects.

        Args:
            product_id: The product identifier to associate with the prices.

        Returns:
            A list of CompetitorPrice entries parsed from the CSV data.
        """
        if not self.csv_data:
            # Default CSV data if none provided
            self.csv_data = "competitor_name,price\nCompetitorC,11.99\nCompetitorD,12.49"

        lines = self.csv_data.strip().split("\n")
        if len(lines) < 2:
            return []

        prices = []
        for line in lines[1:]:  # Skip header
            parts = line.split(",")
            if len(parts) == 2:
                competitor_name = parts[0].strip()
                try:
                    price = float(parts[1].strip())
                    prices.append(
                        CompetitorPrice(
                            product_id=product_id,
                            competitor_name=competitor_name,
                            price=price,
                            last_updated=datetime.now(),
                        )
                    )
                except ValueError:
                    continue
        return prices
