"""Tests for SEO Analyzer module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from youtube_studio.seo_analyzer import SEOAnalyzer
import pytest


@pytest.fixture
def analyzer():
    return SEOAnalyzer()


class TestSEOAnalyzerTitleAnalysis:
    """Tests for title analysis."""

    def test_empty_title(self, analyzer):
        result = analyzer.analyze_title("")
        assert result['score'] == 0
        assert 'Title is empty' in result['issues'][0]

    def test_short_title(self, analyzer):
        result = analyzer.analyze_title("Hi")
        assert result['score'] < 50
        assert any('too short' in issue.lower() for issue in result['issues'])

    def test_optimal_length_title(self, analyzer):
        result = analyzer.analyze_title("How to Make Perfect Pasta in 10 Minutes")
        assert result['score'] >= 70
        assert result['length'] == len("How to Make Perfect Pasta in 10 Minutes")

    def test_title_with_keywords(self, analyzer):
        result = analyzer.analyze_title("Best Python Tutorial for Beginners 2024")
        assert result['score'] >= 60
        assert 'Python' in result['keywords_found']

    def test_title_with_special_characters(self, analyzer):
        result = analyzer.analyze_title("Top 10! Tips & Tricks (2024)")
        assert result['score'] >= 50
        assert result['length'] == len("Top 10! Tips & Tricks (2024)")

    def test_title_case_analysis(self, analyzer):
        result = analyzer.analyze_title("ALL CAPS TITLE")
        assert 'caps' in result['issues'][0].lower() or 'uppercase' in result['issues'][0].lower()

    def test_title_with_numbers(self, analyzer):
        result = analyzer.analyze_title("5 Easy Steps to Learn Python")
        assert result['score'] >= 60
        assert '5' in result['keywords_found'] or '5' in result['title']


class TestSEOAnalyzerDescriptionAnalysis:
    """Tests for description analysis."""

    def test_empty_description(self, analyzer):
        result = analyzer.analyze_description("")
        assert result['score'] == 0
        assert 'Description is empty' in result['issues'][0]

    def test_short_description(self, analyzer):
        result = analyzer.analyze_description("Short")
        assert result['score'] < 50
        assert any('too short' in issue.lower() for issue in result['issues'])

    def test_optimal_length_description(self, analyzer):
        desc = "This is a comprehensive guide that covers everything you need to know about the topic. " * 5
        result = analyzer.analyze_description(desc)
        assert result['score'] >= 60
        assert result['length'] >= 100

    def test_description_with_keywords(self, analyzer):
        desc = "Learn Python programming with this tutorial. Python is a great language for beginners."
        result = analyzer.analyze_description(desc)
        assert 'Python' in result['keywords_found']

    def test_description_with_links(self, analyzer):
        desc = "Check out our website: https://example.com and follow us on Twitter @example"
        result = analyzer.analyze_description(desc)
        assert len(result['links']) >= 1

    def test_description_with_hashtags(self, analyzer):
        desc = "Learn Python #python #programming #tutorial #coding"
        result = analyzer.analyze_description(desc)
        assert len(result['hashtags']) >= 1

    def test_description_with_timestamps(self, analyzer):
        desc = "00:00 Intro\n01:30 Main Content\n10:00 Conclusion"
        result = analyzer.analyze_description(desc)
        assert len(result['timestamps']) >= 1


class TestSEOAnalyzerKeywordAnalysis:
    """Tests for keyword analysis."""

    def test_empty_keywords(self, analyzer):
        result = analyzer.analyze_keywords([])
        assert result['score'] == 0
        assert 'No keywords provided' in result['issues'][0]

    def test_single_keyword(self, analyzer):
        result = analyzer.analyze_keywords(['python'])
        assert result['score'] >= 50
        assert 'python' in result['keywords']

    def test_multiple_keywords(self, analyzer):
        result = analyzer.analyze_keywords(['python', 'tutorial', 'beginner', '2024'])
        assert result['score'] >= 60
        assert len(result['keywords']) == 4

    def test_duplicate_keywords(self, analyzer):
        result = analyzer.analyze_keywords(['python', 'python', 'python'])
        assert len(result['keywords']) == 1
        assert 'duplicate' in result['issues'][0].lower()

    def test_keyword_too_long(self, analyzer):
        result = analyzer.analyze_keywords(['this is a very long keyword that exceeds the limit'])
        assert any('too long' in issue.lower() for issue in result['issues'])

    def test_keyword_with_special_characters(self, analyzer):
        result = analyzer.analyze_keywords(['python@#$'])
        assert 'python' in result['keywords'] or len(result['keywords']) == 0


class TestSEOAnalyzerOptimizeTitle:
    """Tests for title optimization."""

    def test_optimize_short_title(self, analyzer):
        result = analyzer.optimize_title("Hi", ['python'])
        assert len(result) > 0
        assert 'Hi' in result or len(result) > 2

    def test_optimize_title_with_keywords(self, analyzer):
        result = analyzer.optimize_title("Python", ['python', 'tutorial'])
        assert 'Python' in result

    def test_optimize_title_adds_keywords(self, analyzer):
        result = analyzer.optimize_title("Learn", ['python', 'programming'])
        assert 'Learn' in result
        assert len(result) > len("Learn")

    def test_optimize_title_already_optimal(self, analyzer):
        result = analyzer.optimize_title("How to Make Perfect Pasta in 10 Minutes", ['pasta', 'cooking'])
        assert 'Pasta' in result or 'pasta' in result


class TestSEOAnalyzerOptimizeDescription:
    """Tests for description optimization."""

    def test_optimize_short_description(self, analyzer):
        result = analyzer.optimize_description("Short", ['python'])
        assert len(result) > 0

    def test_optimize_description_with_keywords(self, analyzer):
        result = analyzer.optimize_description("Learn Python", ['python', 'tutorial'])
        assert 'Python' in result

    def test_optimize_description_adds_content(self, analyzer):
        result = analyzer.optimize_description("Intro", ['python', 'beginner'])
        assert 'Intro' in result
        assert len(result) > len("Intro")


class TestSEOAnalyzerGetSeoScore:
    """Tests for overall SEO score calculation."""

    def test_empty_inputs(self, analyzer):
        result = analyzer.get_seo_score("", "", [])
        assert result['score'] == 0
        assert result['title_score'] == 0
        assert result['description_score'] == 0
        assert result['keywords_score'] == 0

    def test_optimal_inputs(self, analyzer):
        title = "How to Make Perfect Pasta in 10 Minutes"
        desc = "This comprehensive guide covers everything you need to know about making perfect pasta. " * 3
        keywords = ['pasta', 'cooking', 'recipe', 'easy']
        result = analyzer.get_seo_score(title, desc, keywords)
        assert result['score'] >= 60
        assert result['title_score'] >= 50
        assert result['description_score'] >= 50
        assert result['keywords_score'] >= 50

    def test_score_components(self, analyzer):
        title = "Test Title"
        desc = "Test description"
        keywords = ['test']
        result = analyzer.get_seo_score(title, desc, keywords)
        assert 'title_score' in result
        assert 'description_score' in result
        assert 'keywords_score' in result
        assert 'overall_score' in result
        assert 'recommendations' in result
        assert 'title_analysis' in result
        assert 'description_analysis' in result
        assert 'keywords_analysis' in result

    def test_score_range(self, analyzer):
        title = "Test"
        desc = "Test"
        keywords = ['test']
        result = analyzer.get_seo_score(title, desc, keywords)
        assert 0 <= result['score'] <= 100


class TestSEOAnalyzerIntegration:
    """Integration tests for SEO Analyzer."""

    def test_full_workflow(self, analyzer):
        title = "How to Make Perfect Pasta in 10 Minutes"
        desc = "This comprehensive guide covers everything you need to know about making perfect pasta. " * 3
        keywords = ['pasta', 'cooking', 'recipe', 'easy']
        
        # Analyze each component
        title_analysis = analyzer.analyze_title(title)
        desc_analysis = analyzer.analyze_description(desc)
        keywords_analysis = analyzer.analyze_keywords(keywords)
        
        # Get overall score
        score = analyzer.get_seo_score(title, desc, keywords)
        
        # Optimize
        optimized_title = analyzer.optimize_title(title, keywords)
        optimized_desc = analyzer.optimize_description(desc, keywords)
        
        # Verify all operations completed
        assert title_analysis['score'] >= 0
        assert desc_analysis['score'] >= 0
        assert keywords_analysis['score'] >= 0
        assert score['score'] >= 0
        assert len(optimized_title) > 0
        assert len(optimized_desc) > 0

    def test_keyword_suggestions(self, analyzer):
        title = "How to Make Perfect Pasta"
        desc = "Learn to cook pasta like a pro"
        suggestions = analyzer.generate_keyword_suggestions(title, desc)
        assert len(suggestions) > 0
        assert isinstance(suggestions, list)
        assert all(isinstance(kw, str) for kw in suggestions)
