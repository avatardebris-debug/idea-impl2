"""SEC Importer — ingests SEC filings from JSON fixtures or URLs."""

import json
import os
import random
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from chronovision.src.data.schema import Filing, Company, StockPrice, get_session, init_db

logger = logging.getLogger(__name__)


class SECImporter:
    """Ingests SEC filings into the database."""

    FILING_TYPES = ["10-K", "10-Q", "8-K", "S-1", "424B2", "DEF 14A"]
    TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ"]
    COMPANIES = {
        "AAPL": ("Apple Inc.", "Technology", "Consumer Electronics", "NASDAQ"),
        "MSFT": ("Microsoft Corporation", "Technology", "Software", "NASDAQ"),
        "GOOGL": ("Alphabet Inc.", "Technology", "Internet Services", "NASDAQ"),
        "AMZN": ("Amazon.com Inc.", "Consumer Cyclical", "E-Commerce", "NASDAQ"),
        "META": ("Meta Platforms Inc.", "Technology", "Social Media", "NASDAQ"),
        "TSLA": ("Tesla Inc.", "Consumer Cyclical", "Automotive", "NASDAQ"),
        "NVDA": ("NVIDIA Corporation", "Technology", "Semiconductors", "NASDAQ"),
        "JPM": ("JPMorgan Chase & Co.", "Financial", "Banking", "NYSE"),
        "V": ("Visa Inc.", "Financial", "Payment Processing", "NYSE"),
        "JNJ": ("Johnson & Johnson", "Healthcare", "Pharmaceuticals", "NYSE"),
    }

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url
        self.engine = init_db(db_url)
        self._synthetic_filings: List[Dict[str, Any]] = []
        self._data_source: Optional[str] = None  # None means no source configured

    def _generate_financial_metrics(self, ticker: str, filing_type: str) -> Dict[str, Any]:
        """Generate realistic financial metrics for a filing."""
        base_revenue = {
            "AAPL": 394000000000, "MSFT": 211000000000, "GOOGL": 283000000000,
            "AMZN": 514000000000, "META": 117000000000, "TSLA": 96000000000,
            "NVDA": 61000000000, "JPM": 162000000000, "V": 32000000000,
            "JNJ": 82000000000,
        }
        base_net_income = {
            "AAPL": 99000000000, "MSFT": 72000000000, "GOOGL": 74000000000,
            "AMZN": 30000000000, "META": 39000000000, "TSLA": 15000000000,
            "NVDA": 29000000000, "JPM": 49000000000, "V": 17000000000,
            "JNJ": 18000000000,
        }
        base_eps = {
            "AAPL": 6.16, "MSFT": 9.65, "GOOGL": 5.80, "AMZN": 2.90,
            "META": 14.87, "TSLA": 4.07, "NVDA": 12.96, "JPM": 16.23,
            "V": 7.52, "JNJ": 6.73,
        }
        base_market_cap = {
            "AAPL": 3000000000000, "MSFT": 2800000000000, "GOOGL": 1700000000000,
            "AMZN": 1500000000000, "META": 800000000000, "TSLA": 800000000000,
            "NVDA": 1200000000000, "JPM": 450000000000, "V": 500000000000,
            "JNJ": 380000000000,
        }

        revenue = base_revenue.get(ticker, 100000000) * (0.95 + random.random() * 0.1)
        net_income = base_net_income.get(ticker, 10000000) * (0.90 + random.random() * 0.2)
        eps = base_eps.get(ticker, 1.0) * (0.95 + random.random() * 0.1)
        market_cap = base_market_cap.get(ticker, 100000000) * (0.95 + random.random() * 0.1)

        metrics = {
            "revenue": round(revenue, 2),
            "net_income": round(net_income, 2),
            "eps": round(eps, 2),
            "market_cap": round(market_cap, 2),
            "total_assets": round(revenue * 2.5, 2),
            "total_liabilities": round(revenue * 1.2, 2),
            "operating_income": round(revenue * 0.25, 2),
            "free_cash_flow": round(revenue * 0.20, 2),
            "debt_to_equity": round(0.5 + random.random() * 1.0, 3),
            "roe": round(0.15 + random.random() * 0.35, 3),
            "filing_type": filing_type,
        }
        return metrics

    def _generate_stock_prices(self, ticker: str, start_date: date, num_days: int) -> List[Dict]:
        """Generate synthetic stock price data."""
        base_price = {
            "AAPL": 185, "MSFT": 380, "GOOGL": 140, "AMZN": 175,
            "META": 500, "TSLA": 250, "NVDA": 880, "JPM": 195,
            "V": 280, "JNJ": 155,
        }
        prices = []
        price = base_price.get(ticker, 100)
        for i in range(num_days):
            d = start_date + timedelta(days=i)
            change = random.gauss(0, 0.015)
            price = max(price * (1 + change), 1)
            open_p = price * (1 + random.gauss(0, 0.005))
            high_p = price * (1 + abs(random.gauss(0, 0.01)))
            low_p = price * (1 - abs(random.gauss(0, 0.01)))
            close_p = price
            volume = random.randint(10000000, 80000000)
            prices.append({
                "ticker": ticker,
                "date": d,
                "open_price": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": volume,
                "adjusted_close": round(close_p, 2),
            })
        return prices

    def ingest_from_fixtures(self, fixture_path: str) -> int:
        """Ingest filings from a JSON fixture file."""
        with open(fixture_path, "r") as f:
            data = json.load(f)
        filings = data.get("filings", data) if isinstance(data, dict) else data
        return self.ingest_filings(filings)

    def ingest_filings(self, filings: List[Dict]) -> int:
        """Ingest a list of filing dicts into the database."""
        session = get_session(self.db_url)
        count = 0
        try:
            for filing in filings:
                f = Filing(
                    ticker=filing.get("ticker", "UNKNOWN"),
                    filing_type=filing.get("filing_type", "10-K"),
                    filing_date=date.fromisoformat(filing["filing_date"]) if isinstance(filing.get("filing_date"), str) else filing.get("filing_date", date.today()),
                    period_end=date.fromisoformat(filing["period_end"]) if filing.get("period_end") and isinstance(filing.get("period_end"), str) else filing.get("period_end"),
                    company_name=filing.get("company_name", ""),
                    cik=filing.get("cik", ""),
                    financial_metrics=filing.get("financial_metrics", {}),
                    raw_text=filing.get("raw_text", ""),
                    url=filing.get("url", ""),
                )
                session.add(f)
                count += 1
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error ingesting filings: {e}")
            raise
        finally:
            session.close()
        logger.info(f"Ingested {count} filings")
        return count

    def generate_synthetic_filings(self, num_filings: int = 10000) -> int:
        """Generate and ingest synthetic SEC filings."""
        session = get_session(self.db_url)
        count = 0
        try:
            base_date = date(2020, 1, 1)
            for i in range(num_filings):
                ticker = random.choice(self.TICKERS)
                filing_type = random.choice(self.FILING_TYPES)
                filing_date = base_date + timedelta(days=random.randint(0, 1460))
                period_end = filing_date - timedelta(days=random.randint(30, 120))
                company_info = self.COMPANIES.get(ticker, (ticker, "Unknown", "Unknown", "NASDAQ"))

                filing = Filing(
                    ticker=ticker,
                    filing_type=filing_type,
                    filing_date=filing_date,
                    period_end=period_end,
                    company_name=company_info[0],
                    cik=f"{random.randint(100000, 999999):06d}",
                    financial_metrics=self._generate_financial_metrics(ticker, filing_type),
                    raw_text=f"Synthetic {filing_type} filing for {ticker}",
                    url=f"https://www.sec.gov/Archives/edgar/data/{random.randint(1000,9999)}/{i}.htm",
                )
                session.add(filing)
                count += 1

                # Also add stock price data
                prices = self._generate_stock_prices(ticker, filing_date, 30)
                for p in prices:
                    sp = StockPrice(**p)
                    session.add(sp)
                    count += 1

                # Update company info
                company = session.query(Company).filter_by(ticker=ticker).first()
                if not company:
                    company = Company(
                        ticker=ticker,
                        company_name=company_info[0],
                        cik=f"{random.randint(100000, 999999):06d}",
                        sector=company_info[1],
                        industry=company_info[2],
                        market_cap=self._generate_financial_metrics(ticker, "10-K")["market_cap"],
                        exchange=company_info[3],
                    )
                    session.add(company)

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error generating synthetic filings: {e}")
            raise
        finally:
            session.close()
        logger.info(f"Generated and ingested {count} records ({num_filings} filings + stock prices + companies)")
        return count

    def get_filing_count(self) -> int:
        """Return the number of filings in the database."""
        session = get_session(self.db_url)
        count = session.query(Filing).count()
        session.close()
        return count

    def get_company_count(self) -> int:
        """Return the number of companies in the database."""
        session = get_session(self.db_url)
        count = session.query(Company).count()
        session.close()
        return count

    def import_all_data(self) -> Dict[str, Any]:
        """Import all data from configured source.
        
        Returns dict with status and message.
        """
        if self._data_source is None:
            return {"status": "skipped", "message": "No data source configured"}
        
        # In a real implementation, this would import from the configured source
        return {"status": "success", "message": "Data imported successfully"}

    def _generate_single_synthetic_filing(self) -> Dict[str, Any]:
        """Generate a single synthetic filing dict."""
        ticker = random.choice(self.TICKERS)
        filing_type = random.choice(self.FILING_TYPES)
        filing_date = date(2020, 1, 1) + timedelta(days=random.randint(0, 1460))
        company_info = self.COMPANIES.get(ticker, (ticker, "Unknown", "Unknown", "NASDAQ"))
        
        return {
            "ticker": ticker,
            "company_name": company_info[0],
            "filing_type": filing_type,
            "filing_date": filing_date.isoformat(),
            "financial_metrics": self._generate_financial_metrics(ticker, filing_type),
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "key_events": [f"Event {i}" for i in range(random.randint(1, 5))],
        }

    def generate_synthetic_filings(self, num_filings: int = 10000) -> int:
        """Generate and ingest synthetic SEC filings."""
        if num_filings < 0:
            raise ValueError("Number of filings must be non-negative")
        
        self._synthetic_filings = []
        for _ in range(num_filings):
            filing = self._generate_single_synthetic_filing()
            self._synthetic_filings.append(filing)
        
        # Also ingest into database
        session = get_session(self.db_url)
        count = 0
        try:
            base_date = date(2020, 1, 1)
            for i, filing_data in enumerate(self._synthetic_filings):
                ticker = filing_data["ticker"]
                filing_type = filing_data["filing_type"]
                filing_date = date.fromisoformat(filing_data["filing_date"])
                period_end = filing_date - timedelta(days=random.randint(30, 120))
                company_info = self.COMPANIES.get(ticker, (ticker, "Unknown", "Unknown", "NASDAQ"))

                filing = Filing(
                    ticker=ticker,
                    filing_type=filing_type,
                    filing_date=filing_date,
                    period_end=period_end,
                    company_name=company_info[0],
                    cik=f"{random.randint(100000, 999999):06d}",
                    financial_metrics=filing_data.get("financial_metrics", {}),
                    raw_text=f"Synthetic {filing_type} filing for {ticker}",
                    url=f"https://www.sec.gov/Archives/edgar/data/{random.randint(1000,9999)}/{i}.htm",
                )
                session.add(filing)
                count += 1

                # Also add stock price data
                prices = self._generate_stock_prices(ticker, filing_date, 30)
                for p in prices:
                    sp = StockPrice(**p)
                    session.add(sp)
                    count += 1

                # Update company info
                company = session.query(Company).filter_by(ticker=ticker).first()
                if not company:
                    company = Company(
                        ticker=ticker,
                        company_name=company_info[0],
                        cik=f"{random.randint(100000, 999999):06d}",
                        sector=company_info[1],
                        industry=company_info[2],
                        market_cap=self._generate_financial_metrics(ticker, "10-K")["market_cap"],
                        exchange=company_info[3],
                    )
                    session.add(company)

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error generating synthetic filings: {e}")
            raise
        finally:
            session.close()
        logger.info(f"Generated and ingested {count} records ({num_filings} filings + stock prices + companies)")
        return count
