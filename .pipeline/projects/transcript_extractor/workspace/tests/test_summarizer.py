"""
Comprehensive tests for SummaryGenerator class.
"""

import pytest
from unittest.mock import patch, MagicMock

from transcript_extractor.summarizer import SummaryGenerator


class TestSummaryGeneratorInit:
    """Tests for SummaryGenerator initialization."""
    
    def test_init_default_strategy(self):
        """Test default strategy initialization."""
        generator = SummaryGenerator()
        assert generator.strategy == "extractive"
        assert generator.length == "medium"
    
    def test_init_custom_strategy(self):
        """Test custom strategy initialization."""
        generator = SummaryGenerator(strategy="abstractive")
        assert generator.strategy == "abstractive"
    
    def test_init_custom_length(self):
        """Test custom length initialization."""
        generator = SummaryGenerator(length="short")
        assert generator.length == "short"
    
    def test_init_custom_strategy_and_length(self):
        """Test custom strategy and length initialization."""
        generator = SummaryGenerator(strategy="simple", length="long")
        assert generator.strategy == "simple"
        assert generator.length == "long"
    
    def test_init_invalid_strategy(self):
        """Test invalid strategy raises error."""
        with pytest.raises(ValueError, match="Unknown summarization strategy"):
            SummaryGenerator(strategy="invalid")
    
    def test_init_invalid_length_extractive(self):
        """Test invalid length for extractive raises error."""
        with pytest.raises(ValueError, match="Invalid length"):
            SummaryGenerator(strategy="extractive", length="invalid")
    
    def test_init_invalid_length_abstractive(self):
        """Test invalid length for abstractive raises error."""
        with pytest.raises(ValueError, match="Invalid length"):
            SummaryGenerator(strategy="abstractive", length="invalid")
    
    def test_init_invalid_length_simple(self):
        """Test invalid length for simple raises error."""
        with pytest.raises(ValueError, match="Invalid length"):
            SummaryGenerator(strategy="simple", length="invalid")


class TestGenerate:
    """Tests for generate method."""
    
    def test_generate_extractive(self):
        """Test extractive summarization."""
        generator = SummaryGenerator(strategy="extractive", length="medium")
        text = "This is a test sentence. This is another test sentence. " * 10
        result = generator.generate(text)
        assert "summary" in result
        assert "key_points" in result
        assert result["method"] == "extractive"
        assert len(result["summary"]) > 0
    
    def test_generate_abstractive(self):
        """Test abstractive summarization."""
        generator = SummaryGenerator(strategy="abstractive", length="medium")
        text = "This is a test sentence. This is another test sentence. " * 10
        result = generator.generate(text)
        assert "summary" in result
        assert "key_points" in result
        assert result["method"] == "abstractive"
        assert len(result["summary"]) > 0
    
    def test_generate_simple(self):
        """Test simple summarization."""
        generator = SummaryGenerator(strategy="simple", length="medium")
        text = "This is a test sentence. This is another test sentence. " * 10
        result = generator.generate(text)
        assert "summary" in result
        assert "key_points" in result
        assert result["method"] == "length_based"
        assert len(result["summary"]) > 0
    
    def test_generate_empty_text(self):
        """Test generation with empty text."""
        generator = SummaryGenerator(strategy="extractive")
        result = generator.generate("")
        assert result["summary"] == ""
        assert result["key_points"] == []
    
    def test_generate_short_text(self):
        """Test generation with very short text."""
        generator = SummaryGenerator(strategy="extractive")
        result = generator.generate("Short text")
        assert result["summary"] == "Short text"
    
    def test_generate_with_language(self):
        """Test generation with specific language."""
        generator = SummaryGenerator(strategy="extractive")
        text = "This is a test sentence. " * 10
        result = generator.generate(text, language="en")
        assert "summary" in result
        assert len(result["summary"]) > 0
    
    def test_generate_returns_dict(self):
        """Test that generate returns a dictionary."""
        generator = SummaryGenerator(strategy="extractive")
        text = "This is a test sentence. " * 10
        result = generator.generate(text)
        assert isinstance(result, dict)


