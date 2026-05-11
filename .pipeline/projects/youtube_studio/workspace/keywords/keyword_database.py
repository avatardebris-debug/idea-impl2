"""
Keyword Database Module

This module provides the KeywordDatabase class for managing keyword databases,
including local keyword storage and API interfaces for external keyword services.
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import os


@dataclass
class KeywordEntry:
    """A single keyword entry in the database"""
    keyword: str
    category: str
    search_volume: int
    competition: str  # 'low', 'medium', 'high'
    relevance_score: float
    created_at: str


class KeywordDatabase:
    """
    Local keyword database for YouTube SEO optimization.
    
    This class provides functionality for storing, retrieving, and searching
    keywords, as well as interfacing with external keyword APIs.
    """
    
    # Default database file
    DEFAULT_DB_PATH = 'keyword_database.json'
    
    # Sample keywords for initialization
    SAMPLE_KEYWORDS = [
        KeywordEntry(keyword='tutorial', category='education', search_volume=1000000,
                    competition='high', relevance_score=1.0,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='how to', category='education', search_volume=5000000,
                    competition='high', relevance_score=1.0,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='review', category='entertainment', search_volume=2000000,
                    competition='high', relevance_score=0.9,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='tips', category='lifestyle', search_volume=800000,
                    competition='medium', relevance_score=0.85,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='guide', category='education', search_volume=1500000,
                    competition='medium', relevance_score=0.85,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='best', category='entertainment', search_volume=3000000,
                    competition='high', relevance_score=0.8,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='viral', category='entertainment', search_volume=500000,
                    competition='medium', relevance_score=0.75,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='trending', category='entertainment', search_volume=600000,
                    competition='medium', relevance_score=0.75,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='technology', category='technology', search_volume=1200000,
                    competition='high', relevance_score=0.9,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='lifestyle', category='lifestyle', search_volume=900000,
                    competition='medium', relevance_score=0.85,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='beginner', category='education', search_volume=700000,
                    competition='low', relevance_score=0.7,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='advanced', category='education', search_volume=500000,
                    competition='low', relevance_score=0.7,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='2024', category='news', search_volume=2000000,
                    competition='high', relevance_score=0.8,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='new', category='news', search_volume=1800000,
                    competition='high', relevance_score=0.75,
                    created_at=datetime.now().isoformat()),
        KeywordEntry(keyword='latest', category='news', search_volume=1000000,
                    competition='medium', relevance_score=0.75,
                    created_at=datetime.now().isoformat()),
    ]
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the keyword database.
        
        Args:
            db_path: Optional path to the database file
        """
        self.db_path = db_path or os.path.join(os.getcwd(), self.DEFAULT_DB_PATH)
        self._keywords: Dict[str, KeywordEntry] = {}
        self._load_database()
    
    def _load_database(self):
        """Load the database from file"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                
                for item in data:
                    entry = KeywordEntry(
                        keyword=item['keyword'],
                        category=item['category'],
                        search_volume=item['search_volume'],
                        competition=item['competition'],
                        relevance_score=item['relevance_score'],
                        created_at=item['created_at']
                    )
                    self._keywords[entry.keyword] = entry
            except (json.JSONDecodeError, KeyError):
                # If loading fails, start with sample keywords
                self._initialize_sample_data()
        else:
            # Initialize with sample data
            self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample keywords"""
        for entry in self.SAMPLE_KEYWORDS:
            self._keywords[entry.keyword] = entry
        self._save_database()
    
    def _save_database(self):
        """Save the database to file"""
        data = [
            {
                'keyword': entry.keyword,
                'category': entry.category,
                'search_volume': entry.search_volume,
                'competition': entry.competition,
                'relevance_score': entry.relevance_score,
                'created_at': entry.created_at
            }
            for entry in self._keywords.values()
        ]
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_keyword(self, keyword: str, category: str, search_volume: int,
                   competition: str, relevance_score: float) -> bool:
        """
        Add a keyword to the database.
        
        Args:
            keyword: The keyword to add
            category: Category of the keyword
            search_volume: Estimated monthly search volume
            competition: Competition level ('low', 'medium', 'high')
            relevance_score: Relevance score (0.0 to 1.0)
            
        Returns:
            True if added successfully, False if already exists
        """
        if keyword in self._keywords:
            return False
        
        entry = KeywordEntry(
            keyword=keyword,
            category=category,
            search_volume=search_volume,
            competition=competition,
            relevance_score=relevance_score,
            created_at=datetime.now().isoformat()
        )
        
        self._keywords[keyword] = entry
        self._save_database()
        return True
    
    def remove_keyword(self, keyword: str) -> bool:
        """
        Remove a keyword from the database.
        
        Args:
            keyword: The keyword to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if keyword not in self._keywords:
            return False
        
        del self._keywords[keyword]
        self._save_database()
        return True
    
    def get_keyword(self, keyword: str) -> Optional[KeywordEntry]:
        """
        Get a keyword entry by keyword.
        
        Args:
            keyword: The keyword to look up
            
        Returns:
            KeywordEntry if found, None otherwise
        """
        return self._keywords.get(keyword)
    
    def search_keywords(self, query: str, category: Optional[str] = None,
                       max_results: int = 50) -> List[KeywordEntry]:
        """
        Search for keywords matching a query.
        
        Args:
            query: Search query
            category: Optional category filter
            max_results: Maximum number of results
            
        Returns:
            List of matching KeywordEntry objects
        """
        query_lower = query.lower()
        results = []
        
        for keyword, entry in self._keywords.items():
            # Check category filter
            if category and entry.category != category:
                continue
            
            # Check if keyword matches query
            if query_lower in keyword.lower() or keyword.lower() in query_lower:
                results.append(entry)
        
        # Sort by relevance score descending
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:max_results]
    
    def get_keywords_by_category(self, category: str) -> List[KeywordEntry]:
        """
        Get all keywords in a category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of KeywordEntry objects in the category
        """
        return [
            entry for entry in self._keywords.values()
            if entry.category == category
        ]
    
    def get_top_keywords(self, category: Optional[str] = None,
                        max_results: int = 20) -> List[KeywordEntry]:
        """
        Get top keywords by search volume.
        
        Args:
            category: Optional category filter
            max_results: Maximum number of results
            
        Returns:
            List of top KeywordEntry objects
        """
        keywords = list(self._keywords.values())
        
        if category:
            keywords = [k for k in keywords if k.category == category]
        
        # Sort by search volume descending
        keywords.sort(key=lambda x: x.search_volume, reverse=True)
        
        return keywords[:max_results]
    
    def get_all_categories(self) -> List[str]:
        """
        Get all unique categories in the database.
        
        Returns:
            List of unique category names
        """
        return list(set(entry.category for entry in self._keywords.values()))
    
    def get_keyword_stats(self) -> Dict[str, int]:
        """
        Get statistics about the keyword database.
        
        Returns:
            Dictionary with database statistics
        """
        total_keywords = len(self._keywords)
        
        if total_keywords == 0:
            return {
                'total_keywords': 0,
                'total_categories': 0,
                'avg_search_volume': 0,
                'avg_relevance_score': 0.0,
                'categories': {}
            }
        
        total_search_volume = sum(entry.search_volume for entry in self._keywords.values())
        total_relevance = sum(entry.relevance_score for entry in self._keywords.values())
        
        # Count by category
        categories = {}
        for entry in self._keywords.values():
            categories[entry.category] = categories.get(entry.category, 0) + 1
        
        return {
            'total_keywords': total_keywords,
            'total_categories': len(categories),
            'avg_search_volume': total_search_volume // total_keywords,
            'avg_relevance_score': total_relevance / total_keywords,
            'categories': categories
        }
    
    def export_to_json(self, output_path: str) -> bool:
        """
        Export the database to a JSON file.
        
        Args:
            output_path: Path to save the JSON file
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            data = [
                {
                    'keyword': entry.keyword,
                    'category': entry.category,
                    'search_volume': entry.search_volume,
                    'competition': entry.competition,
                    'relevance_score': entry.relevance_score,
                    'created_at': entry.created_at
                }
                for entry in self._keywords.values()
            ]
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def import_from_json(self, input_path: str) -> bool:
        """
        Import keywords from a JSON file.
        
        Args:
            input_path: Path to the JSON file
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            for item in data:
                entry = KeywordEntry(
                    keyword=item['keyword'],
                    category=item['category'],
                    search_volume=item['search_volume'],
                    competition=item['competition'],
                    relevance_score=item['relevance_score'],
                    created_at=item.get('created_at', datetime.now().isoformat())
                )
                self._keywords[entry.keyword] = entry
            
            self._save_database()
            return True
        except Exception:
            return False
    
    def clear(self):
        """Clear all keywords from the database"""
        self._keywords.clear()
        self._save_database()
    
    def get_keyword_suggestions(self, keyword: str, num_suggestions: int = 10) -> List[str]:
        """
        Get keyword suggestions based on an existing keyword.
        
        Args:
            keyword: Base keyword
            num_suggestions: Number of suggestions to return
            
        Returns:
            List of suggested keywords
        """
        suggestions = []
        keyword_lower = keyword.lower()
        
        # Find similar keywords
        for existing_keyword in self._keywords.keys():
            if existing_keyword != keyword_lower:
                # Check for common words
                common_words = set(keyword_lower.split()) & set(existing_keyword.split())
                if common_words:
                    suggestions.append(existing_keyword)
        
        # Add common prefixes/suffixes
        prefixes = ['best', 'top', 'how to', 'guide', 'tutorial', 'review']
        suffixes = ['tips', 'tricks', '2024', 'for beginners', 'explained']
        
        for prefix in prefixes:
            suggestions.append(f"{prefix} {keyword}")
        
        for suffix in suffixes:
            suggestions.append(f"{keyword} {suffix}")
        
        # Remove duplicates and limit
        suggestions = list(set(suggestions))
        return suggestions[:num_suggestions]
    
    def get_competition_analysis(self, keyword: str) -> Dict[str, int]:
        """
        Get competition analysis for a keyword.
        
        Args:
            keyword: Keyword to analyze
            
        Returns:
            Dictionary with competition analysis
        """
        entry = self.get_keyword(keyword)
        
        if not entry:
            return {
                'keyword': keyword,
                'search_volume': 0,
                'competition': 'unknown',
                'difficulty_score': 0.0,
                'opportunity_score': 0.0
            }
        
        # Calculate difficulty score (0-100)
        competition_scores = {'low': 20, 'medium': 50, 'high': 80}
        difficulty = competition_scores.get(entry.competition, 50)
        
        # Calculate opportunity score (0-100)
        # Higher search volume and lower competition = higher opportunity
        opportunity = (entry.relevance_score * 50) + (50 - difficulty)
        
        return {
            'keyword': keyword,
            'search_volume': entry.search_volume,
            'competition': entry.competition,
            'difficulty_score': difficulty,
            'opportunity_score': round(opportunity, 2)
        }
