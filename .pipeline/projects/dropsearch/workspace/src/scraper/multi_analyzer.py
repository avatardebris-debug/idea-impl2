"""Multi-store competitor analysis orchestrator."""

import logging
from typing import List, Optional

from src.models.store_analysis import StoreAnalysis, CompetitorComparison
from src.scraper.browser import BrowserFetcher
from src.scraper.extractor import ProductExtractor
from src.scraper.supplier_detector import SupplierDetector

logger = logging.getLogger(__name__)


class MultiStoreAnalyzer:
    """Fetches, extracts, and compares multiple competitor stores."""

    def __init__(
        self,
        browser_fetcher: Optional[BrowserFetcher] = None,
        product_extractor: Optional[ProductExtractor] = None,
        supplier_detector: Optional[SupplierDetector] = None,
    ):
        self.fetcher = browser_fetcher or BrowserFetcher()
        self.extractor = product_extractor or ProductExtractor()
        self.detector = supplier_detector or SupplierDetector()

    def analyze(self, urls: List[str]) -> List[StoreAnalysis]:
        """Analyze multiple competitor stores.

        Args:
            urls: List of store URLs to analyze.

        Returns:
            List of StoreAnalysis objects, one per URL.
        """
        analyses: List[StoreAnalysis] = []
        for url in urls:
            analysis = self._analyze_single(url)
            analyses.append(analysis)
        return analyses

    def compare(self, urls: List[str]) -> CompetitorComparison:
        """Analyze and compare multiple competitor stores.

        Args:
            urls: List of store URLs to analyze and compare.

        Returns:
            CompetitorComparison with overlaps, price gaps, and insights.
        """
        stores = self.analyze(urls)
        return self._build_comparison(stores)

    def _analyze_single(self, url: str) -> StoreAnalysis:
        """Analyze a single store URL."""
        logger.info(f"Analyzing store: {url}")

        # Fetch HTML
        html = self.fetcher.fetch(url)
        if not html:
            logger.warning(f"Could not fetch HTML from {url}")
            return StoreAnalysis(
                stores_url=url,
                platform="Unknown",
                products=[],
                supplier_info=[],
                raw_html="",
            )

        # Extract products
        products = self.extractor.extract(html, url)
        product_dicts = [p.model_dump() for p in products]

        # Detect supplier chains
        supplier_info = self.detector.detect(html)

        # Detect platform
        platform = self.extractor._detect_platform(html)

        analysis = StoreAnalysis(
            stores_url=url,
            platform=platform,
            products=product_dicts,
            supplier_info=supplier_info,
            raw_html=html,
        )
        logger.info(f"Analyzed {url}: {len(products)} products, {len(supplier_info)} supplier chains")
        return analysis

    def _build_comparison(self, stores: List[StoreAnalysis]) -> CompetitorComparison:
        """Build a CompetitorComparison from StoreAnalysis objects."""
        from src.analysis.overlap_detector import OverlapDetector
        from src.analysis.margin_analyzer import MarginAnalyzer

        overlap_detector = OverlapDetector()
        margin_analyzer = MarginAnalyzer()

        overlaps = overlap_detector.detect(stores)
        margins = margin_analyzer.analyze(stores)

        # Compute price gaps
        price_gaps = []
        for overlap in overlaps:
            prices = overlap.get("prices", {})
            if len(prices) >= 2:
                max_price = max(prices.values())
                min_price = min(prices.values())
                gap_pct = ((max_price - min_price) / max_price) * 100 if max_price > 0 else 0
                price_gaps.append({
                    "product_name": overlap["product_name"],
                    "store_prices": prices,
                    "max_price": max_price,
                    "min_price": min_price,
                    "gap_pct": round(gap_pct, 2),
                })

        # Generate insights
        insights = self._generate_insights(stores, overlaps, margins, price_gaps)

        return CompetitorComparison(
            stores=stores,
            product_overlaps=overlaps,
            price_gaps=price_gaps,
            margins=margins,
            insights=insights,
        )

    def _generate_insights(
        self,
        stores: List[StoreAnalysis],
        overlaps: List[dict],
        margins: List[dict],
        price_gaps: List[dict] = None,
    ) -> List[str]:
        """Generate actionable insights from analysis results."""
        insights = []

        # Insight: margin opportunities
        for margin in margins:
            if margin.get("margin_pct", 0) > 50:
                insights.append(
                    f"High margin opportunity: {margin['product_name']} has {margin['margin_pct']:.1f}% margin "
                    f"via {margin.get('supplier_source', 'unknown')}."
                )

        # Insight: price undercutting
        if price_gaps:
            for gap in [g for g in price_gaps if g.get("gap_pct", 0) > 20]:
                min_store = min(gap["store_prices"], key=gap["store_prices"].get)
                max_store = max(gap["store_prices"], key=gap["store_prices"].get)
                insights.append(
                    f"Price gap alert: '{gap['product_name']}' is {gap['gap_pct']:.1f}% cheaper at "
                    f"{min_store} ({gap['min_price']}) vs {max_store} ({gap['max_price']})."
                )

        # Insight: supplier detection
        for store in stores:
            for supplier in store.supplier_info:
                if supplier.confidence > 0.7:
                    insights.append(
                        f"Supplier detected: {store.stores_url} likely sources from {supplier.source} "
                        f"(confidence: {supplier.confidence:.0%})."
                    )

        if not insights:
            insights.append("No significant insights detected. Consider analyzing more stores or products.")

        return insights
