"""Tests for the extraction pipeline."""

import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction import (
    ExtractionPipeline,
    ExtractionPipelineResult,
    VitalExtractor,
    VitalConcept,
    ConceptRelationship,
    VitalExtractionResult,
    PatternGenerator,
    PatternExtractionResult,
    OutlineGenerator,
    OutlineExtractionResult,
    LearningModule,
    LearningActivity,
    ModuleSequence,
    TimeEstimates,
    ExtractionOrchestrator,
    ExtractionResult,
    SummaryGenerator,
)
from extraction.patterns.learning_patterns import PatternGenerator, LearningPattern, CompressionOpportunity, EncodingStrategy, PatternExtractionResult as LearningPatternResult
from extraction.outline.outline_generator import OutlineGenerator, LearningModule as OutlineModule, LearningActivity as OutlineActivity, ModuleSequence, TimeEstimates, OutlineExtractionResult as OutlineResult
from extraction.eighty_twenty.vital_extractor import VitalExtractor, VitalConcept, ConceptRelationship, VitalExtractionResult


class TestVitalExtractor:
    """Tests for VitalExtractor class."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{}'))]
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def vital_extractor(self, mock_openai_client):
        """Create a VitalExtractor instance with mocked client."""
        with patch('extraction.eighty_twenty.vital_extractor.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            extractor = VitalExtractor(
                api_key="test_key",
                model="gpt-4o",
                temperature=0.5
            )
        return extractor
    
    @pytest.fixture
    def pattern_generator(self, mock_openai_client):
        """Create a PatternGenerator instance with mocked client."""
        with patch('extraction.patterns.learning_patterns.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            generator = PatternGenerator(
                api_key="test_key",
                model="gpt-4o",
                temperature=0.5
            )
        return generator
    
    @pytest.fixture
    def outline_generator(self, mock_openai_client):
        """Create an OutlineGenerator instance with mocked client."""
        with patch('extraction.outline.outline_generator.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            generator = OutlineGenerator(
                api_key="test_key",
                model="gpt-4o",
                temperature=0.5
            )
        return generator
    
    def test_initialization(self, vital_extractor):
        """Test that VitalExtractor initializes correctly."""
        assert vital_extractor.model == "gpt-4o"
        assert vital_extractor.temperature == 0.5
        assert vital_extractor.api_key == "test_key"
    
    def test_extract_vital_concepts_empty_response(self, vital_extractor):
        """Test extraction with empty response."""
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1", "Point 2"]
        }
        
        result = vital_extractor.extract_vital_concepts(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        assert isinstance(result, VitalExtractionResult)
        assert result.topic_name == "Test Topic"
        assert isinstance(result.vital_concepts, list)
        assert isinstance(result.concept_relationships, list)
        assert "phase_1_foundation" in result.learning_priority
    
    def test_extract_vital_concepts_with_valid_json(self, vital_extractor):
        """Test extraction with valid JSON response."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"test": "value"}'))]
        vital_extractor.client.chat.completions.create.return_value = mock_response
        
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1"]
        }
        
        result = vital_extractor.extract_vital_concepts(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        assert result.topic_name == "Test Topic"
    
    def test_analyze_frequency(self, vital_extractor):
        """Test frequency analysis."""
        key_points = [
            "Python is great",
            "Python is popular",
            "Python is easy"
        ]
        source_summaries = [
            {"key_points": ["Python is amazing", "Python is versatile"]}
        ]
        
        frequency = vital_extractor.analyze_frequency(key_points, source_summaries)
        
        assert isinstance(frequency, dict)
        assert "Python" in frequency or "python" in frequency
    
    def test_calculate_semantic_importance(self, vital_extractor):
        """Test semantic importance calculation."""
        content_summary = {
            "summary_text": "Python is essential for data analysis",
            "key_points": ["Python is important"]
        }
        frequency = {"Python": 5, "Data": 3}
        
        importance = vital_extractor.calculate_semantic_importance(
            "Python",
            content_summary,
            frequency
        )
        
        assert "frequency_score" in importance
        assert "centrality_score" in importance
        assert "impact_score" in importance
        assert "total_score" in importance
    
    def test_rank_concepts(self, vital_extractor):
        """Test concept ranking."""
        concepts = ["Python", "Data", "Analysis", "Learning"]
        content_summary = {
            "summary_text": "Python is essential",
            "key_points": ["Python is important"]
        }
        frequency = {"Python": 5, "Data": 3, "Analysis": 2, "Learning": 1}
        
        ranked = vital_extractor.rank_concepts(concepts, content_summary, frequency)
        
        assert isinstance(ranked, list)
        assert len(ranked) == 4
        # Python should be first due to highest frequency
        assert ranked[0][0] == "Python"
    
    def test_identify_vital_20(self, vital_extractor):
        """Test vital 20% identification."""
        ranked_concepts = [
            ("Concept1", 10),
            ("Concept2", 8),
            ("Concept3", 6),
            ("Concept4", 4),
            ("Concept5", 2)
        ]
        
        vital = vital_extractor.identify_vital_20(ranked_concepts, 5)
        
        assert len(vital) == 1  # 20% of 5 = 1
        assert "Concept1" in vital


class TestPatternGenerator:
    """Tests for PatternGenerator class."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{}'))]
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def pattern_generator(self, mock_openai_client):
        """Create a PatternGenerator instance with mocked client."""
        with patch('extraction.patterns.learning_patterns.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            generator = PatternGenerator(
                api_key="test_key",
                model="gpt-4o",
                temperature=0.5
            )
        return generator
    
    def test_initialization(self, pattern_generator):
        """Test that PatternGenerator initializes correctly."""
        assert pattern_generator.model == "gpt-4o"
        assert pattern_generator.temperature == 0.5
    
    def test_extract_patterns_empty_response(self, pattern_generator):
        """Test pattern extraction with empty response."""
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1"]
        }
        
        result = pattern_generator.extract_patterns(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        assert isinstance(result, LearningPatternResult)
        assert result.topic_name == "Test Topic"
        assert isinstance(result.learning_patterns, list)
        assert isinstance(result.compression_opportunities, list)
        assert isinstance(result.encoding_strategies, list)


class TestOutlineGenerator:
    """Tests for OutlineGenerator class."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{}'))]
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def outline_generator(self, mock_openai_client):
        """Create an OutlineGenerator instance with mocked client."""
        with patch('extraction.outline.outline_generator.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            generator = OutlineGenerator(
                api_key="test_key",
                model="gpt-4o",
                temperature=0.5
            )
        return generator
    
    def test_initialization(self, outline_generator):
        """Test that OutlineGenerator initializes correctly."""
        assert outline_generator.model == "gpt-4o"
        assert outline_generator.temperature == 0.5
    
    def test_extract_outline_empty_response(self, outline_generator):
        """Test outline extraction with empty response."""
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1"]
        }
        
        result = outline_generator.extract_outline(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        assert isinstance(result, OutlineResult)
        assert result.topic_name == "Test Topic"
        assert isinstance(result.learning_modules, list)
        assert isinstance(result.module_sequence, ModuleSequence)
        assert isinstance(result.time_estimates, TimeEstimates)


class TestExtractionPipeline:
    """Tests for ExtractionPipeline class."""
    
    @pytest.fixture
    def mock_extractors(self):
        """Create mock extractors for pipeline testing."""
        mock_vital = Mock(spec=VitalExtractor)
        mock_vital.extract_vital_concepts.return_value = VitalExtractionResult(
            topic_name="Test",
            vital_concepts=[],
            concept_relationships=[],
            learning_priority={"phase_1_foundation": [], "phase_2_core": [], "phase_3_advanced": []}
        )
        
        mock_pattern = Mock(spec=PatternGenerator)
        mock_pattern.extract_patterns.return_value = LearningPatternResult(
            topic_name="Test",
            learning_patterns=[],
            compression_opportunities=[],
            frequency_patterns={},
            encoding_strategies=[]
        )
        
        mock_outline = Mock(spec=OutlineGenerator)
        mock_outline.extract_outline.return_value = OutlineResult(
            topic_name="Test",
            learning_modules=[],
            module_sequence=ModuleSequence(
                linear_path=["module1", "module2"],
                parallel_paths=[],
                optional_modules=[],
                milestones=[]
            ),
            learning_activities=[],
            time_estimates=TimeEstimates(
                total_learning_hours=10,
                module_breakdown={},
                practice_hours=0,
                review_hours=0
            ),
            learning_outline={
                "topic_name": "Test",
                "learning_modules": [],
                "module_sequence": {
                    "linear_path": ["module1", "module2"],
                    "parallel_paths": [],
                    "optional_modules": [],
                    "milestones": []
                },
                "learning_activities": [],
                "time_estimates": {
                    "total_learning_hours": 10,
                    "module_breakdown": {},
                    "practice_hours": 0,
                    "review_hours": 0
                }
            }
        )
        
        return mock_vital, mock_pattern, mock_outline
    
    @pytest.fixture
    def pipeline(self, mock_extractors):
        """Create a pipeline with mocked extractors."""
        with patch.object(ExtractionPipeline, '__init__', return_value=None):
            pipeline = ExtractionPipeline.__new__(ExtractionPipeline)
            pipeline.vital_extractor = mock_extractors[0]
            pipeline.pattern_generator = mock_extractors[1]
            pipeline.outline_generator = mock_extractors[2]
        return pipeline
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.vital_extractor is not None
        assert pipeline.pattern_generator is not None
        assert pipeline.outline_generator is not None
    
    def test_run_extraction(self, pipeline):
        """Test running the extraction pipeline."""
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1", "Point 2"]
        }
        
        result = pipeline.run_extraction(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        assert isinstance(result, ExtractionPipelineResult)
        assert result.topic_name == "Test Topic"
        assert isinstance(result.content_summary, dict)
        assert isinstance(result.vital_concepts, list)
        assert isinstance(result.pattern_extraction, dict)
        assert isinstance(result.learning_outline, dict)
        assert result.extraction_timestamp is not None
    
    def test_save_results(self, pipeline, tmp_path):
        """Test saving extraction results."""
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1"]
        }
        
        result = pipeline.run_extraction(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        saved_files = pipeline.save_results(result, str(tmp_path))
        
        assert "result" in saved_files
        assert "vital_concepts" in saved_files
        assert "patterns" in saved_files
        assert "outline" in saved_files
        
        # Verify files exist
        for file_path in saved_files.values():
            assert Path(file_path).exists()
    
    def test_load_extraction_result(self, pipeline, tmp_path):
        """Test loading extraction results from file."""
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1"]
        }
        
        result = pipeline.run_extraction(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        # Save result
        saved_files = pipeline.save_results(result, str(tmp_path))
        result_path = saved_files["result"]
        
        # Load result
        loaded_result = pipeline.load_extraction_result(result_path)
        
        assert loaded_result.topic_name == result.topic_name
        assert loaded_result.content_summary == result.content_summary
        assert loaded_result.vital_concepts == result.vital_concepts


class TestExtractionOrchestrator:
    """Tests for ExtractionOrchestrator class."""
    
    @pytest.fixture
    def mock_extractors(self):
        """Create mock extractors for orchestrator testing."""
        mock_vital = Mock()
        mock_vital.extract_vital_concepts.return_value = {
            "vital_concepts": ["Concept1", "Concept2"],
            "concept_relationships": [],
            "learning_priority": {"phase_1_foundation": [], "phase_2_core": [], "phase_3_advanced": []}
        }
        
        mock_pattern = Mock()
        mock_pattern.extract_patterns.return_value = {
            "learning_patterns": [],
            "compression_opportunities": [],
            "frequency_patterns": {},
            "encoding_strategies": []
        }
        
        mock_outline = Mock()
        mock_outline.extract_outline.return_value = {
            "learning_modules": [],
            "module_sequence": {
                "linear_path": [],
                "parallel_paths": [],
                "optional_modules": [],
                "milestones": []
            },
            "learning_activities": [],
            "time_estimates": {
                "total_learning_hours": 0,
                "module_breakdown": {},
                "practice_hours": 0,
                "review_hours": 0
            }
        }
        
        return mock_vital, mock_pattern, mock_outline
    
    @pytest.fixture
    def orchestrator(self, mock_extractors):
        """Create an ExtractionOrchestrator instance with mocked extractors."""
        with patch.object(ExtractionOrchestrator, '__init__', return_value=None):
            orchestrator = ExtractionOrchestrator.__new__(ExtractionOrchestrator)
            orchestrator.vital_extractor = mock_extractors[0]
            orchestrator.pattern_generator = mock_extractors[1]
            orchestrator.outline_generator = mock_extractors[2]
            orchestrator.api_key = "test_key"
            orchestrator.model = "gpt-4o"
            orchestrator.temperature = 0.5
            orchestrator.config_path = None
        return orchestrator
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.model == "gpt-4o"
        assert orchestrator.temperature == 0.5
    
    def test_run_extraction(self, orchestrator):
        """Test running extraction through orchestrator."""
        content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1"]
        }
        
        result = orchestrator.run_extraction(
            topic_name="Test Topic",
            content_summary=content_summary
        )
        
        assert isinstance(result, ExtractionResult)
        assert result.topic_name == "Test Topic"
        assert isinstance(result.content_summary, dict)
        assert isinstance(result.vital_concepts, list)
        assert isinstance(result.pattern_extraction, dict)
        assert isinstance(result.learning_outline, dict)


