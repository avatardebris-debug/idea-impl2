"""
Tests for Cover Manager module.

This module contains comprehensive tests for the CoverManager class,
testing all major functionality including analysis, generation, optimization,
and A/B testing.
"""

import pytest
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import json
import tempfile
import os
from pathlib import Path

from design.models import (
    CoverDesign,
    CoverAnalysis,
    DesignRecommendation,
    ColorPalette,
    TypographySpec,
    LayoutSpec,
    ImageSpec,
    DesignStyle,
    LayoutType,
    ImageType,
    BookMetadata,
    AnalysisCategory,
    RecommendationPriority,
)
from design.cover_manager import (
    CoverManager,
    create_cover_manager,
    analyze_cover,
    generate_cover,
    optimize_cover,
    run_ab_test,
)
from design.cover_generator import GenerationResult, Template


class TestCoverManager:
    """Tests for the CoverManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a CoverManager instance for testing."""
        return CoverManager()
    
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
    
    # ==================== ANALYSIS TESTS ====================
    
    def test_analyze_cover(self, manager, sample_design):
        """Test cover analysis functionality."""
        analysis = manager.analyze_cover(sample_design)
        
        assert analysis is not None
        assert isinstance(analysis, CoverAnalysis)
        assert analysis.design_id == sample_design.id
        assert analysis.overall_score > 0
        assert len(analysis.category_scores) == 5
        assert len(analysis.recommendations) >= 0
    
    def test_get_analysis_categories(self, manager):
        """Test getting analysis categories."""
        categories = manager.get_analysis_categories()
        
        assert len(categories) == 5
        assert "visual_hierarchy" in categories
        assert "color_contrast" in categories
        assert "readability" in categories
        assert "genre_appropriateness" in categories
        assert "market_alignment" in categories
    
    def test_get_recommendations(self, manager, sample_design):
        """Test getting recommendations."""
        recommendations = manager.get_recommendations(sample_design)
        
        assert isinstance(recommendations, list)
        assert all(isinstance(rec, DesignRecommendation) for rec in recommendations)
    
    def test_get_recommendations_by_category(self, manager, sample_design):
        """Test filtering recommendations by category."""
        recommendations = manager.get_recommendations(
            sample_design, 
            AnalysisCategory.VISUAL_HIERARCHY
        )
        
        assert all(rec.category == AnalysisCategory.VISUAL_HIERARCHY 
                  for rec in recommendations)
    
    # ==================== GENERATION TESTS ====================
    
    def test_generate_from_template(self, manager, sample_metadata):
        """Test generating cover from template."""
        result = manager.generate_from_template(
            "business_professional",
            sample_metadata
        )
        
        assert result is not None
        assert isinstance(result, GenerationResult)
        assert result.generation_method == "template"
        assert result.template_used == "business_professional"
        assert result.design is not None
        assert result.design.metadata.title == sample_metadata.title
    
    def test_generate_from_specification(self, manager, sample_metadata):
        """Test generating cover from specification."""
        result = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL,
            optimize=True
        )
        
        assert result is not None
        assert isinstance(result, GenerationResult)
        assert result.generation_method == "specification"
        assert result.design is not None
        assert result.design.design_style == DesignStyle.PROFESSIONAL
    
    def test_generate_variants(self, manager, sample_metadata):
        """Test generating multiple variants."""
        variants = manager.generate_variants(sample_metadata, num_variants=3)
        
        assert len(variants) == 3
        assert all(isinstance(v, GenerationResult) for v in variants)
        assert all(v.design is not None for v in variants)
    
    def test_get_templates(self, manager):
        """Test getting list of templates."""
        templates = manager.get_templates()
        
        assert len(templates) > 0
        assert all(isinstance(t, Template) for t in templates)
    
    def test_get_template(self, manager):
        """Test getting specific template."""
        template = manager.get_template("business_professional")
        
        assert template is not None
        assert template.name == "business_professional"
    
    def test_get_nonexistent_template(self, manager):
        """Test getting non-existent template."""
        template = manager.get_template("nonexistent_template")
        
        assert template is None
    
    # ==================== OPTIMIZATION TESTS ====================
    
    def test_optimize_cover(self, manager, sample_design):
        """Test cover optimization."""
        result = manager.optimize_cover(sample_design)
        
        assert result is not None
        assert result.optimized_design is not None
        assert result.optimized_design.id == sample_design.id
        assert result.improvement_score >= 0
    
    def test_generate_optimization_variants(self, manager, sample_design):
        """Test generating optimization variants."""
        variants = manager.generate_optimization_variants(sample_design, num_variants=3)
        
        assert len(variants) == 3
        assert all(isinstance(v, CoverDesign) for v in variants)
    
    def test_iterative_optimization(self, manager, sample_design):
        """Test iterative optimization."""
        result = manager.iterative_optimization(sample_design, max_iterations=3)
        
        assert result is not None
        assert result.optimized_design is not None
        assert result.iterations >= 0
    
    # ==================== A/B TESTING TESTS ====================
    
    def test_run_ab_test(self, manager, sample_metadata):
        """Test A/B testing."""
        variant_a = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL
        ).design
        
        variant_b = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.MODERN
        ).design
        
        result = manager.run_ab_test(variant_a, variant_b)
        
        assert result is not None
        assert result.winner in ["A", "B"]
        assert result.metric_a > 0
        assert result.metric_b > 0
    
    # ==================== BATCH OPERATIONS TESTS ====================
    
    def test_batch_analyze(self, manager, sample_metadata):
        """Test batch analysis."""
        designs = [
            CoverDesign(
                id=f"test-{i}",
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
            for i in range(3)
        ]
        
        analyses = manager.batch_analyze(designs)
        
        assert len(analyses) == 3
        assert all(isinstance(a, CoverAnalysis) for a in analyses)
    
    def test_batch_optimize(self, manager, sample_metadata):
        """Test batch optimization."""
        designs = [
            CoverDesign(
                id=f"test-{i}",
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
            for i in range(3)
        ]
        
        results = manager.batch_optimize(designs)
        
        assert len(results) == 3
        assert all(hasattr(r, 'optimized_design') for r in results)
    
    def test_batch_generate(self, manager, sample_metadata):
        """Test batch generation."""
        metadata_list = [
            BookMetadata(
                title=f"Book {i}",
                author="Author",
                genre="fiction",
                target_audience="general",
                book_length=300,
                publication_date="2024-01-01",
                series_name=None,
                series_number=0,
                keywords=["test"]
            )
            for i in range(3)
        ]
        
        results = manager.batch_generate(metadata_list)
        
        assert len(results) == 3
        assert all(isinstance(r, GenerationResult) for r in results)
    
    # ==================== DESIGN MANAGEMENT TESTS ====================
    
    def test_save_design(self, manager, sample_design):
        """Test saving a design."""
        design_id = manager.save_design(sample_design)
        
        assert design_id == sample_design.id
        assert manager.get_design(design_id) is not None
    
    def test_save_design_with_custom_id(self, manager, sample_design):
        """Test saving a design with custom ID."""
        custom_id = "custom-design-id"
        design_id = manager.save_design(sample_design, custom_id)
        
        assert design_id == custom_id
        assert manager.get_design(custom_id) is not None
    
    def test_get_design(self, manager, sample_design):
        """Test retrieving a saved design."""
        manager.save_design(sample_design)
        retrieved = manager.get_design(sample_design.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_design.id
    
    def test_get_nonexistent_design(self, manager):
        """Test retrieving non-existent design."""
        retrieved = manager.get_design("nonexistent")
        
        assert retrieved is None
    
    def test_list_saved_designs(self, manager, sample_design):
        """Test listing saved designs."""
        manager.save_design(sample_design)
        design_ids = manager.list_saved_designs()
        
        assert sample_design.id in design_ids
    
    def test_delete_design(self, manager, sample_design):
        """Test deleting a design."""
        manager.save_design(sample_design)
        result = manager.delete_design(sample_design.id)
        
        assert result is True
        assert manager.get_design(sample_design.id) is None
    
    def test_delete_nonexistent_design(self, manager):
        """Test deleting non-existent design."""
        result = manager.delete_design("nonexistent")
        
        assert result is False
    
    # ==================== UTILITY TESTS ====================
    
    def test_get_design_summary(self, manager, sample_design):
        """Test getting design summary."""
        summary = manager.get_design_summary(sample_design)
        
        assert isinstance(summary, str)
        assert "DESIGN SUMMARY" in summary
        assert sample_metadata.title in summary
    
    def test_get_analysis_summary(self, manager, sample_design):
        """Test getting analysis summary."""
        analysis = manager.analyze_cover(sample_design)
        summary = manager.get_analysis_summary(analysis)
        
        assert isinstance(summary, str)
        assert "ANALYSIS SUMMARY" in summary
    
    def test_get_optimization_summary(self, manager, sample_design):
        """Test getting optimization summary."""
        result = manager.optimize_cover(sample_design)
        summary = manager.get_optimization_summary(result)
        
        assert isinstance(summary, str)
        assert "OPTIMIZATION SUMMARY" in summary
    
    def test_get_generation_summary(self, manager, sample_metadata):
        """Test getting generation summary."""
        result = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL
        )
        summary = manager.get_generation_summary(result)
        
        assert isinstance(summary, str)
        assert "GENERATION SUMMARY" in summary
    
    def test_get_ab_test_summary(self, manager, sample_metadata):
        """Test getting A/B test summary."""
        variant_a = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL
        ).design
        
        variant_b = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.MODERN
        ).design
        
        result = manager.run_ab_test(variant_a, variant_b)
        summary = manager.get_ab_test_summary(result)
        
        assert isinstance(summary, str)
        assert "A/B TEST SUMMARY" in summary
    
    # ==================== EXPORT/IMPORT TESTS ====================
    
    def test_export_design(self, manager, sample_design):
        """Test exporting a design."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            result = manager.export_design(sample_design, filepath)
            
            assert result is True
            assert os.path.exists(filepath)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert data["id"] == sample_design.id
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_import_design(self, manager, sample_design):
        """Test importing a design."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            manager.export_design(sample_design, filepath)
            imported = manager.import_design(filepath)
            
            assert imported is not None
            assert imported.id == sample_design.id
            assert imported.metadata.title == sample_design.metadata.title
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_export_analysis(self, manager, sample_design):
        """Test exporting an analysis."""
        analysis = manager.analyze_cover(sample_design)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            result = manager.export_analysis(analysis, filepath)
            
            assert result is True
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_import_analysis(self, manager, sample_design):
        """Test importing an analysis."""
        analysis = manager.analyze_cover(sample_design)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            manager.export_analysis(analysis, filepath)
            imported = manager.import_analysis(filepath)
            
            assert imported is not None
            assert imported.design_id == analysis.design_id
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_export_optimization_result(self, manager, sample_design):
        """Test exporting optimization result."""
        result = manager.optimize_cover(sample_design)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            exported = manager.export_optimization_result(result, filepath)
            
            assert exported is True
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_export_generation_result(self, manager, sample_metadata):
        """Test exporting generation result."""
        result = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            exported = manager.export_generation_result(result, filepath)
            
            assert exported is True
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_export_ab_test_result(self, manager, sample_metadata):
        """Test exporting A/B test result."""
        variant_a = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL
        ).design
        
        variant_b = manager.generate_from_specification(
            metadata=sample_metadata,
            design_style=DesignStyle.MODERN
        ).design
        
        result = manager.run_ab_test(variant_a, variant_b)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            exported = manager.export_ab_test_result(result, filepath)
            
            assert exported is True
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_create_cover_manager(self):
        """Test creating cover manager."""
        manager = create_cover_manager()
        
        assert isinstance(manager, CoverManager)
    
    def test_analyze_cover_function(self, sample_metadata):
        """Test analyze_cover convenience function."""
        design = CoverDesign(
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
        
        analysis = analyze_cover(design)
        
        assert isinstance(analysis, CoverAnalysis)
        assert analysis.design_id == design.id
    
    def test_generate_cover_function(self, sample_metadata):
        """Test generate_cover convenience function."""
        result = generate_cover(
            metadata=sample_metadata,
            design_style=DesignStyle.PROFESSIONAL,
            optimize=True
        )
        
        assert isinstance(result, GenerationResult)
        assert result.design is not None
        assert result.design.metadata.title == sample_metadata.title
    
    def test_optimize_cover_function(self, sample_metadata):
        """Test optimize_cover convenience function."""
        design = CoverDesign(
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
        
        result = optimize_cover(design)
        
        assert result is not None
        assert result.optimized_design is not None
    
    def test_run_ab_test_function(self, sample_metadata):
        """Test run_ab_test convenience function."""
        variant_a = CoverDesign(
            id="variant-a",
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
        
        variant_b = CoverDesign(
            id="variant-b",
            metadata=sample_metadata,
            design_style=DesignStyle.MODERN,
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
                primary_color="#E74C3C",
                secondary_color="#C0392B",
                accent_color="#F39C12",
                background_color="#FDFEFE"
            ),
            image_spec=ImageSpec(
                image_type=ImageType.GRAPHIC,
                image_url="",
                overlay_opacity=0.1
            )
        )
        
        result = run_ab_test(variant_a, variant_b)
        
        assert result is not None
        assert result.winner in ["A", "B"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
