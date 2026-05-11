"""YouTube Studio orchestrator.

This module provides the main orchestration functionality for YouTube Studio,
coordinating video metadata generation, SEO analysis, and keyword optimization.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from .keyword_generator import KeywordGenerator
from .seo_analyzer import SEOAnalyzer
from .template_engine import TemplateEngine, TemplateManager
from .config import YouTubeStudioConfig


class YouTubeStudioOrchestrator:
    """Main orchestrator for YouTube Studio operations."""
    
    def __init__(self, config: Optional[YouTubeStudioConfig] = None):
        """Initialize YouTube Studio orchestrator.
        
        Args:
            config: YouTube Studio configuration
        """
        self.config = config or YouTubeStudioConfig()
        self.keyword_generator = KeywordGenerator()
        self.seo_analyzer = SEOAnalyzer()
        self.template_engine = TemplateEngine()
        self.template_manager = TemplateManager()
        self.history = []  # Track operations history
    
    def generate_video_metadata(self, video_data: Dict[str, str]) -> Dict[str, Any]:
        """Generate complete video metadata.
        
        Args:
            video_data: Dictionary with video information
                Required keys: 'title', 'description'
                Optional keys: 'keywords', 'category', 'language'
            
        Returns:
            Dictionary with generated metadata
        """
        # Extract video data
        title = video_data.get('title', '')
        description = video_data.get('description', '')
        keywords = video_data.get('keywords', [])
        category = video_data.get('category', self.config.default_video_category)
        language = video_data.get('language', self.config.default_video_language)
        
        # Generate keywords if needed
        if self.config.auto_generate_keywords and not keywords:
            keywords = self.keyword_generator.generate_keywords(title, description)
        
        # Optimize title if needed
        if self.config.auto_optimize_titles:
            title = self.seo_analyzer.optimize_title(title, keywords)
        
        # Optimize description if needed
        if self.config.auto_generate_descriptions:
            description = self.seo_analyzer.optimize_description(description, keywords)
        
        # Generate thumbnail info
        thumbnail_info = self._generate_thumbnail_info(video_data)
        
        # Compile metadata
        metadata = {
            'title': title,
            'description': description,
            'keywords': keywords,
            'category': category,
            'language': language,
            'thumbnail': thumbnail_info,
            'seo_score': self.seo_analyzer.get_seo_score(title, description, keywords),
            'generated_at': datetime.now().isoformat(),
            'video_id': self._generate_video_id()
        }
        
        # Add to history
        self.history.append({
            'operation': 'generate_metadata',
            'timestamp': datetime.now().isoformat(),
            'input': video_data,
            'output': metadata
        })
        
        return metadata
    
    def analyze_seo(self, title: str, description: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyze SEO for video metadata.
        
        Args:
            title: Video title
            description: Video description
            keywords: List of keywords
            
        Returns:
            Dictionary with SEO analysis results
        """
        analysis = self.seo_analyzer.get_seo_score(title, description, keywords)
        
        # Add to history
        self.history.append({
            'operation': 'analyze_seo',
            'timestamp': datetime.now().isoformat(),
            'input': {
                'title': title,
                'description': description,
                'keywords': keywords
            },
            'output': analysis
        })
        
        return analysis
    
    def generate_keywords(self, title: str, description: str, count: int = 10) -> List[str]:
        """Generate keywords for a video.
        
        Args:
            title: Video title
            description: Video description
            count: Number of keywords to generate
            
        Returns:
            List of generated keywords
        """
        keywords = self.keyword_generator.generate_keywords(title, description, count)
        
        # Add to history
        self.history.append({
            'operation': 'generate_keywords',
            'timestamp': datetime.now().isoformat(),
            'input': {
                'title': title,
                'description': description,
                'count': count
            },
            'output': keywords
        })
        
        return keywords
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Optional[str]:
        """Render a template with variables.
        
        Args:
            template_name: Name of the template to render
            variables: Dictionary of variable values
            
        Returns:
            Rendered template string or None if template not found
        """
        rendered = self.template_manager.render_template(template_name, variables)
        
        # Add to history
        self.history.append({
            'operation': 'render_template',
            'timestamp': datetime.now().isoformat(),
            'input': {
                'template_name': template_name,
                'variables': variables
            },
            'output': rendered
        })
        
        return rendered
    
    def save_template(self, name: str, template: Dict[str, str]) -> bool:
        """Save a template.
        
        Args:
            name: Name of the template
            template: Template dictionary
            
        Returns:
            True if successful, False otherwise
        """
        success = self.template_manager.save_template(name, template)
        
        # Add to history
        self.history.append({
            'operation': 'save_template',
            'timestamp': datetime.now().isoformat(),
            'input': {
                'name': name,
                'template': template
            },
            'output': {'success': success}
        })
        
        return success
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get operation history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of history entries
        """
        return self.history[-limit:]
    
    def clear_history(self) -> None:
        """Clear operation history."""
        self.history = []
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration.
        
        Returns:
            Dictionary with configuration data
        """
        return self.config.to_dict()
    
    def import_config(self, config_data: Dict[str, Any]) -> None:
        """Import configuration.
        
        Args:
            config_data: Dictionary with configuration data
        """
        self.config = YouTubeStudioConfig.from_dict(config_data)
    
    def _generate_thumbnail_info(self, video_data: Dict[str, str]) -> Dict[str, str]:
        """Generate thumbnail information.
        
        Args:
            video_data: Dictionary with video information
            
        Returns:
            Dictionary with thumbnail information
        """
        title = video_data.get('title', '')
        description = video_data.get('description', '')
        
        # Generate thumbnail style based on content
        if 'tutorial' in title.lower() or 'how to' in title.lower():
            style = 'educational'
        elif 'review' in title.lower() or 'unboxing' in title.lower():
            style = 'product'
        else:
            style = self.config.thumbnail_style
        
        # Generate color scheme based on content
        if 'nature' in title.lower() or 'outdoor' in title.lower():
            color_scheme = 'green'
        elif 'tech' in title.lower() or 'computer' in title.lower():
            color_scheme = 'blue'
        else:
            color_scheme = self.config.thumbnail_color_scheme
        
        return {
            'style': style,
            'color_scheme': color_scheme,
            'size': self.config.thumbnail_size,
            'text_overlay': title[:30] if title else '',
            'background_color': self._get_color_hex(color_scheme)
        }
    
    def _get_color_hex(self, color_name: str) -> str:
        """Get hex color code for a color name.
        
        Args:
            color_name: Name of the color
            
        Returns:
            Hex color code
        """
        colors = {
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'orange': '#FFA500',
            'purple': '#800080',
            'pink': '#FFC0CB',
            'black': '#000000',
            'white': '#FFFFFF',
            'gray': '#808080',
            'brown': '#A52A2A',
            'teal': '#008080',
            'navy': '#000080',
            'maroon': '#800000',
        }
        return colors.get(color_name.lower(), '#FFFFFF')
    
    def _generate_video_id(self) -> str:
        """Generate a unique video ID.
        
        Returns:
            Unique video ID string
        """
        import uuid
        return str(uuid.uuid4())[:8]