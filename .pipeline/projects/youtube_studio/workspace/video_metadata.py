"""
Video Metadata Module

This module provides the VideoMetadata class for managing video metadata
including title, description, tags, thumbnail, and other video information.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VideoMetadata:
    """
    Represents video metadata for YouTube uploads.
    
    This class manages all metadata associated with a YouTube video,
    including title, description, tags, thumbnail, and custom fields.
    """
    
    # Basic metadata
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    category_id: str = "22"  # People & Blogs
    privacy_status: str = "private"
    license: str = "youtube"
    embeddable: bool = True
    public_stats_viewable: bool = True
    
    # Thumbnail
    thumbnail_url: str = ""
    thumbnail_file: str = ""
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    
    def update(self, **kwargs) -> None:
        """
        Update video metadata with new values.
        
        Args:
            **kwargs: Key-value pairs of metadata to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert video metadata to a dictionary.
        
        Returns:
            Dictionary representation of the metadata
        """
        return {
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'category_id': self.category_id,
            'privacy_status': self.privacy_status,
            'license': self.license,
            'embeddable': self.embeddable,
            'public_stats_viewable': self.public_stats_viewable,
            'thumbnail_url': self.thumbnail_url,
            'thumbnail_file': self.thumbnail_file,
            'custom_fields': self.custom_fields,
            'metadata': {
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'version': self.version
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoMetadata':
        """
        Create a VideoMetadata object from a dictionary.
        
        Args:
            data: Dictionary representation of the metadata
            
        Returns:
            VideoMetadata instance
        """
        metadata = data.get('metadata', {})
        
        return cls(
            title=data.get('title', ''),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            category_id=data.get('category_id', '22'),
            privacy_status=data.get('privacy_status', 'private'),
            license=data.get('license', 'youtube'),
            embeddable=data.get('embeddable', True),
            public_stats_viewable=data.get('public_stats_viewable', True),
            thumbnail_url=data.get('thumbnail_url', ''),
            thumbnail_file=data.get('thumbnail_file', ''),
            custom_fields=data.get('custom_fields', {}),
            created_at=metadata.get('created_at', datetime.now().isoformat()),
            updated_at=metadata.get('updated_at', datetime.now().isoformat()),
            version=metadata.get('version', '1.0')
        )
    
    def validate(self) -> List[str]:
        """
        Validate the video metadata.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate title
        if not self.title:
            errors.append("Title is required")
        elif len(self.title) > 100:
            errors.append("Title must be 100 characters or less")
        
        # Validate description
        if len(self.description) > 5000:
            errors.append("Description must be 5000 characters or less")
        
        # Validate tags
        if len(self.tags) > 500:
            errors.append("Too many tags (max 500)")
        
        for tag in self.tags:
            if len(tag) > 500:
                errors.append(f"Tag '{tag}' must be 500 characters or less")
        
        # Validate privacy status
        if self.privacy_status not in ['private', 'public', 'unlisted']:
            errors.append("Invalid privacy status")
        
        # Validate license
        if self.license not in ['youtube', 'creativeCommon']:
            errors.append("Invalid license")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the video metadata.
        
        Returns:
            Dictionary with summary information
        """
        return {
            'title': self.title,
            'description_length': len(self.description),
            'tag_count': len(self.tags),
            'category_id': self.category_id,
            'privacy_status': self.privacy_status,
            'thumbnail_url': self.thumbnail_url,
            'custom_field_count': len(self.custom_fields)
        }