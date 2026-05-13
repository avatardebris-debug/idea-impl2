"""Tests for the Entity class."""

import time
import unittest
import numpy as np

from chronovision.src.model.entity import Entity


class TestEntity(unittest.TestCase):
    """Test suite for Entity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.entity = Entity(
            ticker="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            price=185.0,
            volume=50000000.0,
            market_cap=3000000000000.0,
            pe_ratio=30.0,
            eps=6.16,
            revenue=394000000000.0,
            net_income=99000000000.0,
            debt_to_equity=1.5,
            roe=0.35,
            beta=1.2,
            momentum_5d=0.05,
            momentum_20d=0.10,
            volatility_20d=0.25,
            rsi=60.0,
        )

    def test_feature_vector_length(self):
        """Test that feature vector has correct length."""
        features = self.entity.to_feature_vector()
        self.assertEqual(len(features), 14)

    def test_feature_vector_values(self):
        """Test that feature vector contains correct values."""
        features = self.entity.to_feature_vector()
        expected = [
            185.0, 50000000.0, 3000000000000.0, 30.0,
            6.16, 394000000000.0, 99000000000.0, 1.5,
            0.35, 1.2, 0.05, 0.10,
            0.25, 60.0,
        ]
        np.testing.assert_array_almost_equal(features, expected)

    def test_feature_names(self):
        """Test that feature names are correct."""
        names = self.entity.feature_names()
        expected_names = [
            "price", "volume", "market_cap", "pe_ratio",
            "eps", "revenue", "net_income", "debt_to_equity",
            "roe", "beta", "momentum_5d", "momentum_20d",
            "volatility_20d", "rsi",
        ]
        self.assertEqual(names, expected_names)

    def test_update_from_filing(self):
        """Test updating entity from filing metrics."""
        metrics = {
            "revenue": 400000000000.0,
            "net_income": 100000000000.0,
            "eps": 6.50,
            "market_cap": 3100000000000.0,
            "debt_to_equity": 1.6,
            "roe": 0.36,
        }
        initial_filing_count = self.entity.filing_count
        self.entity.update_from_filing(metrics)
        self.assertEqual(self.entity.revenue, 400000000000.0)
        self.assertEqual(self.entity.net_income, 100000000000.0)
        self.assertEqual(self.entity.eps, 6.50)
        self.assertEqual(self.entity.market_cap, 3100000000000.0)
        self.assertEqual(self.entity.debt_to_equity, 1.6)
        self.assertEqual(self.entity.roe, 0.36)
        self.assertEqual(self.entity.filing_count, initial_filing_count + 1)
        self.assertGreater(self.entity.last_updated, time.time() - 1)

    def test_update_from_filing_partial(self):
        """Test updating entity with partial filing metrics."""
        metrics = {"revenue": 400000000000.0}
        self.entity.update_from_filing(metrics)
        self.assertEqual(self.entity.revenue, 400000000000.0)
        # Other fields should remain unchanged
        self.assertEqual(self.entity.net_income, 99000000000.0)
        self.assertEqual(self.entity.eps, 6.16)

    def test_update_from_price(self):
        """Test updating entity from price data."""
        self.entity.update_from_price(190.0, 55000000.0)
        self.assertEqual(self.entity.price, 190.0)
        self.assertEqual(self.entity.volume, 55000000.0)
        self.assertGreater(self.entity.last_updated, time.time() - 1)

    def test_similarity_to_self(self):
        """Test cosine similarity to self is 1.0."""
        sim = self.entity.similarity_to(self.entity)
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_similarity_to_different_entity(self):
        """Test cosine similarity between different entities."""
        other = Entity(
            ticker="MSFT",
            name="Microsoft",
            sector="Technology",
            industry="Software",
            price=380.0,
            volume=30000000.0,
            market_cap=2800000000000.0,
            pe_ratio=35.0,
            eps=9.65,
            revenue=211000000000.0,
            net_income=72000000000.0,
            debt_to_equity=0.8,
            roe=0.40,
            beta=1.1,
            momentum_5d=0.03,
            momentum_20d=0.08,
            volatility_20d=0.22,
            rsi=55.0,
        )
        sim = self.entity.similarity_to(other)
        # Should be positive since both are tech companies with similar profiles
        self.assertGreater(sim, 0.0)
        self.assertLessEqual(sim, 1.0)

    def test_similarity_to_zero_vector(self):
        """Test similarity to entity with all zeros."""
        zero_entity = Entity(ticker="ZERO")
        sim = self.entity.similarity_to(zero_entity)
        self.assertEqual(sim, 0.0)

    def test_similarity_symmetry(self):
        """Test that similarity is symmetric."""
        other = Entity(
            ticker="GOOGL",
            name="Alphabet",
            sector="Technology",
            industry="Internet Services",
            price=140.0,
            volume=25000000.0,
            market_cap=1700000000000.0,
            pe_ratio=25.0,
            eps=5.80,
            revenue=283000000000.0,
            net_income=74000000000.0,
            debt_to_equity=0.3,
            roe=0.25,
            beta=1.3,
            momentum_5d=0.02,
            momentum_20d=0.06,
            volatility_20d=0.30,
            rsi=45.0,
        )
        sim_ab = self.entity.similarity_to(other)
        sim_ba = other.similarity_to(self.entity)
        self.assertAlmostEqual(sim_ab, sim_ba, places=5)

    def test_entity_defaults(self):
        """Test default values for Entity."""
        entity = Entity(ticker="TEST")
        self.assertEqual(entity.name, "")
        self.assertEqual(entity.sector, "")
        self.assertEqual(entity.industry, "")
        self.assertEqual(entity.price, 0.0)
        self.assertEqual(entity.volume, 0.0)
        self.assertEqual(entity.market_cap, 0.0)
        self.assertEqual(entity.pe_ratio, 0.0)
        self.assertEqual(entity.eps, 0.0)
        self.assertEqual(entity.revenue, 0.0)
        self.assertEqual(entity.net_income, 0.0)
        self.assertEqual(entity.debt_to_equity, 0.0)
        self.assertEqual(entity.roe, 0.0)
        self.assertEqual(entity.beta, 1.0)
        self.assertEqual(entity.momentum_5d, 0.0)
        self.assertEqual(entity.momentum_20d, 0.0)
        self.assertEqual(entity.volatility_20d, 0.0)
        self.assertEqual(entity.rsi, 50.0)
        self.assertEqual(entity.filing_count, 0)
        self.assertEqual(entity.neighbors, [])


if __name__ == "__main__":
    unittest.main()
