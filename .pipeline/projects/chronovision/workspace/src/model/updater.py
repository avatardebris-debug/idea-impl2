"""Updater — updates the state space with new data."""

import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

import numpy as np

from chronovision.src.data.loader import DataLoader
from chronovision.src.data.sec_importer import SECImporter
from chronovision.src.model.entity import Entity
from chronovision.src.model.state_space import StateSpace

logger = logging.getLogger(__name__)


class Updater:
    """Updates the state space with new data."""
    
    def __init__(self, data_loader: DataLoader, sec_importer: SECImporter):
        self.data_loader = data_loader
        self.sec_importer = sec_importer
    
    def update_with_new_prices(self, state_space: StateSpace, tickers: List[str] = None) -> StateSpace:
        """Update entity prices from latest stock data."""
        if tickers is None:
            tickers = list(state_space.entities.keys())
        
        for ticker in tickers:
            entity = state_space.get_entity(ticker)
            if not entity:
                continue
            
            prices = self.data_loader.get_stock_prices(ticker, limit=60)
            if prices.empty:
                continue
            
            closes = prices["close"].values
            volumes = prices["volume"].values
            
            entity.price = closes[-1]
            entity.volume = volumes[-1]
            
            # Update technical indicators
            if len(closes) >= 20:
                entity.momentum_5d = (closes[-1] - closes[-6]) / closes[-6] if closes[-6] != 0 else 0
                entity.momentum_20d = (closes[-1] - closes[-21]) / closes[-21] if closes[-21] != 0 else 0
                returns = np.diff(closes) / closes[:-1]
                entity.volatility_20d = np.std(returns[-20:]) if len(returns) >= 20 else 0
                gains = np.maximum(returns[-14:], 0)
                losses = np.abs(np.minimum(returns[-14:], 0))
                avg_gain = np.mean(gains) if len(gains) > 0 else 0
                avg_loss = np.mean(losses) if len(losses) > 0 else 0
                rs = avg_gain / avg_loss if avg_loss != 0 else 100
                entity.rsi = 100 - (100 / (1 + rs))
            
            state_space.add_entity(entity)
        
        state_space.compute_transition_matrix()
        state_space.time_step += 1
        logger.info(f"Updated state space at time step {state_space.time_step}")
        return state_space
    
    def update_with_new_filings(self, state_space: StateSpace, tickers: List[str] = None) -> StateSpace:
        """Update entity financials from new filings."""
        if tickers is None:
            tickers = list(state_space.entities.keys())
        
        for ticker in tickers:
            entity = state_space.get_entity(ticker)
            if not entity:
                continue
            
            filings = self.data_loader.get_filings(ticker=ticker, limit=1)
            if filings.empty:
                continue
            
            latest_filing = filings.iloc[0]
            metrics = latest_filing.get("financial_metrics", {})
            if not metrics:
                continue
            
            entity.update_from_filing(metrics)
            state_space.add_entity(entity)
        
        state_space.compute_transition_matrix()
        state_space.time_step += 1
        logger.info(f"Updated state space with new filings at time step {state_space.time_step}")
        return state_space
    
    def update_with_synthetic_data(self, state_space: StateSpace, num_new_filings: int = 100) -> StateSpace:
        """Update with synthetic data for testing."""
        # Generate new synthetic filings
        self.sec_importer.generate_synthetic_filings(num_new_filings)
        
        # Update state space
        tickers = self.data_loader.get_all_tickers()
        self.update_with_new_prices(state_space, tickers)
        self.update_with_new_filings(state_space, tickers)
        
        logger.info(f"Updated state space with {num_new_filings} new synthetic filings")
        return state_space
    
    def propagate_and_predict(self, state_space: StateSpace, steps: int = 1) -> Dict[str, float]:
        """Propagate states and return predictions."""
        propagation = state_space.propagate_state(steps)
        return propagation
