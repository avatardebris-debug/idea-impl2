"""
tests/test_report.py — unit tests for Phase 3: ReportBuilder, AlertEngine
"""
import pytest
import sys
import pathlib
import csv
import io

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from real_estate_listing_analyzer.fetcher import Listing
from real_estate_listing_analyzer.analyzer import TrendResult
from real_estate_listing_analyzer.report import ReportBuilder, AlertEngine, DealAlert


# ------ Fixtures ------

def _make_listing(
    zpid="12345",
    address="100 Main St",
    city="Beverly Hills",
    state="CA",
    zip_code="90210",
    bedrooms=3,
    bathrooms=2,
    sqft=1500,
    price=600000,
    price_per_sqft=400.0,
    days_on_market=10,
    zestimate=650000,
    neighborhood_score=75,
) -> Listing:
    return Listing(
        zpid=zpid, address=address, city=city, state=state, zip_code=zip_code,
        bedrooms=bedrooms, bathrooms=bathrooms, sqft=sqft, price=price,
        price_per_sqft=price_per_sqft, days_on_market=days_on_market,
        zestimate=zestimate, neighborhood_score=neighborhood_score,
    )


def _make_trend(
    zip_code="90210",
    listing_count=20,
    median_price=700000,
    median_price_per_sqft=500.0,
    price_slope_30d=1.5,
    price_slope_90d=2.0,
    price_slope_365d=3.0,
    median_dom=15.0,
    dom_std=5.0,
    list_to_sale_ratio=0.98,
    neighborhood_score=75.0,
) -> TrendResult:
    return TrendResult(
        zip_code=zip_code, listing_count=listing_count, median_price=median_price,
        median_price_per_sqft=median_price_per_sqft, price_slope_30d=price_slope_30d,
        price_slope_90d=price_slope_90d, price_slope_365d=price_slope_365d,
        median_dom=median_dom, dom_std=dom_std, list_to_sale_ratio=list_to_sale_ratio,
        neighborhood_score=neighborhood_score,
    )


# ------ AlertEngine tests ------

