"""PriceTracker engine for managing competitor price data sources."""

from datetime import datetime
from typing import List, Optional

from .models import CompetitorPrice, PriceSnapshot


class PriceTracker:
    """Manages competitor price data sources and polls for price snapshots.

    Attributes:
        sources: List of data sources that provide CompetitorPrice data.
    """

    def __init__(self):
        """Initialize an empty PriceTracker with no sources."""
        self._sources: list = []

    def add_source(self, source) -> None:
        """Add a data source to the tracker.

        Args:
            source: An object with a fetch_prices(product_id) method
                    that returns a list of CompetitorPrice.
        """
        if source not in self._sources:
            self._sources.append(source)

    def remove_source(self, source) -> None:
        """Remove a data source from the tracker.

        Args:
            source: The source object to remove.
        """
        if source in self._sources:
            self._sources.remove(source)

    def poll_all(self) -> List[PriceSnapshot]:
        """Poll all registered sources and return PriceSnapshot objects.

        Iterates over all registered sources, calls fetch_prices on each,
        and converts CompetitorPrice objects to PriceSnapshot objects
        with the current timestamp and source name.

        Returns:
            A list of PriceSnapshot objects from all sources.
        """
        snapshots = []
        now = datetime.now()
        for source in self._sources:
            source_name = getattr(source, "source_name", type(source).__name__)
            competitor_prices = source.fetch_prices("")
            for cp in competitor_prices:
                snapshot = PriceSnapshot(
                    product_id=cp.product_id,
                    competitor=cp.competitor_name,
                    price=cp.price,
                    timestamp=now,
                    source=source_name,
                )
                snapshots.append(snapshot)
        return snapshots

    def poll_for_product(self, product_id: str) -> List[PriceSnapshot]:
        """Poll all registered sources for a specific product_id.

        Args:
            product_id: The product to poll prices for.

        Returns:
            A list of PriceSnapshot objects for the given product_id.
        """
        snapshots = []
        now = datetime.now()
        for source in self._sources:
            source_name = getattr(source, "source_name", type(source).__name__)
            competitor_prices = source.fetch_prices(product_id)
            for cp in competitor_prices:
                snapshot = PriceSnapshot(
                    product_id=cp.product_id,
                    competitor=cp.competitor_name,
                    price=cp.price,
                    timestamp=now,
                    source=source_name,
                )
                snapshots.append(snapshot)
        return snapshots

    def get_current_price(self, product_id: str) -> Optional[PriceSnapshot]:
        """Return the latest PriceSnapshot for a given product_id.

        Polls all sources specifically for the given product_id and returns
        the most recent snapshot.

        Args:
            product_id: The product to look up.

        Returns:
            The most recent PriceSnapshot for the product, or None if
            no data exists for that product.
        """
        snapshots = []
        now = datetime.now()
        for source in self._sources:
            source_name = type(source).__name__
            competitor_prices = source.fetch_prices(product_id)
            for cp in competitor_prices:
                snapshot = PriceSnapshot(
                    product_id=cp.product_id,
                    competitor=cp.competitor_name,
                    price=cp.price,
                    timestamp=now,
                    source=source_name,
                )
                snapshots.append(snapshot)

        product_snapshots = [s for s in snapshots if s.product_id == product_id]
        if not product_snapshots:
            return None
        return max(product_snapshots, key=lambda s: s.timestamp)
