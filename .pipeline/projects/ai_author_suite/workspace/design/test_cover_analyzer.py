import pytest
import json
import tempfile
import os
import sys
import pathlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the workspace root to sys.path so absolute imports work from any cwd
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

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
    CoverAnalysis as AnalysisResult,
    AnalysisSeverity as DesignScore,
)
# DesignFeedback may not exist in this model version — use a sentinel
DesignFeedback = dict

from design.cover_analyzer import (
    CoverAnalyzer,
    AnalysisMode,
    create_cover_analyzer,
    analyze_cover,
)



class TestCoverAnalyzer:
    """Tests for the CoverAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a CoverAnalyzer instance for testing."""
        return CoverAnalyzer()
    
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
    
    # ==================== ANALYSIS MODE TESTS ====================
    
    def test_analysis_mode_enum(self, analyzer):
        """Test AnalysisMode enum values."""
        assert hasattr(AnalysisMode, 'AI_POWERED')
        assert hasattr(AnalysisMode, 'TEMPLATE_BASED')
        assert hasattr(AnalysisMode, 'RULE_BASED')
        assert hasattr(AnalysisMode, 'HYBRID')
    
    def test_create_cover_analyzer(self, analyzer):
        """Test create_cover_analyzer factory function."""
        ana = create_cover_analyzer()
        
        assert isinstance(ana, CoverAnalyzer)
    
    # ==================== AI-POWERED ANALYSIS TESTS ====================
    
    @patch('workspace.design.cover_analyzer.OpenAI')
    def test_analyze_ai_powered(self, mock_openai, analyzer, sample_design):
        """Test AI-powered cover analysis."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "overall_score": 85,
            "scores": {
                "readability": 90,
                "visual_appeal": 85,
                "genre_alignment": 80,
                "color_harmony": 85,
                "typography_balance": 90,
                "layout_effectiveness": 85
            },
            "feedback": {
                "strengths": [
                    "Excellent readability with clear title hierarchy",
                    "Strong color contrast for professional appeal",
                    "Well-balanced typography"
                ],
                "weaknesses": [
                    "Could improve genre-specific visual cues",
                    "Accent color could be more vibrant"
                ],
                "suggestions": [
                    "Consider adding genre-specific imagery",
                    "Increase accent color saturation"
                ]
            }
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = analyzer.analyze(sample_design, mode=AnalysisMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.overall_score == 85
        assert len(result.feedback.strengths) == 3
    
    @patch('workspace.design.cover_analyzer.OpenAI')
    def test_analyze_ai_powered_invalid_response(self, mock_openai, analyzer, sample_design):
        """Test AI-powered cover analysis with invalid response."""
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = analyzer.analyze(sample_design, mode=AnalysisMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
    
    @patch('workspace.design.cover_analyzer.OpenAI')
    def test_analyze_ai_powered_empty_response(self, mock_openai, analyzer, sample_design):
        """Test AI-powered cover analysis with empty response."""
        # Mock OpenAI response with empty content
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = analyzer.analyze(sample_design, mode=AnalysisMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
    
    @patch('workspace.design.cover_analyzer.OpenAI')
    def test_analyze_ai_powered_timeout(self, mock_openai, analyzer, sample_design):
        """Test AI-powered cover analysis with timeout."""
        # Mock OpenAI timeout
        from openai import RateLimitError
        mock_openai.return_value.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded", None)
        
        result = analyzer.analyze(sample_design, mode=AnalysisMode.AI_POWERED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
    
    # ==================== TEMPLATE-BASED ANALYSIS TESTS ====================
    
    def test_analyze_template_based(self, analyzer, sample_design):
        """Test template-based cover analysis."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.TEMPLATE_BASED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.overall_score > 0
    
    def test_analyze_template_based_custom_style(self, analyzer, sample_design):
        """Test template-based cover analysis with custom style."""
        result = analyzer.analyze(
            sample_design,
            mode=AnalysisMode.TEMPLATE_BASED,
            design_style=DesignStyle.FANTASY
        )
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
    
    def test_analyze_template_based_custom_layout(self, analyzer, sample_design):
        """Test template-based cover analysis with custom layout."""
        result = analyzer.analyze(
            sample_design,
            mode=AnalysisMode.TEMPLATE_BASED,
            layout_type=LayoutType.CLASSIC
        )
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
    
    # ==================== RULE-BASED ANALYSIS TESTS ====================
    
    def test_analyze_rule_based(self, analyzer, sample_design):
        """Test rule-based cover analysis."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.overall_score > 0
    
    def test_analyze_rule_based_genre_specific(self, analyzer, sample_design):
        """Test rule-based cover analysis with genre-specific rules."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.scores.genre_alignment > 0
    
    def test_analyze_rule_based_fantasy_genre(self, analyzer):
        """Test rule-based cover analysis for fantasy genre."""
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
        
        design = CoverDesign(
            id="test-002",
            metadata=metadata,
            design_style=DesignStyle.FANTASY,
            layout=LayoutSpec(
                layout_type=LayoutType.MODERN,
                title_position="center",
                author_position="bottom",
                image_position="center"
            ),
            typography=TypographySpec(
                title_font="serif",
                title_size=64,
                title_weight="bold",
                author_font="serif",
                author_size=32,
                author_weight="medium"
            ),
            color_palette=ColorPalette(
                primary_color="#8B4513",
                secondary_color="#654321",
                accent_color="#FFD700",
                background_color="#F5DEB3"
            ),
            image_spec=ImageSpec(
                image_type=ImageType.ILLUSTRATION,
                image_url="",
                overlay_opacity=0.2
            )
        )
        
        result = analyzer.analyze(design, mode=AnalysisMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.scores.genre_alignment > 0
    
    def test_analyze_rule_based_mystery_genre(self, analyzer):
        """Test rule-based cover analysis for mystery genre."""
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
        
        design = CoverDesign(
            id="test-003",
            metadata=metadata,
            design_style=DesignStyle.DARK,
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
                primary_color="#000000",
                secondary_color="#1C1C1C",
                accent_color="#FF0000",
                background_color="#0A0A0A"
            ),
            image_spec=ImageSpec(
                image_type=ImageType.PHOTOGRAPHY,
                image_url="",
                overlay_opacity=0.3
            )
        )
        
        result = analyzer.analyze(design, mode=AnalysisMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.scores.genre_alignment > 0
    
    # ==================== HYBRID ANALYSIS TESTS ====================
    
    def test_analyze_hybrid(self, analyzer, sample_design):
        """Test hybrid cover analysis."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.HYBRID)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.overall_score > 0
    
    def test_analyze_hybrid_with_constraints(self, analyzer, sample_design):
        """Test hybrid cover analysis with constraints."""
        result = analyzer.analyze(
            sample_design,
            mode=AnalysisMode.HYBRID,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
    
    # ==================== ANALYSIS COMPONENT TESTS ====================
    
    def test_analyze_readability(self, analyzer, sample_design):
        """Test readability analysis."""
        score = analyzer._analyze_readability(sample_design)
        
        assert score is not None
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_analyze_visual_appeal(self, analyzer, sample_design):
        """Test visual appeal analysis."""
        score = analyzer._analyze_visual_appeal(sample_design)
        
        assert score is not None
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_analyze_genre_alignment(self, analyzer, sample_design):
        """Test genre alignment analysis."""
        score = analyzer._analyze_genre_alignment(sample_design)
        
        assert score is not None
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_analyze_color_harmony(self, analyzer, sample_design):
        """Test color harmony analysis."""
        score = analyzer._analyze_color_harmony(sample_design)
        
        assert score is not None
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_analyze_typography_balance(self, analyzer, sample_design):
        """Test typography balance analysis."""
        score = analyzer._analyze_typography_balance(sample_design)
        
        assert score is not None
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_analyze_layout_effectiveness(self, analyzer, sample_design):
        """Test layout effectiveness analysis."""
        score = analyzer._analyze_layout_effectiveness(sample_design)
        
        assert score is not None
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    # ==================== FEEDBACK GENERATION TESTS ====================
    
    def test_generate_feedback_strengths(self, analyzer, sample_design):
        """Test feedback strengths generation."""
        strengths = analyzer._generate_feedback_strengths(sample_design)
        
        assert strengths is not None
        assert isinstance(strengths, list)
        assert len(strengths) > 0
    
    def test_generate_feedback_weaknesses(self, analyzer, sample_design):
        """Test feedback weaknesses generation."""
        weaknesses = analyzer._generate_feedback_weaknesses(sample_design)
        
        assert weaknesses is not None
        assert isinstance(weaknesses, list)
    
    def test_generate_feedback_suggestions(self, analyzer, sample_design):
        """Test feedback suggestions generation."""
        suggestions = analyzer._generate_feedback_suggestions(sample_design)
        
        assert suggestions is not None
        assert isinstance(suggestions, list)
    
    def test_generate_feedback(self, analyzer, sample_design):
        """Test feedback generation."""
        feedback = analyzer._generate_feedback(sample_design)
        
        assert feedback is not None
        assert isinstance(feedback, DesignFeedback)
        assert len(feedback.strengths) > 0
    
    # ==================== DESIGN SCORE TESTS ====================
    
    def test_create_design_score(self, analyzer):
        """Test design score creation."""
        score = analyzer._create_design_score(
            readability=90,
            visual_appeal=85,
            genre_alignment=80,
            color_harmony=85,
            typography_balance=90,
            layout_effectiveness=85
        )
        
        assert score is not None
        assert isinstance(score, DesignScore)
        assert score.readability == 90
        assert score.visual_appeal == 85
    
    def test_calculate_overall_score(self, analyzer):
        """Test overall score calculation."""
        scores = analyzer._create_design_score(
            readability=90,
            visual_appeal=85,
            genre_alignment=80,
            color_harmony=85,
            typography_balance=90,
            layout_effectiveness=85
        )
        
        overall = analyzer._calculate_overall_score(scores)
        
        assert overall is not None
        assert isinstance(overall, int)
        assert 0 <= overall <= 100
    
    # ==================== ANALYSIS RESULT TESTS ====================
    
    def test_create_analysis_result(self, analyzer, sample_design):
        """Test analysis result creation."""
        result = analyzer._create_analysis_result(
            design=sample_design,
            scores=analyzer._create_design_score(
                readability=90,
                visual_appeal=85,
                genre_alignment=80,
                color_harmony=85,
                typography_balance=90,
                layout_effectiveness=85
            ),
            feedback=analyzer._generate_feedback(sample_design)
        )
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.design_id == sample_design.id
        assert result.overall_score > 0
    
    # ==================== ANALYSIS MODE SELECTION TESTS ====================
    
    def test_select_analysis_mode_ai(self, analyzer):
        """Test AI-powered analysis mode selection."""
        mode = analyzer._select_analysis_mode(
            mode=AnalysisMode.AI_POWERED,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == AnalysisMode.AI_POWERED
    
    def test_select_analysis_mode_template(self, analyzer):
        """Test template-based analysis mode selection."""
        mode = analyzer._select_analysis_mode(
            mode=AnalysisMode.TEMPLATE_BASED,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == AnalysisMode.TEMPLATE_BASED
    
    def test_select_analysis_mode_rule(self, analyzer):
        """Test rule-based analysis mode selection."""
        mode = analyzer._select_analysis_mode(
            mode=AnalysisMode.RULE_BASED,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == AnalysisMode.RULE_BASED
    
    def test_select_analysis_mode_hybrid(self, analyzer):
        """Test hybrid analysis mode selection."""
        mode = analyzer._select_analysis_mode(
            mode=AnalysisMode.HYBRID,
            design_style=DesignStyle.PROFESSIONAL,
            layout_type=LayoutType.MODERN
        )
        
        assert mode == AnalysisMode.HYBRID
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_analyze_invalid_design(self, analyzer):
        """Test analysis with invalid design."""
        with pytest.raises(ValueError):
            analyzer.analyze(None, mode=AnalysisMode.RULE_BASED)
    
    def test_analyze_invalid_mode(self, analyzer, sample_design):
        """Test analysis with invalid mode."""
        with pytest.raises(ValueError):
            analyzer.analyze(sample_design, mode="invalid_mode")
    
    def test_analyze_invalid_design_style(self, analyzer, sample_design):
        """Test analysis with invalid design style."""
        with pytest.raises(ValueError):
            analyzer.analyze(
                sample_design,
                mode=AnalysisMode.RULE_BASED,
                design_style="invalid_style"
            )
    
    def test_analyze_invalid_layout_type(self, analyzer, sample_design):
        """Test analysis with invalid layout type."""
        with pytest.raises(ValueError):
            analyzer.analyze(
                sample_design,
                mode=AnalysisMode.RULE_BASED,
                layout_type="invalid_layout"
            )
    
    # ==================== BATCH ANALYSIS TESTS ====================
    
    def test_batch_analyze(self, analyzer, sample_design):
        """Test batch analysis."""
        results = analyzer.batch_analyze([sample_design] * 3)
        
        assert len(results) == 3
        assert all(isinstance(r, AnalysisResult) for r in results)
    
    def test_batch_analyze_with_different_styles(self, analyzer):
        """Test batch analysis with different styles."""
        designs = [
            CoverDesign(
                id="test-001",
                metadata=BookMetadata(
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
            ),
            CoverDesign(
                id="test-002",
                metadata=BookMetadata(
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
                design_style=DesignStyle.FANTASY,
                layout=LayoutSpec(
                    layout_type=LayoutType.MODERN,
                    title_position="center",
                    author_position="bottom",
                    image_position="center"
                ),
                typography=TypographySpec(
                    title_font="serif",
                    title_size=64,
                    title_weight="bold",
                    author_font="serif",
                    author_size=32,
                    author_weight="medium"
                ),
                color_palette=ColorPalette(
                    primary_color="#8B4513",
                    secondary_color="#654321",
                    accent_color="#FFD700",
                    background_color="#F5DEB3"
                ),
                image_spec=ImageSpec(
                    image_type=ImageType.ILLUSTRATION,
                    image_url="",
                    overlay_opacity=0.2
                )
            ),
            CoverDesign(
                id="test-003",
                metadata=BookMetadata(
                    title="Book 3",
                    author="Author 3",
                    genre="mystery",
                    target_audience="adult",
                    book_length=320,
                    publication_date="2024-01-15",
                    series_name=None,
                    series_number=0,
                    keywords=["mystery"]
                ),
                design_style=DesignStyle.DARK,
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
                    primary_color="#000000",
                    secondary_color="#1C1C1C",
                    accent_color="#FF0000",
                    background_color="#0A0A0A"
                ),
                image_spec=ImageSpec(
                    image_type=ImageType.PHOTOGRAPHY,
                    image_url="",
                    overlay_opacity=0.3
                )
            )
        ]
        
        results = analyzer.batch_analyze(designs)
        
        assert len(results) == 3
        assert all(isinstance(r, AnalysisResult) for r in results)
    
    # ==================== ANALYSIS EXPORT TESTS ====================
    
    def test_export_analysis_json(self, analyzer, sample_design):
        """Test analysis export to JSON."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.RULE_BASED)
        json_str = analyzer.export_analysis(result, format="json")
        
        assert json_str is not None
        assert isinstance(json_str, str)
        assert "overall_score" in json_str
        assert "design_id" in json_str
    
    def test_export_analysis_dict(self, analyzer, sample_design):
        """Test analysis export to dict."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.RULE_BASED)
        analysis_dict = analyzer.export_analysis(result, format="dict")
        
        assert analysis_dict is not None
        assert isinstance(analysis_dict, dict)
        assert "overall_score" in analysis_dict
        assert "design_id" in analysis_dict
    
    def test_export_analysis_invalid_format(self, analyzer, sample_design):
        """Test analysis export with invalid format."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.RULE_BASED)
        with pytest.raises(ValueError):
            analyzer.export_analysis(result, format="invalid_format")
    
    # ==================== ANALYSIS IMPORT TESTS ====================
    
    def test_import_analysis_from_dict(self, analyzer, sample_design):
        """Test analysis import from dict."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.RULE_BASED)
        result_dict = result.to_dict()
        
        imported_result = analyzer.import_analysis(result_dict)
        
        assert imported_result is not None
        assert isinstance(imported_result, AnalysisResult)
        assert imported_result.design_id == result.design_id
        assert imported_result.overall_score == result.overall_score
    
    def test_import_analysis_from_json(self, analyzer, sample_design):
        """Test analysis import from JSON."""
        result = analyzer.analyze(sample_design, mode=AnalysisMode.RULE_BASED)
        json_str = json.dumps(result.to_dict())
        
        imported_result = analyzer.import_analysis(json_str)
        
        assert imported_result is not None
        assert isinstance(imported_result, AnalysisResult)
        assert imported_result.design_id == result.design_id
        assert imported_result.overall_score == result.overall_score
    
    def test_import_analysis_invalid(self, analyzer):
        """Test analysis import with invalid data."""
        with pytest.raises(ValueError):
            analyzer.import_analysis("invalid_data")


class TestAnalyzeCoverFunction:
    """Tests for the analyze_cover convenience function."""
    
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
    
    def test_analyze_cover_rule_based(self, sample_design):
        """Test analyze_cover with rule-based mode."""
        result = analyze_cover(sample_design, mode=AnalysisMode.RULE_BASED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.design_id == "test-001"
    
    def test_analyze_cover_template_based(self, sample_design):
        """Test analyze_cover with template-based mode."""
        result = analyze_cover(sample_design, mode=AnalysisMode.TEMPLATE_BASED)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.design_id == "test-001"
    
    def test_analyze_cover_hybrid(self, sample_design):
        """Test analyze_cover with hybrid mode."""
        result = analyze_cover(sample_design, mode=AnalysisMode.HYBRID)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.design_id == "test-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