class TestGetKeyPoints:
    """Tests for get_key_points method."""
    
    def test_get_key_points_extractive(self):
        """Test key points extraction with extractive strategy."""
        generator = SummaryGenerator(strategy="extractive")
        text = "First point. Second point. Third point. Fourth point. Fifth point. " * 5
        key_points = generator.get_key_points(text)
        assert isinstance(key_points, list)
        assert len(key_points) > 0
        assert all(isinstance(point, str) for point in key_points)
    
    def test_get_key_points_custom_count(self):
        """Test key points extraction with custom count."""
        generator = SummaryGenerator(strategy="extractive")
        text = "Point one. Point two. Point three. Point four. Point five. " * 10
        key_points = generator.get_key_points(text, num_points=3)
        assert len(key_points) <= 3
    
    def test_get_key_points_abstractive(self):
        """Test key points extraction with abstractive strategy."""
        generator = SummaryGenerator(strategy="abstractive")
        text = "First point. Second point. Third point. " * 10
        key_points = generator.get_key_points(text)
        assert isinstance(key_points, list)
        assert len(key_points) > 0
    
    def test_get_key_points_simple(self):
        """Test key points extraction with simple strategy."""
        generator = SummaryGenerator(strategy="simple")
        text = "First point. Second point. Third point. " * 10
        key_points = generator.get_key_points(text)
        assert isinstance(key_points, list)
        assert len(key_points) > 0


class TestUpdateStrategy:
    """Tests for update_strategy method."""
    
    def test_update_strategy_extractive(self):
        """Test updating to extractive strategy."""
        generator = SummaryGenerator(strategy="abstractive")
        generator.update_strategy("extractive")
        assert generator.strategy == "extractive"
    
    def test_update_strategy_abstractive(self):
        """Test updating to abstractive strategy."""
        generator = SummaryGenerator(strategy="extractive")
        generator.update_strategy("abstractive")
        assert generator.strategy == "abstractive"
    
    def test_update_strategy_simple(self):
        """Test updating to simple strategy."""
        generator = SummaryGenerator(strategy="extractive")
        generator.update_strategy("simple")
        assert generator.strategy == "simple"
    
    def test_update_strategy_invalid(self):
        """Test updating to invalid strategy raises error."""
        generator = SummaryGenerator(strategy="extractive")
        with pytest.raises(ValueError, match="Unknown summarization strategy"):
            generator.update_strategy("invalid")


class TestUpdateLength:
    """Tests for update_length method."""
    
    def test_update_length_short(self):
        """Test updating to short length."""
        generator = SummaryGenerator(length="medium")
        generator.update_length("short")
        assert generator.length == "short"
    
    def test_update_length_medium(self):
        """Test updating to medium length."""
        generator = SummaryGenerator(length="short")
        generator.update_length("medium")
        assert generator.length == "medium"
    
    def test_update_length_long(self):
        """Test updating to long length."""
        generator = SummaryGenerator(length="short")
        generator.update_length("long")
        assert generator.length == "long"
    
    def test_update_length_invalid(self):
        """Test updating to invalid length raises error."""
        generator = SummaryGenerator(length="medium")
        with pytest.raises(ValueError, match="Invalid length"):
            generator.update_length("invalid")


class TestSummaryGeneratorIntegration:
    """Integration tests for SummaryGenerator."""
    
    def test_full_workflow(self):
        """Test complete summarization workflow."""
        generator = SummaryGenerator(strategy="extractive", length="medium")
        
        text = """
        The quick brown fox jumps over the lazy dog. This is a test sentence.
        Another important sentence here. Yet another sentence to make the text longer.
        More text to ensure we have enough content for summarization.
        Final sentence to complete the paragraph.
        """
        
        # Generate summary
        summary_result = generator.generate(text)
        assert "summary" in summary_result
        assert "key_points" in summary_result
        assert len(summary_result["summary"]) > 0
        
        # Get key points
        key_points = generator.get_key_points(text)
        assert isinstance(key_points, list)
        assert len(key_points) > 0
        
        # Update strategy and regenerate
        generator.update_strategy("abstractive")
        summary_result = generator.generate(text)
        assert summary_result["method"] == "abstractive"
        
        # Update length and regenerate
        generator.update_length("short")
        summary_result = generator.generate(text)
        assert generator.length == "short"
