"""SEO Analyzer module for YouTube video optimization."""

import re
from collections import Counter
from typing import List, Dict, Any


class SEOAnalyzer:
    """Analyzes and optimizes YouTube video metadata for SEO."""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can',
            'this', 'that', 'these', 'those', 'it', 'its', 'i', 'me',
            'my', 'we', 'our', 'you', 'your', 'he', 'she', 'they', 'them',
            'their', 'his', 'her', 'not', 'no', 'nor', 'so', 'if', 'then',
            'than', 'too', 'very', 'just', 'about', 'above', 'after',
            'again', 'all', 'also', 'am', 'any', 'as', 'because', 'before',
            'below', 'between', 'both', 'each', 'few', 'from', 'further',
            'get', 'got', 'here', 'how', 'into', 'more', 'most', 'much',
            'must', 'myself', 'new', 'now', 'only', 'other', 'out', 'over',
            'own', 'same', 'some', 'such', 'there', 'through', 'under',
            'until', 'up', 'us', 'what', 'when', 'where', 'which', 'while',
            'who', 'whom', 'why', 'down', 'during', 'off', 'once', 'per',
            'since', 'still', 'till', 'up', 'upon', 'used', 'using', 'via',
            'yet', 'yourself', 'yourselves', 'ourselves', 'himself',
            'herself', 'itself', 'themselves', 'myself', 'my', 'mine',
            'myself', 'we', 'us', 'our', 'ours', 'ourselves', 'you',
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
            'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
            'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these',
            'those', 'i', 'me', 'my', 'mine', 'myself', 'we', 'us',
            'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
            'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
            'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
            'this', 'that', 'these', 'those', 'i', 'me', 'my', 'mine',
            'myself', 'we', 'us', 'our', 'ours', 'ourselves', 'you',
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
            'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
            'itself', 'they', 'them', 'their', 'theirs', 'themselves'
        }
    
    def analyze_title(self, title: str) -> Dict[str, Any]:
        """Analyze video title for SEO optimization.
        
        Args:
            title: Video title to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not title:
            return {
                'score': 0,
                'issues': ['Title is empty'],
                'suggestions': ['Add a descriptive title'],
                'length': 0,
                'title': title,
                'keywords_found': [],
                'has_keywords': False,
                'keyword_count': 0,
                'keywords': [],
                'link_count': 0,
                'links': [],
                'hashtag_count': 0,
                'hashtags': [],
                'timestamps': [],
                'has_cta': False
            }
        
        issues = []
        suggestions = []
        
        # Check title length
        length = len(title)
        if length < 10:
            issues.append('Title is too short')
            suggestions.append('Expand title to at least 10 characters')
        elif length > 60:
            issues.append('Title is too long')
            suggestions.append('Shorten title to under 60 characters')
        
        # Penalize very short titles more heavily
        if length < 5:
            issues.append('Title is extremely short')
            suggestions.append('Consider a more descriptive title')
        
        # Check for all caps
        alpha_chars = [c for c in title if c.isalpha()]
        if alpha_chars and all(c.isupper() for c in alpha_chars):
            issues.append('Title is in all caps')
            suggestions.append('Use proper capitalization')
        
        # Extract keywords
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', title)
        filtered_words = [w for w in words if w.lower() not in self.stop_words]
        keywords = list(set(filtered_words))
        
        # Check for special characters
        special_chars = re.findall(r'[^a-zA-Z0-9\s]', title)
        if special_chars:
            suggestions.append('Consider removing special characters')
        
        # Calculate score
        score = 100
        if length < 10:
            score -= 40
        elif length < 20:
            score -= 20
        elif length > 60:
            score -= 20
        
        if alpha_chars and all(c.isupper() for c in alpha_chars):
            score -= 15
        
        score -= len(issues) * 5
        score -= len(suggestions) * 3
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'issues': issues,
            'suggestions': suggestions,
            'length': length,
            'title': title,
            'keywords_found': keywords,
            'has_keywords': len(keywords) > 0,
            'keyword_count': len(keywords),
            'keywords': keywords,
            'link_count': 0,
            'links': [],
            'hashtag_count': 0,
            'hashtags': [],
            'timestamps': [],
            'has_cta': False
        }
    
    def analyze_description(self, description: str) -> Dict[str, Any]:
        """Analyze video description for SEO optimization.
        
        Args:
            description: Video description to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not description:
            return {
                'score': 0,
                'issues': ['Description is empty'],
                'suggestions': ['Add a detailed description'],
                'word_count': 0,
                'char_count': 0,
                'length': 0,
                'has_keywords': False,
                'keyword_count': 0,
                'keywords': [],
                'keywords_found': [],
                'link_count': 0,
                'links': [],
                'hashtag_count': 0,
                'hashtags': [],
                'timestamps': [],
                'has_cta': False
            }
        
        issues = []
        suggestions = []
        
        # Check description length
        char_count = len(description)
        word_count = len(description.split())
        
        if char_count < 100:
            issues.append('Description is too short')
            suggestions.append('Add more details (recommended: 200+ characters)')
        elif char_count < 200:
            suggestions.append('Consider adding more details')
        
        # Extract keywords
        words = re.findall(r'\b[a-zA-Z]{3,}\b', description)
        filtered_words = [w for w in words if w.lower() not in self.stop_words]
        keywords = list(set(filtered_words))
        
        # Extract links
        links = re.findall(r'https?://\S+', description)
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', description)
        
        # Extract timestamps
        timestamps = re.findall(r'(\d{1,2}:\d{2}(?::\d{2})?)', description)
        
        # Check for CTA
        cta_patterns = ['subscribe', 'like', 'comment', 'share', 'click', 'visit']
        has_cta = any(cta in description.lower() for cta in cta_patterns)
        
        # Calculate score
        score = 100
        if char_count < 100:
            score -= 50
        elif char_count < 200:
            score -= 20
        
        if not keywords:
            score -= 10
        
        if not links:
            score -= 5
        
        if not hashtags:
            score -= 5
        
        if not timestamps:
            score -= 5
        
        if not has_cta:
            score -= 5
        
        score -= len(issues) * 10
        score -= len(suggestions) * 5
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'issues': issues,
            'suggestions': suggestions,
            'word_count': word_count,
            'char_count': char_count,
            'length': char_count,
            'has_keywords': len(keywords) > 0,
            'keyword_count': len(keywords),
            'keywords': keywords,
            'keywords_found': keywords,
            'link_count': len(links),
            'links': links,
            'hashtag_count': len(hashtags),
            'hashtags': hashtags,
            'timestamps': timestamps,
            'has_cta': has_cta
        }
    
    def analyze_tags(self, tags: List[str]) -> Dict[str, Any]:
        """Analyze video tags for SEO optimization.
        
        Args:
            tags: List of tags to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not tags:
            return {
                'score': 0,
                'issues': ['No tags provided'],
                'suggestions': ['Add relevant tags'],
                'tag_count': 0,
                'duplicate_count': 0,
                'too_long_count': 0,
                'tags': []
            }
        
        issues = []
        suggestions = []
        
        # Check tag count
        if len(tags) < 3:
            issues.append('Too few tags')
            suggestions.append('Add more tags (recommended: 5-15)')
        elif len(tags) > 500:
            issues.append('Total tag length exceeds 500 characters')
            suggestions.append('Reduce the number or length of tags')
        
        # Check for duplicates
        tag_lower = [t.lower().strip() for t in tags]
        unique_tags = set(tag_lower)
        duplicate_count = len(tags) - len(unique_tags)
        
        if duplicate_count > 0:
            issues.append(f'{duplicate_count} duplicate tags found')
            suggestions.append('Remove duplicate tags')
        
        # Check tag length
        too_long = [t for t in tags if len(t) > 500]
        too_long_count = len(too_long)
        
        if too_long_count > 0:
            issues.append(f'{too_long_count} tags exceed 500 characters')
            suggestions.append('Shorten tags that exceed 500 characters')
        
        # Calculate score
        score = 100
        score -= len(issues) * 10
        score -= len(suggestions) * 5
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'issues': issues,
            'suggestions': suggestions,
            'tag_count': len(tags),
            'unique_tag_count': len(unique_tags),
            'duplicate_count': duplicate_count,
            'too_long_count': too_long_count,
            'tags': tags
        }
    
    def analyze_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """Analyze video keywords for SEO optimization.
        
        Args:
            keywords: List of keywords to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not keywords:
            return {
                'score': 0,
                'issues': ['No keywords provided'],
                'suggestions': ['Add relevant keywords'],
                'keyword_count': 0,
                'duplicate_count': 0,
                'too_long_count': 0,
                'keywords': []
            }
        
        issues = []
        suggestions = []
        
        # Check keyword count
        if len(keywords) < 3:
            issues.append('Too few keywords identified')
            suggestions.append('Add more relevant keywords')
        
        # Check for duplicates and deduplicate
        keyword_lower = [k.lower().strip() for k in keywords]
        unique_keywords = list(dict.fromkeys(keyword_lower))  # Preserve order, remove duplicates
        duplicate_count = len(keywords) - len(unique_keywords)
        
        if duplicate_count > 0:
            issues.append(f'{duplicate_count} duplicate keywords found')
            suggestions.append('Remove duplicate keywords')
        
        # Check keyword length
        too_long = [k for k in keywords if len(k) > 50]
        too_long_count = len(too_long)
        
        if too_long_count > 0:
            issues.append(f'{too_long_count} keywords are too long')
            suggestions.append('Shorten keywords that exceed 50 characters')
        
        # Check for special characters and clean them
        cleaned_keywords = []
        for k in keywords:
            # Remove special characters but keep alphanumeric
            cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', k)
            if cleaned:
                cleaned_keywords.append(cleaned)
        
        # Calculate score
        score = 100
        score -= len(issues) * 10
        score -= len(suggestions) * 5
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'issues': issues,
            'suggestions': suggestions,
            'keyword_count': len(keywords),
            'unique_keyword_count': len(unique_keywords),
            'duplicate_count': duplicate_count,
            'too_long_count': too_long_count,
            'keywords': cleaned_keywords if cleaned_keywords else keywords
        }
    
    def optimize_title(self, title: str, keywords: List[str]) -> str:
        """Optimize video title for SEO.
        
        Args:
            title: Current video title
            keywords: List of target keywords
            
        Returns:
            Optimized title string
        """
        if not title:
            return ' '.join(keywords[:3]) if keywords else ''
        
        optimized_title = title
        
        # Check title length
        if len(title) < 10:
            # Add keywords to make it longer
            for kw in keywords:
                if len(optimized_title) >= 10:
                    break
                if kw.lower() not in optimized_title.lower():
                    optimized_title = f"{optimized_title} {kw}"
        
        # Check for keyword inclusion
        title_lower = optimized_title.lower()
        for kw in keywords:
            if kw.lower() not in title_lower:
                if len(optimized_title) < 60:
                    optimized_title = f"{optimized_title} {kw}"
        
        return optimized_title
    
    def optimize_description(self, description: str, keywords: List[str]) -> str:
        """Optimize video description for SEO.
        
        Args:
            description: Current video description
            keywords: List of target keywords
            
        Returns:
            Optimized description string
        """
        if not description:
            return ' '.join(keywords[:3]) if keywords else ''
        
        optimized_desc = description
        
        # Check description length
        if len(description) < 100:
            # Add keywords and content to make it longer
            for kw in keywords:
                if len(optimized_desc) >= 100:
                    break
                if kw.lower() not in optimized_desc.lower():
                    optimized_desc = f"{optimized_desc} {kw}"
        
        # Check for keyword inclusion
        desc_lower = optimized_desc.lower()
        for kw in keywords:
            if kw.lower() not in desc_lower:
                if len(optimized_desc) < 500:
                    optimized_desc = f"{optimized_desc} {kw}"
        
        return optimized_desc
    
    def get_seo_score(self, title: str, description: str, 
                     keywords: List[str]) -> Dict[str, Any]:
        """Get overall SEO score for video metadata.
        
        Args:
            title: Video title
            description: Video description
            keywords: List of keywords
            
        Returns:
            Dictionary with overall SEO score and recommendations
        """
        title_analysis = self.analyze_title(title)
        desc_analysis = self.analyze_description(description)
        keywords_analysis = self.analyze_keywords(keywords)
        
        # Calculate weighted score
        title_score = title_analysis['score']
        description_score = desc_analysis['score']
        keywords_score = keywords_analysis['score']
        
        overall_score = (
            title_score * 0.4 +
            description_score * 0.3 +
            keywords_score * 0.3
        )
        
        # Collect all issues and suggestions
        all_issues = title_analysis['issues'] + desc_analysis['issues'] + keywords_analysis['issues']
        all_suggestions = title_analysis['suggestions'] + desc_analysis['suggestions'] + keywords_analysis['suggestions']
        
        # Generate recommendations
        recommendations = []
        if title_score < 70:
            recommendations.append('Improve your video title')
        if description_score < 70:
            recommendations.append('Expand your video description')
        if keywords_score < 70:
            recommendations.append('Add more relevant keywords')
        
        return {
            'score': overall_score,
            'title_score': title_score,
            'description_score': description_score,
            'keywords_score': keywords_score,
            'overall_score': overall_score,
            'issues': all_issues,
            'suggestions': all_suggestions,
            'recommendations': recommendations,
            'title_analysis': title_analysis,
            'description_analysis': desc_analysis,
            'keywords_analysis': keywords_analysis
        }
    
    def generate_keyword_suggestions(self, title: str, 
                                    description: str) -> List[str]:
        """Generate keyword suggestions based on title and description.
        
        Args:
            title: Video title
            description: Video description
            
        Returns:
            List of suggested keywords
        """
        if not title and not description:
            return []
        
        # Extract words from title and description
        text = f"{title} {description}".lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Remove stop words
        filtered_words = [w for w in words if w not in self.stop_words]
        
        # Count word frequency
        word_counts = Counter(filtered_words)
        
        # Return top keywords
        return [word for word, count in word_counts.most_common(10)]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of extracted keywords
        """
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        filtered_words = [w for w in words if w.lower() not in self.stop_words]
        return list(set(filtered_words))
