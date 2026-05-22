"""Tests for the model layer."""

import pytest
import numpy as np
from unittest.mock import MagicMock

from chronovision.src.model.entity import Entity
from chronovision.src.model.state_space import StateSpace
from chronovision.src.model.graph_builder import GraphBuilder
from chronovision.src.model.updater import Updater


class TestEntity:
    """Tests for Entity."""
    
    def test_init(self):
        """Test entity initialization."""
        entity = Entity(ticker="AAPL", name="Apple Inc.")
        assert entity.ticker == "AAPL"
        assert entity.name == "Apple Inc."
        assert entity.price == 0.0
        assert entity.filing_count == 0
    
    def test_to_feature_vector(self):
        """Test feature vector conversion."""
        entity = Entity(ticker="AAPL", price=100.0, volume=1000000.0)
        vector = entity.to_feature_vector()
        assert len(vector) == 14
        assert vector[0] == 100.0  # price
        assert vector[1] == 1000000.0  # volume
    
    def test_feature_names(self):
        """Test feature names."""
        entity = Entity(ticker="AAPL")
        names = entity.feature_names()
        assert len(names) == 14
        assert "price" in names
        assert "volume" in names
        assert "market_cap" in names
    
    def test_update_from_filing(self):
        """Test updating entity from filing."""
        entity = Entity(ticker="AAPL")
        metrics = {"revenue": 1000000, "net_income": 200000, "eps": 5.0}
        entity.update_from_filing(metrics)
        
        assert entity.revenue == 1000000
        assert entity.net_income == 200000
        assert entity.eps == 5.0
        assert entity.filing_count == 1
    
    def test_update_from_price(self):
        """Test updating entity from price."""
        entity = Entity(ticker="AAPL", price=100.0)
        entity.update_from_price(105.0, 1500000.0)
        
        assert entity.price == 105.0
        assert entity.volume == 1500000.0
    
    def test_get_metrics(self):
        """Test getting entity metrics."""
        entity = Entity(ticker="AAPL", price=100.0, market_cap=1000000000.0)
        metrics = entity.get_metrics()
        
        assert "price" in metrics
        assert "market_cap" in metrics
        assert metrics["price"] == 100.0


class TestStateSpace:
    """Tests for StateSpace."""
    
    def test_init(self):
        """Test state space initialization."""
        ss = StateSpace()
        assert ss.entities == {}
        assert ss.adjacency == {}
    
    def test_add_entity(self):
        """Test adding entity."""
        ss = StateSpace()
        entity = Entity(ticker="AAPL", name="Apple Inc.")
        ss.add_entity(entity)
        
        assert "AAPL" in ss.entities
        assert ss.entities["AAPL"] == entity
    
    def test_get_entity(self):
        """Test getting entity."""
        ss = StateSpace()
        entity = Entity(ticker="AAPL", name="Apple Inc.")
        ss.add_entity(entity)
        
        retrieved = ss.get_entity("AAPL")
        assert retrieved == entity
    
    def test_get_entity_not_found(self):
        """Test getting non-existent entity."""
        ss = StateSpace()
        entity = ss.get_entity("NONEXISTENT")
        assert entity is None
    
    def test_get_neighbors(self):
        """Test getting neighbors."""
        ss = StateSpace()
        ss.add_entity(Entity(ticker="AAPL", sector="Tech", price=100.0))
        ss.add_entity(Entity(ticker="MSFT", sector="Tech", price=105.0))
        
        neighbors = ss.get_neighbors("AAPL")
        assert "MSFT" in neighbors
    
    def test_get_world_state(self):
        """Test getting world state."""
        ss = StateSpace()
        ss.add_entity(Entity(ticker="AAPL", price=100.0))
        ss.add_entity(Entity(ticker="MSFT", price=200.0))
        
        state = ss.get_world_state()
        assert "tickers" in state
        assert "AAPL" in state["tickers"]
        assert "MSFT" in state["tickers"]
        assert state["num_entities"] == 2
    
    def test_propagate(self):
        """Test state propagation."""
        ss = StateSpace()
        ss.add_entity(Entity(ticker="AAPL", price=100.0, sector="Tech", market_cap=1000))
        ss.add_entity(Entity(ticker="MSFT", price=200.0, sector="Tech", market_cap=2000))
        
        ss.compute_transition_matrix()
        ss.propagate_state(1)
        
        # After propagation, history should have elements
        assert len(ss.history) > 0


class TestGraphBuilder:
    """Tests for GraphBuilder."""
    
    def test_init(self):
        """Test initialization."""
        loader = MagicMock()
        builder = GraphBuilder(loader)
        assert builder.data_loader == loader
    
    def test_build_from_companies_empty(self):
        """Test building graph with no companies."""
        loader = MagicMock()
        loader.get_all_tickers.return_value = []
        loader.get_company.return_value = None
        
        builder = GraphBuilder(loader)
        ss = StateSpace()
        builder.build_from_companies(ss, [])
        
        assert ss.entities == {}


class TestUpdater:
    """Tests for Updater."""
    
    def test_init(self):
        """Test initialization."""
        loader = MagicMock()
        sec_importer = MagicMock()
        updater = Updater(loader, sec_importer)
        assert updater.data_loader == loader
        assert updater.sec_importer == sec_importer
    
    def test_update_with_new_prices_empty(self):
        """Test updating with no prices."""
        loader = MagicMock()
        loader.get_stock_prices.return_value = None
        
        updater = Updater(loader, MagicMock())
        ss = StateSpace()
        updater.update_with_new_prices(ss, [])
        
        assert ss.entities == {}
    
    def test_propagate_and_predict_empty(self):
        """Test propagation with no entities."""
        loader = MagicMock()
        sec_importer = MagicMock()
        
        updater = Updater(loader, sec_importer)
        ss = StateSpace()
        predictions = updater.propagate_and_predict(ss, 1)
        
        assert predictions == {}