class TestAlertEngine:
    def test_no_deals_when_all_above_trend(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        listings = [
            _make_listing(price_per_sqft=550.0),
            _make_listing(price_per_sqft=600.0),
        ]
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals(listings, trend)
        assert len(deals) == 0

    def test_deals_below_threshold(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        listings = [
            _make_listing(price_per_sqft=400.0),  # 20% below
            _make_listing(price_per_sqft=490.0),  # 2% below — not a deal
            _make_listing(price_per_sqft=300.0),  # 40% below
        ]
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals(listings, trend)
        assert len(deals) == 2
        assert deals[0].discount_pct == pytest.approx(20.0)
        assert deals[1].discount_pct == pytest.approx(40.0)

    def test_custom_threshold(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        listings = [_make_listing(price_per_sqft=480.0)]  # 4% below
        engine = AlertEngine(threshold=3.0)
        deals = engine.find_deals(listings, trend)
        assert len(deals) == 1

    def test_empty_listings(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals([], trend)
        assert len(deals) == 0

    def test_zero_median_price(self):
        trend = _make_trend(median_price_per_sqft=0.0)
        listings = [_make_listing(price_per_sqft=400.0)]
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals(listings, trend)
        assert len(deals) == 0

    def test_none_price_per_sqft(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        listings = [_make_listing(price_per_sqft=None)]
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals(listings, trend)
        assert len(deals) == 0


# ------ ReportBuilder CSV tests ------

class TestReportBuilderCSV:
    def test_csv_header(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [_make_listing()]
        content = builder.build_csv(listings)
        reader = csv.reader(io.StringIO(content))
        header = next(reader)
        assert "zpid" in header
        assert "price_per_sqft" in header
        assert "neighborhood_score" in header

    def test_csv_row_count(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [_make_listing() for _ in range(5)]
        content = builder.build_csv(listings)
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) == 6  # 1 header + 5 data rows

    def test_csv_data_integrity(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listing = _make_listing(price=600000, price_per_sqft=400.0, zestimate=650000)
        listings = [listing]
        content = builder.build_csv(listings)
        reader = csv.DictReader(io.StringIO(content))
        row = next(reader)
        assert row["price"] == "600000"
        assert row["price_per_sqft"] == "400.0"
        assert row["neighborhood_score"] == "75.0"

    def test_csv_list_to_zestimate_ratio(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listing = _make_listing(price=500000, zestimate=500000)  # ratio = 1.0
        listings = [listing]
        content = builder.build_csv(listings)
        reader = csv.DictReader(io.StringIO(content))
        row = next(reader)
        assert row["list_to_zestimate_ratio"] == "1.0"


# ------ ReportBuilder PDF tests ------

class TestReportBuilderPDF:
    def test_pdf_generates_bytes(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [_make_listing() for _ in range(3)]
        pdf_bytes = builder.build_pdf(listings)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_pdf_size_sanity(self):
        """PDF should be at least a few KB (contains chart image)."""
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [_make_listing() for _ in range(10)]
        pdf_bytes = builder.build_pdf(listings)
        assert len(pdf_bytes) > 5000  # reasonable minimum for PDF with chart

    def test_pdf_with_deals(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        listings = [
            _make_listing(price_per_sqft=400.0),
            _make_listing(price_per_sqft=600.0),
        ]
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals(listings, trend)
        builder = ReportBuilder(trend=trend, deals=deals)
        pdf_bytes = builder.build_pdf(listings)
        assert len(pdf_bytes) > 0
        # PDF should contain "Deal" text
        assert b"Deal" in pdf_bytes

    def test_pdf_empty_listings(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        pdf_bytes = builder.build_pdf([])
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


# ------ ReportBuilder Markdown tests ------

class TestReportBuilderMarkdown:
    def test_md_header(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [_make_listing()]
        content = builder.build_markdown(listings)
        assert "# Comparative Market Analysis Report" in content
        assert "90210" in content

    def test_md_listing_table(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [_make_listing(address="100 Main St", price=600000, price_per_sqft=400.0)]
        content = builder.build_markdown(listings)
        assert "100 Main St" in content
        assert "| 1 |" in content  # rank 1

    def test_md_deals_section(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        listings = [_make_listing(price_per_sqft=400.0)]
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals(listings, trend)
        builder = ReportBuilder(trend=trend, deals=deals)
        content = builder.build_markdown(listings)
        assert "## Deal Alerts" in content
        assert "400.00" in content

    def test_md_sorted_by_price_per_sqft(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [
            _make_listing(address="A", price_per_sqft=600.0),
            _make_listing(address="B", price_per_sqft=300.0),
            _make_listing(address="C", price_per_sqft=500.0),
        ]
        content = builder.build_markdown(listings)
        # B should be rank 1 (lowest price/sqft)
        assert "| 1 | B |" in content
        assert "| 2 | C |" in content
        assert "| 3 | A |" in content


# ------ ReportBuilder JSON tests ------

class TestReportBuilderJSON:
    def test_json_structure(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listings = [_make_listing()]
        content = builder.build_json(listings)
        import json
        data = json.loads(content)
        assert "summary" in data
        assert "listings" in data
        assert data["summary"]["zip"] == "90210"
        assert len(data["listings"]) == 1

    def test_json_listing_fields(self):
        trend = _make_trend()
        builder = ReportBuilder(trend=trend)
        listing = _make_listing(price=600000, sqft=1500, bedrooms=3, bathrooms=2)
        listings = [listing]
        content = builder.build_json(listings)
        import json
        data = json.loads(content)
        l = data["listings"][0]
        assert l["price"] == 600000
        assert l["sqft"] == 1500
        assert l["beds"] == 3
        assert l["baths"] == 2


# ------ Integration: AlertEngine + ReportBuilder ------

class TestIntegration:
    def test_alerts_feed_into_report(self):
        trend = _make_trend(median_price_per_sqft=500.0)
        listings = [
            _make_listing(price_per_sqft=400.0),
            _make_listing(price_per_sqft=600.0),
        ]
        engine = AlertEngine(threshold=5.0)
        deals = engine.find_deals(listings, trend)
        builder = ReportBuilder(trend=trend, deals=deals)

        # CSV should have deal info
        csv_content = builder.build_csv(listings)
        assert "Deal" in csv_content or "deal" in csv_content.lower()

        # Markdown should have deal section
        md_content = builder.build_markdown(listings)
        assert "## Deal Alerts" in md_content

        # PDF should have deal info
        pdf_content = builder.build_pdf(listings)
        assert b"Deal" in pdf_content
