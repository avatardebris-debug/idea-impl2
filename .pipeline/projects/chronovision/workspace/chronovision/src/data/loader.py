"""Data Loader — provides a clean API for downstream components to query financial data."""

import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from chronovision.src.data.schema import Filing, Company, StockPrice, get_session

logger = logging.getLogger(__name__)


class DataLoader:
    """Provides queryable access to financial data."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url

    def _get_session(self) -> Session:
        return get_session(self.db_url)

    def get_companies(self) -> pd.DataFrame:
        """Get all tracked companies as a DataFrame."""
        session = self._get_session()
        companies = session.query(Company).all()
        session.close()
        data = [{
            "id": c.id, "ticker": c.ticker, "company_name": c.company_name,
            "cik": c.cik, "sector": c.sector, "industry": c.industry,
            "market_cap": c.market_cap, "exchange": c.exchange,
        } for c in companies]
        return pd.DataFrame(data)

    def get_company(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get a single company by ticker."""
        session = self._get_session()
        company = session.query(Company).filter_by(ticker=ticker).first()
        session.close()
        if not company:
            return None
        return {
            "id": company.id, "ticker": company.ticker, "company_name": company.company_name,
            "cik": company.cik, "sector": company.sector, "industry": company.industry,
            "market_cap": company.market_cap, "exchange": company.exchange,
        }

    def get_filings(self, ticker: Optional[str] = None, filing_type: Optional[str] = None,
                    start_date: Optional[date] = None, end_date: Optional[date] = None,
                    limit: int = 1000) -> pd.DataFrame:
        """Get filings with optional filters."""
        session = self._get_session()
        query = session.query(Filing)
        if ticker:
            query = query.filter_by(ticker=ticker)
        if filing_type:
            query = query.filter_by(filing_type=filing_type)
        if start_date:
            query = query.filter(Filing.filing_date >= start_date)
        if end_date:
            query = query.filter(Filing.filing_date <= end_date)
        query = query.order_by(Filing.filing_date.desc()).limit(limit)
        filings = query.all()
        session.close()
        data = [{
            "id": f.id, "ticker": f.ticker, "filing_type": f.filing_type,
            "filing_date": f.filing_date.isoformat() if f.filing_date else None,
            "period_end": f.period_end.isoformat() if f.period_end else None,
            "company_name": f.company_name, "cik": f.cik,
            "financial_metrics": f.financial_metrics,
            "url": f.url,
        } for f in filings]
        return pd.DataFrame(data)

    def get_stock_prices(self, ticker: str, start_date: Optional[date] = None,
                         end_date: Optional[date] = None, limit: int = 365) -> pd.DataFrame:
        """Get stock prices for a ticker."""
        session = self._get_session()
        query = session.query(StockPrice).filter_by(ticker=ticker)
        if start_date:
            query = query.filter(StockPrice.date >= start_date)
        if end_date:
            query = query.filter(StockPrice.date <= end_date)
        query = query.order_by(StockPrice.date).limit(limit)
        prices = query.all()
        session.close()
        data = [{
            "id": p.id, "ticker": p.ticker, "date": p.date.isoformat() if p.date else None,
            "open_price": p.open_price, "high": p.high, "low": p.low,
            "close": p.close, "volume": p.volume, "adjusted_close": p.adjusted_close,
        } for p in prices]
        return pd.DataFrame(data)

    def get_price_series(self, ticker: str, days: int = 365) -> np.ndarray:
        """Get a numpy array of closing prices for a ticker."""
        df = self.get_stock_prices(ticker, limit=days)
        if df.empty:
            return np.array([])
        return df["close"].values.astype(np.float64)

    def get_price_direction(self, ticker: str, days: int = 365) -> np.ndarray:
        """Get price direction (1=up, 0=down) for a ticker."""
        prices = self.get_price_series(ticker, days)
        if len(prices) < 2:
            return np.array([])
        diffs = np.diff(prices)
        return (diffs > 0).astype(int)

    def get_latest_financial_metrics(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get the latest financial metrics for a company."""
        session = self._get_session()
        filing = session.query(Filing).filter_by(ticker=ticker).order_by(Filing.filing_date.desc()).first()
        session.close()
        if not filing or not filing.financial_metrics:
            return None
        return filing.financial_metrics

    def get_all_tickers(self) -> List[str]:
        """Get all available tickers."""
        session = self._get_session()
        tickers = session.query(Company.ticker).distinct().all()
        session.close()
        return [t[0] for t in tickers]

    def get_prediction_dataset(self, ticker: str, lookback: int = 60, horizon: int = 1) -> Dict[str, Any]:
        """Build a prediction dataset for a ticker.
        
        Returns dict with features (X) and target (y) arrays.
        """
        prices = self.get_price_series(ticker, lookback + horizon)
        if len(prices) < lookback + horizon:
            return {"X": np.array([]), "y": np.array([])}

        # Features: returns, volume changes, moving averages
        returns = np.diff(prices[-(lookback + 1):]) / prices[-(lookback + 1):-1]
        df = self.get_stock_prices(ticker, limit=lookback + horizon)
        volumes = df["volume"].values if not df.empty else np.zeros(lookback + horizon)
        vol_changes = np.diff(volumes) / (volumes[:-1] + 1)

        # Moving averages
        ma_5 = np.convolve(prices, np.ones(5)/5, mode='valid')
        ma_20 = np.convolve(prices, np.ones(20)/20, mode='valid')

        # Build feature matrix
        n = len(returns)
        X = np.column_stack([
            returns,
            vol_changes[:n],
            ma_5[:n] - prices[-(n+1):-1],
            ma_20[:n] - prices[-(n+1):-1],
        ])

        # Target: price direction
        y = (np.diff(prices[-(horizon+1):]) > 0).astype(float)

        return {"X": X, "y": y, "ticker": ticker, "dates": prices[-(n+1):]}
