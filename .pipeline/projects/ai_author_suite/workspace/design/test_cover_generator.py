"""
Tests for Cover Generator module.

This module contains comprehensive tests for the CoverGenerator class,
testing all generation modes including AI-powered, template-based,
and rule-based generation.
"""

import pytest
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from design.models import (
    CoverDesign,
    BookMetadata,
    DesignStyle,
    LayoutType,
    ImageType,
    ColorPalette,
    TypographySpec,
    LayoutSpec,
    ImageSpec,
    AnalysisResult,
    DesignScore,
    DesignFeedback,
)
from design.cover_generator import (
    CoverGenerator,
    GenerationMode,
    create_cover_generator,
    generate_cover,
)


class TestCoverGenerator:
    """Tests for the CoverGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a CoverGenerator instance for testing."""
        return CoverGenerator()
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample book metadata for testing."""
        return BookMetadata(
            title="The Art of Design",
            author="Jane Smith",
            genre="business",
            target_audience="professionals",
            book_length=350,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["design", "business", "creativity"]
        )
    
    @pytest.fixture
    def sample_design(self, sample_metadata):
        """Create a sample cover design for testing."""
        return CoverDesign(
            id="test-001",
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL,
            layout=LayoutSpec(
                layout_type=LayoutType.MODERN,
                title_position="center",
                author_position="bottom",
                image_position="center"
            ),
            typography=TypographySpec(
                title_font="sans-serif",
                title_size=56,
                title_weight="bold",
                author_font="sans-serif",
                author_size=28,
                author_weight="medium"
            ),
            color_palette=ColorPalette(
                primary_color="#2C3E50",
                secondary_color="#34495E",
                accent_color="#3498DB",
                background_color="#ECF0F1"
            ),
            image_spec=ImageSpec(
                image_type=ImageType.GRAPHIC,
                image_url="",
                overlay_opacity=0.1
            )
        )
    
    # ==================== GENERATION MODE TESTS ====================
    
    def test_generation_mode_enum(self, generator):
        """Test GenerationMode enum values."""
        assert hasattr(GenerationMode, 'AI_POWERED')
        assert hasattr(GenerationMode, 'TEMPLATE_BASED')
        assert hasattr(GenerationMode, 'RULE_BASED')
        assert hasattr(GenerationMode, 'HYBRID')
    
    def test_create_cover_generator(self, generator):
        """Test create_cover_generator factory function."""
        gen = create_cover_generator()
        
        assert isinstance(gen, CoverGenerator)
    
    # ==================== AI-POWERED GENERATION TESTS ====================
    
    @patch('workspace.design.cover_generator.OpenAI')
    def test_generate_ai_powered(self, mock_openai, generator, sample_metadata):
        """Test AI-powered cover generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "design_id": "ai-generated-001",
            "design_style": "professional",
            "layout": {
                "layout_type": "modern",
                "title_position": "center",
                "author_position": "bottom",
                "image_position": "center"
            },
            "typography": {
                "title_font": "sans-serif",
                "title_size": 56,
                "title_weight": "bold",
                "author_font": "sans-serif",
                "author_size": 28,
                "author_weight": "medium"
            },
            "color_palette": {
                "primary_color": "#2C3E50",
                "secondary_color": "#34495E",
                "accent_color": "#3498DB",
                "background_color": "#ECF0F1"
            },
            "image_spec": {
                "image_type": "graphic",
                "image_url": "",
                "overlay_opacity": 0.1
            }
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = generator.generate(sample_metadata, mode=GenerationMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id == "ai-generated-001"
        assert result.design_style == DesignStyle.PROFESSIONAL
    
    @patch('workspace.design.cover_generator.OpenAI')
    def test_generate_ai_powered_invalid_response(self, mock_openai, generator, sample_metadata):
        """Test AI-powered cover generation with invalid response."""
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = generator.generate(sample_metadata, mode=GenerationMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
    
    @patch('workspace.design.cover_generator.OpenAI')
    def test_generate_ai_powered_empty_response(self, mock_openai, generator, sample_metadata):
        """Test AI-powered cover generation with empty response."""
        # Mock OpenAI response with empty content
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = generator.generate(sample_metadata, mode=GenerationMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
    
    @patch('workspace.design.cover_generator.OpenAI')
    def test_generate_ai_powered_timeout(self, mock_openai, generator, sample_metadata):
        """Test AI-powered cover generation with timeout."""
        # Mock OpenAI timeout
        from openai import RateLimitError
        mock_openai.return_value.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded", None)
        
        result = generator.generate(sample_metadata, mode=GenerationMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
    
    # ==================== TEMPLATE-BASED GENERATION TESTS ====================
    
    def test_generate_template_based(self, generator, sample_metadata):
        """Test template-based cover generation."""
        result = generator.generate(sample_metadata, mode=GenerationMode.TEMPLATE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    def test_generate_template_based_custom_style(self, generator, sample_metadata):
        """Test template-based cover generation with custom style."""
        result = generator.generate(
            sample_metadata,
            mode=GenerationMode.TEMPLATE_BASED,
            design_style=DesignStyle.FANTASY
        )
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.design_style == DesignStyle.FANTASY
    
    def test_generate_template_based_custom_layout(self, generator, sample_metadata):
        """Test template-based cover generation with custom layout."""
        result = generator.generate(
            sample_metadata,
            mode=GenerationMode.TEMPLATE_BASED,
            layout_type=LayoutType.CLASSIC
        )
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.layout.layout_type == LayoutType.CLASSIC
    
    def test_generate_template_based_fantasy_genre(self, generator):
        """Test template-based cover generation for fantasy genre."""
        metadata = BookMetadata(
            title="The Dragon's Quest",
            author="John Fantasy",
            genre="fantasy",
            target_audience="young_adult",
            book_length=450,
            publication_date="2024-01-15",
            series_name="Epic Chronicles",
            series_number=1,
            keywords=["fantasy", "dragons", "adventure"]
        )
        
        result = generator.generate(metadata, mode=GenerationMode.TEMPLATE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    def test_generate_template_based_mystery_genre(self, generator):
        """Test template-based cover generation for mystery genre."""
        metadata = BookMetadata(
            title="The Silent Witness",
            author="Jane Mystery",
            genre="mystery",
            target_audience="adult",
            book_length=320,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["mystery", "thriller", "crime"]
        )
        
        result = generator.generate(metadata, mode=GenerationMode.TEMPLATE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    # ==================== RULE-BASED GENERATION TESTS ====================
    
    def test_generate_rule_based(self, generator, sample_metadata):
        """Test rule-based cover generation."""
        result = generator.generate(sample_metadata, mode=GenerationMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    def test_generate_rule_based_genre_specific(self, generator, sample_metadata):
        """Test rule-based cover generation with genre-specific rules."""
        result = generator.generate(sample_metadata, mode=GenerationMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    def test_generate_rule_based_fantasy_genre(self, generator):
        """Test rule-based cover generation for fantasy genre."""
        metadata = BookMetadata(
            title="The Dragon's Quest",
            author="John Fantasy",
            genre="fantasy",
            target_audience="young_adult",
            book_length=450,
            publication_date="2024-01-15",
            series_name="Epic Chronicles",
            series_number=1,
            keywords=["fantasy", "dragons", "adventure"]
        )
        
        result = generator.generate(metadata, mode=GenerationMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    def test_generate_rule_based_mystery_genre(self, generator):
        """Test rule-based cover generation for mystery genre."""
        metadata = BookMetadata(
            title="The Silent Witness",
            author="Jane Mystery",
            genre="mystery",
            target_audience="adult",
            book_length=320,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["mystery", "thriller", "crime"]
        )
        
        result = generator.generate(metadata, mode=GenerationMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    # ==================== HYBRID GENERATION TESTS ====================
    
    def test_generate_hybrid(self, generator, sample_metadata):
        """Test hybrid cover generation."""
        result = generator.generate(sample_metadata, mode=GenerationMode.HYBRID)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.id is not None
    
    def test_generate_hybrid_with_constraints(self, generator, sample_metadata):
        """Test hybrid cover generation with constraints."""
        result = generator.generate(
            sample_metadata,
            mode=GenerationMode.HYBRID,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert result is not None
        assert isinstance(result, CoverDesign)
        assert result.design_style == DesignStyle.PROFESSIONAL
        assert result.layout.layout_type == LayoutType.MODERN
    
    # ==================== GENERATION COMPONENT TESTS ====================
    
    def test_generate_layout(self, generator, sample_metadata):
        """Test layout generation."""
        layout = generator._generate_layout(sample_metadata)
        
        assert layout is not None
        assert isinstance(layout, LayoutSpec)
        assert layout.layout_type is not None
    
    def test_generate_typography(self, generator, sample_metadata):
        """Test typography generation."""
        typography = generator._generate_typography(sample_metadata)
        
        assert typography is not None
        assert isinstance(typography, TypographySpec)
        assert typography.title_font is not None
    
    def test_generate_color_palette(self, generator, sample_metadata):
        """Test color palette generation."""
        palette = generator._generate_color_palette(sample_metadata)
        
        assert palette is not None
        assert isinstance(palette, ColorPalette)
        assert palette.primary_color is not None
    
    def test_generate_image_spec(self, generator, sample_metadata):
        """Test image specification generation."""
        image_spec = generator._generate_image_spec(sample_metadata)
        
        assert image_spec is not None
        assert isinstance(image_spec, ImageSpec)
        assert image_spec.image_type is not None
    
    # ==================== LAYOUT GENERATION TESTS ====================
    
    def test_generate_layout_professional(self, generator, sample_metadata):
        """Test layout generation for professional style."""
        layout = generator._generate_layout(sample_metadata, design_style=DesignStyle.PROFESSIONAL)
        
        assert layout is not None
        assert isinstance(layout, LayoutSpec)
    
    def test_generate_layout_fantasy(self, generator):
        """Test layout generation for fantasy style."""
        metadata = BookMetadata(
            title="The Dragon's Quest",
            author="John Fantasy",
            genre="fantasy",
            target_audience="young_adult",
            book_length=450,
            publication_date="2024-01-15",
            series_name="Epic Chronicles",
            series_number=1,
            keywords=["fantasy", "dragons", "adventure"]
        )
        
        layout = generator._generate_layout(metadata, design_style=DesignStyle.FANTASY)
        
        assert layout is not None
        assert isinstance(layout, LayoutSpec)
    
    def test_generate_layout_mystery(self, generator):
        """Test layout generation for mystery style."""
        metadata = BookMetadata(
            title="The Silent Witness",
            author="Jane Mystery",
            genre="mystery",
            target_audience="adult",
            book_length=320,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["mystery", "thriller", "crime"]
        )
        
        layout = generator._generate_layout(metadata, design_style=DesignStyle.DARK)
        
        assert layout is not None
        assert isinstance(layout, LayoutSpec)
    
    # ==================== TYPOGRAPHY GENERATION TESTS ====================
    
    def test_generate_typography_professional(self, generator, sample_metadata):
        """Test typography generation for professional style."""
        typography = generator._generate_typography(sample_metadata, design_style=DesignStyle.PROFESSIONAL)
        
        assert typography is not None
        assert isinstance(typography, TypographySpec)
    
    def test_generate_typography_fantasy(self, generator):
        """Test typography generation for fantasy style."""
        metadata = BookMetadata(
            title="The Dragon's Quest",
            author="John Fantasy",
            genre="fantasy",
            target_audience="young_adult",
            book_length=450,
            publication_date="2024-01-15",
            series_name="Epic Chronicles",
            series_number=1,
            keywords=["fantasy", "dragons", "adventure"]
        )
        
        typography = generator._generate_typography(metadata, design_style=DesignStyle.FANTASY)
        
        assert typography is not None
        assert isinstance(typography, TypographySpec)
    
    def test_generate_typography_mystery(self, generator):
        """Test typography generation for mystery style."""
        metadata = BookMetadata(
            title="The Silent Witness",
            author="Jane Mystery",
            genre="mystery",
            target_audience="adult",
            book_length=320,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["mystery", "thriller", "crime"]
        )
        
        typography = generator._generate_typography(metadata, design_style=DesignStyle.DARK)
        
        assert typography is not None
        assert isinstance(typography, TypographySpec)
    
    # ==================== COLOR PALETTE GENERATION TESTS ====================
    
    def test_generate_color_palette_professional(self, generator, sample_metadata):
        """Test color palette generation for professional style."""
        palette = generator._generate_color_palette(sample_metadata, design_style=DesignStyle.PROFESSIONAL)
        
        assert palette is not None
        assert isinstance(palette, ColorPalette)
    
    def test_generate_color_palette_fantasy(self, generator):
        """Test color palette generation for fantasy style."""
        metadata = BookMetadata(
            title="The Dragon's Quest",
            author="John Fantasy",
            genre="fantasy",
            target_audience="young_adult",
            book_length=450,
            publication_date="2024-01-15",
            series_name="Epic Chronicles",
            series_number=1,
            keywords=["fantasy", "dragons", "adventure"]
        )
        
        palette = generator._generate_color_palette(metadata, design_style=DesignStyle.FANTASY)
        
        assert palette is not None
        assert isinstance(palette, ColorPalette)
    
    def test_generate_color_palette_mystery(self, generator):
        """Test color palette generation for mystery style."""
        metadata = BookMetadata(
            title="The Silent Witness",
            author="Jane Mystery",
            genre="mystery",
            target_audience="adult",
            book_length=320,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["mystery", "thriller", "crime"]
        )
        
        palette = generator._generate_color_palette(metadata, design_style=DesignStyle.DARK)
        
        assert palette is not None
        assert isinstance(palette, ColorPalette)
    
    # ==================== IMAGE SPEC GENERATION TESTS ====================
    
    def test_generate_image_spec_professional(self, generator, sample_metadata):
        """Test image spec generation for professional style."""
        image_spec = generator._generate_image_spec(sample_metadata, design_style=DesignStyle.PROFESSIONAL)
        
        assert image_spec is not None
        assert isinstance(image_spec, ImageSpec)
    
    def test_generate_image_spec_fantasy(self, generator):
        """Test image spec generation for fantasy style."""
        metadata = BookMetadata(
            title="The Dragon's Quest",
            author="John Fantasy",
            genre="fantasy",
            target_audience="young_adult",
            book_length=450,
            publication_date="2024-01-15",
            series_name="Epic Chronicles",
            series_number=1,
            keywords=["fantasy", "dragons", "adventure"]
        )
        
        image_spec = generator._generate_image_spec(metadata, design_style=DesignStyle.FANTASY)
        
        assert image_spec is not None
        assert isinstance(image_spec, ImageSpec)
    
    def test_generate_image_spec_mystery(self, generator):
        """Test image spec generation for mystery style."""
        metadata = BookMetadata(
            title="The Silent Witness",
            author="Jane Mystery",
            genre="mystery",
            target_audience="adult",
            book_length=320,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["mystery", "thriller", "crime"]
        )
        
        image_spec = generator._generate_image_spec(metadata, design_style=DesignStyle.DARK)
        
        assert image_spec is not None
        assert isinstance(image_spec, ImageSpec)
    
    # ==================== GENERATION MODE SELECTION TESTS ====================
    
    def test_select_generation_mode_ai(self, generator):
        """Test AI-powered generation mode selection."""
        mode = generator._select_generation_mode(
            mode=GenerationMode.AI_POWERED,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == GenerationMode.AI_POWERED
    
    def test_select_generation_mode_template(self, generator):
        """Test template-based generation mode selection."""
        mode = generator._select_generation_mode(
            mode=GenerationMode.TEMPLATE_BASED,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == GenerationMode.TEMPLATE_BASED
    
    def test_select_generation_mode_rule(self, generator):
        """Test rule-based generation mode selection."""
        mode = generator._select_generation_mode(
            mode=GenerationMode.RULE_BASED,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == GenerationMode.RULE_BASED
    
    def test_select_generation_mode_hybrid(self, generator):
        """Test hybrid generation mode selection."""
        mode = generator._select_generation_mode(
            mode=GenerationMode.HYBRID,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == GenerationMode.HYBRID
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_generate_invalid_metadata(self, generator):
        """Test generation with invalid metadata."""
        with pytest.raises(ValueError):
            generator.generate(None, mode=GenerationMode.RULE_BASED)
    
    def test_generate_invalid_mode(self, generator, sample_metadata):
        """Test generation with invalid mode."""
        with pytest.raises(ValueError):
            generator.generate(sample_metadata, mode="invalid_mode")
    
    def test_generate_invalid_design_style(self, generator, sample_metadata):
        """Test generation with invalid design style."""
        with pytest.raises(ValueError):
            generator.generate(
                sample_metadata,
                mode=GenerationMode.RULE_BASED,
                design_style="invalid_style"
            )
    
    def test_generate_invalid_layout_type(self, generator, sample_metadata):
        """Test generation with invalid layout type."""
        with pytest.raises(ValueError):
            generator.generate(
                sample_metadata,
                mode=GenerationMode.RULE_BASED,
                layout_type="invalid_layout"
            )
    
    # ==================== BATCH GENERATION TESTS ====================
    
    def test_batch_generate(self, generator, sample_metadata):
        """Test batch generation."""
        results = generator.batch_generate([sample_metadata] * 3)
        
        assert len(results) == 3
        assert all(isinstance(r, CoverDesign) for r in results)
    
    def test_batch_generate_with_different_styles(self, generator):
        """Test batch generation with different styles."""
        metadatas = [
            BookMetadata(
                title="Book 1",
                author="Author 1",
                genre="business",
                target_audience="professionals",
                book_length=350,
                publication_date="2024-01-15",
                series_name=None,
                series_number=0,
                keywords=["business"]
            ),
            BookMetadata(
                title="Book 2",
                author="Author 2",
                genre="fantasy",
                target_audience="young_adult",
                book_length=450,
                publication_date="2024-01-15",
                series_name="Series 1",
                series_number=1,
                keywords=["fantasy"]
            ),
            BookMetadata(
                title="Book 3",
                author="Author 3",
                genre="mystery",
                target_audience="adult",
                book_length=320,
                publication_date="2024-01-15",
                series_name=None,
                series_number=0,
                keywords=["mystery"]
            )
        ]
        
        results = generator.batch_generate(metadatas)
        
        assert len(results) == 3
        assert all(isinstance(r, CoverDesign) for r in results)
    
    # ==================== GENERATION EXPORT TESTS ====================
    
    def test_export_design_json(self, generator, sample_design):
        """Test design export to JSON."""
        json_str = generator.export_design(sample_design, format="json")
        
        assert json_str is not None
        assert isinstance(json_str, str)
        assert "design_id" in json_str
        assert "title" in json_str
    
    def test_export_design_dict(self, generator, sample_design):
        """Test design export to dict."""
        design_dict = generator.export_design(sample_design, format="dict")
        
        assert design_dict is not None
        assert isinstance(design_dict, dict)
        assert "design_id" in design_dict
        assert "title" in design_dict
    
    def test_export_design_invalid_format(self, generator, sample_design):
        """Test design export with invalid format."""
        with pytest.raises(ValueError):
            generator.export_design(sample_design, format="invalid_format")
    
    # ==================== GENERATION IMPORT TESTS ====================
    
    def test_import_design_from_dict(self, generator, sample_design):
        """Test design import from dict."""
        design_dict = sample_design.to_dict()
        
        imported_design = generator.import_design(design_dict)
        
        assert imported_design is not None
        assert isinstance(imported_design, CoverDesign)
        assert imported_design.id == sample_design.id
    
    def test_import_design_from_json(self, generator, sample_design):
        """Test design import from JSON."""
        json_str = json.dumps(sample_design.to_dict())
        
        imported_design = generator.import_design(json_str)
        
        assert imported_design is not None
        assert isinstance(imported_design, CoverDesign)
        assert imported_design.id == sample_design.id
    
    def test_import_design_invalid(self, generator):
        """Test design import with invalid data."""
        with pytest.raises(ValueError):
            generator.import_design("invalid_data")


class TestGenerateCoverFunction:
    """Tests for the generate_cover convenience function."""
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample book metadata for testing."""
        return BookMetadata(
            title="The Art of Design",
            author="Jane Smith",
            genre="business",
            target_audience="professionals",
            book_length=350,
            publication_date="2024-01-15",
            series_name=None,
            series_number=0,
            keywords=["design", "business", "creativity"]
        )
    
    def test_generate_cover_rule_based(self, sample_metadata):
        """Test generate_cover with rule-based mode."""
        result = generate_cover(sample_metadata, mode=GenerationMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
    
    def test_generate_cover_template_based(self, sample_metadata):
        """Test generate_cover with template-based mode."""
        result = generate_cover(sample_metadata, mode=GenerationMode.TEMPLATE_BASED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
    
    def test_generate_cover_hybrid(self, sample_metadata):
        """Test generate_cover with hybrid mode."""
        result = generate_cover(sample_metadata, mode=GenerationMode.HYBRID)
        
        assert result is not None
        assert isinstance(result, CoverDesign)
    
    def test_generate_cover_ai_powered(self, sample_metadata):
        """Test generate_cover with AI-powered mode."""
        result = generate_cover(sample_metadata, mode=GenerationMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, CoverDesign)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
