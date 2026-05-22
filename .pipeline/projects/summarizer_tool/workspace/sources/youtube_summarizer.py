"""YouTube summarization module.

This module provides functionality to extract transcripts from YouTube videos and generate summaries.
"""

import os
import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


class YouTubeSummarizer:
    """Summarizer for YouTube videos."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the YouTube summarizer.
        
        Args:
            api_key: OpenAI API key. If None, will be read from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from a YouTube URL.
        
        Args:
            url: YouTube URL.
            
        Returns:
            Video ID.
            
        Raises:
            ValueError: If the URL is not a valid YouTube URL.
        """
        # Pattern to match YouTube URLs (both standard and short URLs)
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
            r'(?:youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Invalid YouTube URL: {url}")
    
    def fetch_transcript(self, video_id: str) -> str:
        """Fetch transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID.
            
        Returns:
            Transcript text.
            
        Raises:
            NoTranscriptFound: If no transcript is available.
            TranscriptsDisabled: If transcripts are disabled.
            Exception: If there's an error fetching the transcript.
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = " ".join([part['text'] for part in transcript_list])
            return transcript
        except NoTranscriptFound:
            raise NoTranscriptFound(f"No transcript found for video ID: {video_id}")
        except TranscriptsDisabled:
            raise TranscriptsDisabled(f"Transcripts are disabled for video ID: {video_id}")
    
    def summarize(self, url: str, prompt: Optional[str] = None) -> str:
        """Fetch transcript from a YouTube video and generate a summary.
        
        Args:
            url: YouTube URL.
            prompt: Optional custom prompt for the summarization.
            
        Returns:
            Generated summary.
            
        Raises:
            ValueError: If the URL is not a valid YouTube URL.
            Exception: If there's an error during summarization.
        """
        # Extract video ID
        video_id = self.extract_video_id(url)
        
        # Fetch transcript
        transcript = self.fetch_transcript(video_id)
        
        if not transcript.strip():
            return "No transcript could be found for this video."
        
        # Prepare the prompt for summarization
        if prompt is None:
            prompt = "Please provide a concise summary of the following YouTube video transcript:"
        
        full_prompt = f"{prompt}\n\nTranscript content:\n{transcript[:25000]}"  # Limit to avoid token limits
        
        # Generate summary using OpenAI
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise and accurate summaries of video transcripts."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
