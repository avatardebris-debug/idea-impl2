"""GraphBuilder — constructs the state-space graph from data."""

import logging
from typing import List, Dict, Any

import numpy as np

from chronovision.src.data.loader import DataLoader
from chronovision.src.model.entity import Entity
from chronovision.src.model.state_space import StateSpace

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds the state-space graph from financial data."""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
    
    def build_from_companies(self, state_space: StateSpace, tickers: List[str] = None) -> StateSpace:
        """Build the state space from company data."""
        state_space.reset()
        
        if tickers is None:
            tickers = self.data_loader.get_all_tickers()
        
        for ticker in tickers:
            company = self.data_loader.get_company(ticker)
            if not company:
                continue
            
            metrics = self.data_loader.get_latest_financial_metrics(ticker)
            prices = self.data_loader.get_stock_prices(ticker, limit=60)
            
            entity = Entity(
                ticker=ticker,
                name=company.get("company_name", ticker),
                sector=company.get("sector", ""),
                industry=company.get("industry", ""),
                price=prices["close"].iloc[-1] if not prices.empty else 0.0,
                volume=prices["volume"].iloc[-1] if not prices.empty else 0.0,
                market_cap=company.get("market_cap", 0.0),
                pe_ratio=company.get("market_cap", 0.0) / max(metrics.get("net_income", 1), 1) if metrics else 0.0,
                eps=metrics.get("eps", 0.0) if metrics else 0.0,
                revenue=metrics.get("revenue", 0.0) if metrics else 0.0,
                net_income=metrics.get("net_income", 0.0) if metrics else 0.0,
                debt_to_equity=metrics.get("debt_to_equity", 0.0) if metrics else 0.0,
                roe=metrics.get("roe", 0.0) if metrics else 0.0,
            )
            
            # Compute technical indicators
            if not prices.empty and len(prices) >= 20:
                closes = prices["close"].values
                entity.momentum_5d = (closes[-1] - closes[-6]) / closes[-6] if closes[-6] != 0 else 0
                entity.momentum_20d = (closes[-1] - closes[-21]) / closes[-21] if closes[-21] != 0 else 0
                
                # Volatility
                returns = np.diff(closes) / closes[:-1]
                entity.volatility_20d = np.std(returns[-20:]) if len(returns) >= 20 else 0
                
                # RSI
                gains = np.maximum(returns[-14:], 0)
                losses = np.abs(np.minimum(returns[-14:], 0))
                avg_gain = np.mean(gains) if len(gains) > 0 else 0
                avg_loss = np.mean(losses) if len(losses) > 0 else 0
                rs = avg_gain / avg_loss if avg_loss != 0 else 100
                entity.rsi = 100 - (100 / (1 + rs))
            
            state_space.add_entity(entity)
        
        state_space.compute_transition_matrix()
        logger.info(f"Built state space with {len(state_space.entities)} entities")
        return state_space
    
    def build_from_filings(self, state_space: StateSpace, tickers: List[str] = None) -> StateSpace:
        """Build the state space from filing data."""
        state_space.reset()
        
        if tickers is None:
            tickers = self.data_loader.get_all_tickers()
        
        for ticker in tickers:
            filings = self.data_loader.get_filings(ticker=ticker, limit=1)
            if filings.empty:
                continue
            
            latest_filing = filings.iloc[0]
            metrics = latest_filing.get("financial_metrics", {})
            if not metrics:
                continue
            
            entity = Entity(
                ticker=ticker,
                name=latest_filing.get("company_name", ticker),
                sector="",
                industry="",
                price=0.0,
                volume=0.0,
                market_cap=metrics.get("market_cap", 0.0),
                pe_ratio=metrics.get("market_cap", 0.0) / max(metrics.get("net_income", 1), 1),
                eps=metrics.get("eps", 0.0),
                revenue=metrics.get("revenue", 0.0),
                net_income=metrics.get("net_income", 0.0),
                debt_to_equity=metrics.get("debt_to_equity", 0.0),
                roe=metrics.get("roe", 0.0),
            )
            state_space.add_entity(entity)
        
        state_space.compute_transition_matrix()
        logger.info(f"Built state space from filings with {len(state_space.entities)} entities")
        return state_space
