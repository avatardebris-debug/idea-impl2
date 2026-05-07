"""Entity — represents a financial entity (company, stock, market)."""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Entity:
    """A node in the state-space representing a financial entity."""
    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    
    # Core features
    price: float = 0.0
    volume: float = 0.0
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    eps: float = 0.0
    revenue: float = 0.0
    net_income: float = 0.0
    debt_to_equity: float = 0.0
    roe: float = 0.0
    beta: float = 1.0
    
    # Derived features
    momentum_5d: float = 0.0
    momentum_20d: float = 0.0
    volatility_20d: float = 0.0
    rsi: float = 50.0
    
    # Metadata
    last_updated: float = field(default_factory=time.time)
    filing_count: int = 0
    neighbors: List[str] = field(default_factory=list)
    
    def to_feature_vector(self) -> List[float]:
        """Convert entity features to a numeric vector for ML."""
        return [
            self.price, self.volume, self.market_cap, self.pe_ratio,
            self.eps, self.revenue, self.net_income, self.debt_to_equity,
            self.roe, self.beta, self.momentum_5d, self.momentum_20d,
            self.volatility_20d, self.rsi,
        ]
    
    def feature_names(self) -> List[str]:
        """Return names of features."""
        return [
            "price", "volume", "market_cap", "pe_ratio", "eps",
            "revenue", "net_income", "debt_to_equity", "roe", "beta",
            "momentum_5d", "momentum_20d", "volatility_20d", "rsi",
        ]
    
    def update_from_filing(self, metrics: Dict[str, Any]) -> None:
        """Update entity features from a filing's financial metrics."""
        self.revenue = metrics.get("revenue", self.revenue)
        self.net_income = metrics.get("net_income", self.net_income)
        self.eps = metrics.get("eps", self.eps)
        self.market_cap = metrics.get("market_cap", self.market_cap)
        self.debt_to_equity = metrics.get("debt_to_equity", self.debt_to_equity)
        self.roe = metrics.get("roe", self.roe)
        self.filing_count += 1
        self.last_updated = time.time()
    
    def update_from_price(self, price: float, volume: float) -> None:
        """Update entity from price data."""
        self.price = price
        self.volume = volume
        self.last_updated = time.time()
    
    def similarity_to(self, other: 'Entity') -> float:
        """Compute cosine similarity between two entities' feature vectors."""
        v1 = self.to_feature_vector()
        v2 = other.to_feature_vector()
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
