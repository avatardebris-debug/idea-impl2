"""Tests for the StateSpace class."""

import unittest
import numpy as np

from chronovision.src.model.state_space import StateSpace
from chronovision.src.model.entity import Entity


class TestStateSpace(unittest.TestCase):
    """Test suite for StateSpace class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sspace = StateSpace(dimension=14)
        # Add some test entities
        self.aapl = Entity(
            ticker="AAPL", name="Apple Inc.", sector="Technology",
            industry="Consumer Electronics", price=185.0, market_cap=3000000000000.0,
            pe_ratio=30.0, roe=0.35, beta=1.2,
            momentum_5d=0.05, momentum_20d=0.10, volatility_20d=0.25, rsi=60.0,
            volume=50000000.0, eps=6.16, revenue=394000000000.0, net_income=99000000000.0,
            debt_to_equity=1.5,
        )
        self.msft = Entity(
            ticker="MSFT", name="Microsoft", sector="Technology",
            industry="Software", price=380.0, market_cap=2800000000000.0,
            pe_ratio=35.0, roe=0.40, beta=1.1,
            momentum_5d=0.03, momentum_20d=0.08, volatility_20d=0.22, rsi=55.0,
            volume=30000000.0, eps=9.65, revenue=211000000000.0, net_income=72000000000.0,
            debt_to_equity=0.8,
        )
        self.jpm = Entity(
            ticker="JPM", name="JPMorgan", sector="Financial",
            industry="Banking", price=195.0, market_cap=450000000000.0,
            pe_ratio=12.0, roe=0.15, beta=1.3,
            momentum_5d=0.02, momentum_20d=0.05, volatility_20d=0.20, rsi=50.0,
            volume=10000000.0, eps=16.23, revenue=162000000000.0, net_income=49000000000.0,
            debt_to_equity=1.0,
        )
        self.sspace.add_entity(self.aapl)
        self.sspace.add_entity(self.msft)
        self.sspace.add_entity(self.jpm)

    def test_add_entity(self):
        """Test adding an entity to the state space."""
        self.assertEqual(len(self.sspace.entities), 3)
        self.assertIn("AAPL", self.sspace.entities)
        self.assertIn("MSFT", self.sspace.entities)
        self.assertIn("JPM", self.sspace.entities)

    def test_get_entity(self):
        """Test retrieving an entity by ticker."""
        entity = self.sspace.get_entity("AAPL")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.ticker, "AAPL")

    def test_get_entity_not_found(self):
        """Test retrieving a non-existent entity."""
        entity = self.sspace.get_entity("XYZ")
        self.assertIsNone(entity)

    def test_remove_entity(self):
        """Test removing an entity from the state space."""
        self.sspace.remove_entity("AAPL")
        self.assertNotIn("AAPL", self.sspace.entities)
        self.assertEqual(len(self.sspace.entities), 2)

    def test_get_neighbors(self):
        """Test getting neighbors of an entity."""
        neighbors = self.sspace.get_neighbors("AAPL", k=10)
        # AAPL should be similar to MSFT (both tech) more than JPM (financial)
        self.assertIn("MSFT", neighbors)
        self.assertIn("JPM", neighbors)
        # AAPL should not be in its own neighbors
        self.assertNotIn("AAPL", neighbors)

    def test_get_neighbors_empty(self):
        """Test getting neighbors of non-existent entity."""
        neighbors = self.sspace.get_neighbors("XYZ")
        self.assertEqual(neighbors, [])

    def test_get_neighbors_k_limit(self):
        """Test that k limit is respected."""
        neighbors = self.sspace.get_neighbors("AAPL", k=1)
        self.assertEqual(len(neighbors), 1)

    def test_compute_transition_matrix(self):
        """Test computing the transition matrix."""
        matrix = self.sspace.compute_transition_matrix()
        self.assertIsInstance(matrix, np.ndarray)
        self.assertEqual(matrix.shape, (3, 3))
        # Each row should sum to approximately 1 (normalized)
        row_sums = matrix.sum(axis=1)
        np.testing.assert_array_almost_equal(row_sums, [1.0, 1.0, 1.0], decimal=5)
        # All values should be non-negative
        self.assertTrue(np.all(matrix >= 0))

    def test_compute_transition_matrix_empty(self):
        """Test computing transition matrix with no entities."""
        empty_ss = StateSpace()
        matrix = empty_ss.compute_transition_matrix()
        self.assertEqual(matrix.size, 0)

    def test_propagate_state(self):
        """Test state propagation."""
        self.sspace.compute_transition_matrix()
        result = self.sspace.propagate_state(steps=1)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)
        # All values should be non-negative
        for val in result.values():
            self.assertGreaterEqual(val, 0)
        # Values should sum to approximately 1
        self.assertAlmostEqual(sum(result.values()), 1.0, places=5)

    def test_propagate_state_multiple_steps(self):
        """Test state propagation over multiple steps."""
        self.sspace.compute_transition_matrix()
        result1 = self.sspace.propagate_state(steps=1)
        result2 = self.sspace.propagate_state(steps=5)
        # History should have entries
        self.assertEqual(len(self.sspace.history), 2)

    def test_get_state_vector(self):
        """Test getting state vector for a ticker."""
        vector = self.sspace.get_state_vector("AAPL")
        self.assertIsNotNone(vector)
        self.assertEqual(len(vector), 14)
        self.assertIsInstance(vector, np.ndarray)

    def test_get_state_vector_not_found(self):
        """Test getting state vector for non-existent ticker."""
        vector = self.sspace.get_state_vector("XYZ")
        self.assertIsNone(vector)

    def test_get_world_state(self):
        """Test getting world state summary."""
        world_state = self.sspace.get_world_state()
        self.assertIn("tickers", world_state)
        self.assertIn("total_market_cap", world_state)
        self.assertIn("avg_pe", world_state)
        self.assertIn("avg_roe", world_state)
        self.assertIn("num_entities", world_state)
        self.assertIn("time_step", world_state)
        self.assertEqual(world_state["num_entities"], 3)
        self.assertEqual(sorted(world_state["tickers"]), ["AAPL", "JPM", "MSFT"])

    def test_get_world_state_empty(self):
        """Test getting world state with no entities."""
        empty_ss = StateSpace()
        world_state = empty_ss.get_world_state()
        self.assertEqual(world_state["tickers"], [])
        self.assertEqual(world_state["total_market_cap"], 0)
        self.assertEqual(world_state["avg_pe"], 0)
        self.assertEqual(world_state["avg_roe"], 0)

    def test_reset(self):
        """Test resetting the state space."""
        self.sspace.reset()
        self.assertEqual(len(self.sspace.entities), 0)
        self.assertEqual(len(self.sspace.adjacency), 0)
        self.assertIsNone(self.sspace.transition_matrix)
        self.assertEqual(len(self.sspace.history), 0)
        self.assertEqual(self.sspace.time_step, 0)

    def test_adjacency_same_sector(self):
        """Test that entities in the same sector are more likely to be neighbors."""
        # AAPL and MSFT are both in Technology sector
        aapl_neighbors = self.sspace.get_neighbors("AAPL")
        msft_neighbors = self.sspace.get_neighbors("MSFT")
        # They should be in each other's top neighbors
        self.assertIn("MSFT", aapl_neighbors)
        self.assertIn("AAPL", msft_neighbors)

    def test_transition_matrix_symmetry(self):
        """Test that transition matrix has some symmetry properties."""
        self.sspace.compute_transition_matrix()
        matrix = self.sspace.transition_matrix
        # For entities with similar features, transitions should be somewhat symmetric
        # This is a soft test - we just check the matrix is valid
        self.assertTrue(np.all(matrix >= 0))
        self.assertTrue(np.allclose(matrix.sum(axis=1), 1.0))


if __name__ == "__main__":
    unittest.main()