class TestSummaryGenerator:
    """Tests for SummaryGenerator class."""
    
    @pytest.fixture
    def mock_extraction_result(self):
        """Create a mock ExtractionResult for testing."""
        return Mock(spec=ExtractionResult)
    
    @pytest.fixture
    def generator(self, mock_extraction_result):
        """Create a SummaryGenerator instance."""
        return SummaryGenerator(result=mock_extraction_result)
    
    def test_initialization(self, generator, mock_extraction_result):
        """Test generator initialization."""
        assert generator.result == mock_extraction_result
    
    def test_generate_markdown_summary(self, generator, mock_extraction_result):
        """Test generating a markdown summary."""
        mock_extraction_result.topic_name = "Test Topic"
        mock_extraction_result.extraction_timestamp = "2024-01-01"
        mock_extraction_result.content_summary = {
            "summary_text": "Test summary",
            "key_points": ["Point 1", "Point 2"]
        }
        mock_extraction_result.vital_concepts = ["Concept1", "Concept2"]
        mock_extraction_result.pattern_extraction = {
            "compression_opportunities": [],
            "abstraction_patterns": [],
            "mental_models": []
        }
        mock_extraction_result.learning_outline = {
            "learning_modules": []
        }
        
        summary = generator.generate_markdown_summary()
        
        assert isinstance(summary, str)
        assert "Test Topic" in summary
        assert "Test summary" in summary
        assert "Point 1" in summary


