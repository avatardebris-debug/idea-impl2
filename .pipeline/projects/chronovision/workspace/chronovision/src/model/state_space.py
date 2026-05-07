"""StateSpace — the core state-space representation of the financial world."""

import time
import math
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import numpy as np

from chronovision.src.model.entity import Entity


class StateSpace:
    """Represents the current state of the financial world as a graph of entities."""
    
    def __init__(self, dimension: int = 14):
        self.dimension = dimension
        self.entities: Dict[str, Entity] = {}
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.transition_matrix: Optional[np.ndarray] = None
        self.time_step: int = 0
        self.history: List[Dict[str, float]] = []
    
    def add_entity(self, entity: Entity) -> None:
        """Add or update an entity in the state space."""
        self.entities[entity.ticker] = entity
        self._update_adjacency()
    
    def remove_entity(self, ticker: str) -> None:
        """Remove an entity from the state space."""
        if ticker in self.entities:
            del self.entities[ticker]
            if ticker in self.adjacency:
                del self.adjacency[ticker]
            # Remove from other adjacency lists
            for t in self.adjacency:
                if ticker in self.adjacency[t]:
                    self.adjacency[t].remove(ticker)
    
    def get_entity(self, ticker: str) -> Optional[Entity]:
        """Get an entity by ticker."""
        return self.entities.get(ticker)
    
    def get_neighbors(self, ticker: str, k: int = 10) -> List[str]:
        """Get the k most similar entities to a given ticker."""
        if ticker not in self.entities:
            return []
        entity = self.entities[ticker]
        similarities = []
        for other_ticker, other in self.entities.items():
            if other_ticker != ticker:
                sim = entity.similarity_to(other)
                similarities.append((other_ticker, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in similarities[:k]]
    
    def _update_adjacency(self) -> None:
        """Update the adjacency list based on sector/industry similarity."""
        self.adjacency = defaultdict(list)
        for ticker, entity in self.entities.items():
            neighbors = []
            for other_ticker, other in self.entities.items():
                if other_ticker == ticker:
                    continue
                # Same sector or industry gets higher weight
                sector_match = 1.0 if entity.sector == other.sector else 0.5
                industry_match = 1.0 if entity.industry == other.industry else 0.0
                price_sim = 1.0 / (1.0 + abs(math.log(entity.price / other.price) + 1e-10))
                score = sector_match + industry_match + price_sim * 0.5
                neighbors.append((other_ticker, score))
            neighbors.sort(key=lambda x: x[1], reverse=True)
            self.adjacency[ticker] = [t for t, _ in neighbors[:15]]
    
    def compute_transition_matrix(self) -> np.ndarray:
        """Compute the transition matrix between entities."""
        tickers = sorted(self.entities.keys())
        n = len(tickers)
        if n == 0:
            return np.array([])
        
        ticker_to_idx = {t: i for i, t in enumerate(tickers)}
        matrix = np.zeros((n, n))
        
        for i, ticker in enumerate(tickers):
            neighbors = self.adjacency.get(ticker, [])
            if neighbors:
                for neighbor in neighbors:
                    if neighbor in ticker_to_idx:
                        j = ticker_to_idx[neighbor]
                        # Weight by similarity
                        sim = self.entities[ticker].similarity_to(self.entities[neighbor])
                        matrix[i, j] = sim
        
        # Normalize rows
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        matrix = matrix / row_sums
        
        self.transition_matrix = matrix
        return matrix
    
    def propagate_state(self, steps: int = 1) -> Dict[str, float]:
        """Propagate states through the graph for a given number of steps."""
        if not self.transition_matrix or self.transition_matrix.size == 0:
            return {}
        
        tickers = sorted(self.entities.keys())
        n = len(tickers)
        
        # Initial state vector (normalized market cap)
        market_caps = np.array([self.entities[t].market_cap for t in tickers], dtype=np.float64)
        total_cap = market_caps.sum()
        if total_cap == 0:
            state = np.ones(n) / n
        else:
            state = market_caps / total_cap
        
        # Propagate
        for _ in range(steps):
            state = self.transition_matrix @ state
        
        # Convert back to dict
        result = {t: float(s) for t, s in zip(tickers, state)}
        self.history.append(result)
        return result
    
    def get_state_vector(self, ticker: str) -> Optional[np.ndarray]:
        """Get the state vector for a specific ticker."""
        if ticker not in self.entities:
            return None
        entity = self.entities[ticker]
        return np.array(entity.to_feature_vector())
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get a summary of the current world state."""
        if not self.entities:
            return {"tickers": [], "total_market_cap": 0, "avg_pe": 0, "avg_roe": 0}
        
        total_cap = sum(e.market_cap for e in self.entities.values())
        avg_pe = np.mean([e.pe_ratio for e in self.entities.values() if e.pe_ratio > 0]) if self.entities else 0
        avg_roe = np.mean([e.roe for e in self.entities.values() if e.roe > 0]) if self.entities else 0
        
        return {
            "tickers": list(self.entities.keys()),
            "total_market_cap": total_cap,
            "avg_pe": avg_pe,
            "avg_roe": avg_roe,
            "num_entities": len(self.entities),
            "time_step": self.time_step,
        }
    
    def reset(self) -> None:
        """Reset the state space."""
        self.entities.clear()
        self.adjacency.clear()
        self.transition_matrix = None
        self.history.clear()
        self.time_step = 0
