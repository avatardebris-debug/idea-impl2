"""Description builder for YouTube Studio.

This module provides functionality for building optimized video descriptions
with sections, links, and metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from .config import get_config


@dataclass
class DescriptionSection:
    """A section of the description.
    
    Attributes:
        title: Section title.
        content: Section content.
        order: Display order.
    """
    title: str
    content: str
    order: int = 0


@dataclass
class DescriptionResult:
    """Result of description building.
    
    Attributes:
        full_description: Complete description text.
        sections: List of description sections.
        word_count: Total word count.
        generated_at: Generation timestamp.
    """
    full_description: str
    sections: List[DescriptionSection] = field(default_factory=list)
    word_count: int = 0
    generated_at: datetime = field(default_factory=datetime.now)


class DescriptionBuilder:
    """Builder for YouTube video descriptions.
    
    This class builds optimized video descriptions with sections,
    links, and metadata following YouTube best practices.
    """
    
    # Description templates
    DESCRIPTION_TEMPLATES = {
        'intro': [
            'In this video, I\'ll show you everything you need to know about {topic}.',
            'Welcome to my guide on {topic}! Here\'s what we\'ll cover:',
            'Today we\'re diving deep into {topic}. Let\'s get started!',
            'If you\'re looking to learn about {topic}, you\'re in the right place.',
        ],
        'chapters': [
            '📑 Chapters:\n0:00 - Introduction\n{chapters}',
            '⏰ Timestamps:\n0:00 - Intro\n{chapters}',
            '📖 Table of Contents:\n0:00 - Overview\n{chapters}',
        ],
        'links': [
            '🔗 Links mentioned:\n{links}',
            '📎 Resources:\n{links}',
            '👉 Useful Links:\n{links}',
        ],
        'cta': [
            '👍 If you found this helpful, please like and subscribe!',
            '💡 Don\'t forget to like, subscribe, and hit the bell icon!',
            '🎯 Love this content? Subscribe for more weekly videos!',
        ],
        'hashtags': [
            '#YouTube #{topic} #{category}',
            '#{topic} #{category} #tutorial',
            '#{topic} #{category} #howto',
        ],
    }
    
    def __init__(self):
        """Initialize description builder."""
        self.config = get_config()
    
    def build_description(self, topic: str, chapters: List[str] = None,
                         links: List[str] = None, hashtags: List[str] = None,
                         category: str = 'education') -> DescriptionResult:
        """Build a complete video description.
        
        Args:
            topic: Main topic of the video.
            chapters: List of chapter titles.
            links: List of links to include.
            hashtags: List of hashtags.
            category: Video category.
            
        Returns:
            DescriptionResult object.
        """
        sections = []
        
        # Add intro section
        intro = self._generate_intro(topic)
        sections.append(DescriptionSection(
            title='Introduction',
            content=intro,
            order=1,
        ))
        
        # Add chapters section if provided
        if chapters:
            chapters_content = '\n'.join([f'{i+1:02d}:{i+1:02d} - {chapter}' 
                                        for i, chapter in enumerate(chapters)])
            chapters_template = self._get_template('chapters')
            chapters_content = chapters_template.format(chapters=chapters_content)
            sections.append(DescriptionSection(
                title='Chapters',
                content=chapters_content,
                order=2,
            ))
        
        # Add links section if provided
        if links:
            links_content = '\n'.join([f'- {link}' for link in links])
            links_template = self._get_template('links')
            links_content = links_template.format(links=links_content)
            sections.append(DescriptionSection(
                title='Links',
                content=links_content,
                order=3,
            ))
        
        # Add CTA section
        cta = self._get_template('cta')
        sections.append(DescriptionSection(
            title='Call to Action',
            content=cta,
            order=4,
        ))
        
        # Add hashtags section
        if hashtags:
            hashtags_content = ' '.join(hashtags)
        else:
            hashtags_content = self._generate_hashtags(topic, category)
        sections.append(DescriptionSection(
            title='Hashtags',
            content=hashtags_content,
            order=5,
        ))
        
        # Sort sections by order
        sections.sort(key=lambda x: x.order)
        
        # Combine all sections
        full_description = '\n\n'.join([section.content for section in sections])
        
        # Calculate word count
        word_count = len(full_description.split())
        
        return DescriptionResult(
            full_description=full_description,
            sections=sections,
            word_count=word_count,
        )
    
    def _generate_intro(self, topic: str) -> str:
        """Generate introduction text.
        
        Args:
            topic: Main topic.
            
        Returns:
            Introduction string.
        """
        templates = self.DESCRIPTION_TEMPLATES['intro']
        import random
        template = random.choice(templates)
        return template.format(topic=topic)
    
    def _get_template(self, section_type: str) -> str:
        """Get a template for a section type.
        
        Args:
            section_type: Type of section.
            
        Returns:
            Template string.
        """
        templates = self.DESCRIPTION_TEMPLATES.get(section_type, [])
        if templates:
            import random
            return random.choice(templates)
        return ''
    
    def _generate_hashtags(self, topic: str, category: str) -> str:
        """Generate hashtags for the video.
        
        Args:
            topic: Main topic.
            category: Video category.
            
        Returns:
            Hashtags string.
        """
        templates = self.DESCRIPTION_TEMPLATES['hashtags']
        import random
        template = random.choice(templates)
        return template.format(topic=topic, category=category)