class TestIntegration:
    """Integration tests for the extraction pipeline."""
    
    @pytest.fixture
    def sample_content_summary(self):
        """Create a sample content summary."""
        return {
            "summary_text": "This is a comprehensive guide to learning Python programming. "
                           "It covers fundamental concepts like variables, data types, "
                           "control structures, functions, and object-oriented programming. "
                           "The guide emphasizes practical exercises and real-world projects.",
            "key_points": [
                "Variables and data types are fundamental to Python programming",
                "Control structures (if statements, loops) are essential for logic",
                "Functions promote code reusability and modularity",
                "Object-oriented programming enables complex system design",
                "Practice through projects is crucial for mastery"
            ]
        }
    
    @pytest.fixture
    def sample_source_summaries(self):
        """Create sample source summaries."""
        return [
            {
                "title": "Python Basics",
                "key_points": [
                    "Python is a versatile programming language",
                    "Variables store data values",
                    "Loops repeat code blocks"
                ]
            },
            {
                "title": "Advanced Python",
                "key_points": [
                    "Object-oriented programming is powerful",
                    "Functions can be passed as arguments",
                    "Error handling is important"
                ]
            }
        ]
    
    def test_complete_extraction_pipeline(self, sample_content_summary, sample_source_summaries):
        """Test the complete extraction pipeline with sample data."""
        with patch('extraction.eighty_twenty.vital_extractor.OpenAI') as mock_vital, \
             patch('extraction.patterns.learning_patterns.OpenAI') as mock_pattern, \
             patch('extraction.outline.outline_generator.OpenAI') as mock_outline:
            
            # Setup mocks
            for mock in [mock_vital, mock_pattern, mock_outline]:
                mock.return_value = Mock()
                mock.return_value.chat.completions.create.return_value = Mock(
                    choices=[Mock(message=Mock(content='{}'))]
                )
            
            # Create pipeline
            pipeline = ExtractionPipeline(
                api_key="test_key",
                model="gpt-4o",
                temperature=0.5
            )
            
            # Run extraction
            result = pipeline.run_extraction(
                topic_name="Python Programming",
                content_summary=sample_content_summary,
                source_summaries=sample_source_summaries
            )
            
            # Verify result structure
            assert result.topic_name == "Python Programming"
            assert isinstance(result.content_summary, dict)
            assert isinstance(result.vital_concepts, list)
            assert isinstance(result.pattern_extraction, dict)
            assert isinstance(result.learning_outline, dict)
            assert result.extraction_timestamp is not None
    
    def test_summary_generation(self, sample_content_summary):
        """Test summary generation with sample data."""
        mock_result = Mock(spec=ExtractionResult)
        mock_result.topic_name = "Python Programming"
        mock_result.extraction_timestamp = "2024-01-01"
        mock_result.content_summary = sample_content_summary
        mock_result.vital_concepts = ["Python", "Programming"]
        mock_result.pattern_extraction = {
            "compression_opportunities": [],
            "abstraction_patterns": [],
            "mental_models": []
        }
        mock_result.learning_outline = {
            "learning_modules": []
        }
        
        generator = SummaryGenerator(result=mock_result)
        
        summary = generator.generate_markdown_summary()
        
        # Verify summary structure
        assert "Python Programming" in summary
        assert "This is a comprehensive guide" in summary
        assert "Variables and data types" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])