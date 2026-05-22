"""Web summarization module.

This module provides functionality to scrape web content and generate summaries.
"""

import os
import re
from typing import Optional
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


class WebSummarizer:
    """Summarizer for web pages."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the web summarizer.
        
        Args:
            api_key: OpenAI API key. If None, will be read from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def fetch_content(self, url: str) -> str:
        """Fetch content from a web page.
        
        Args:
            url: URL of the web page.
            
        Returns:
            Extracted text content.
            
        Raises:
            requests.RequestException: If there's an error fetching the page.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.text
    
    def extract_text(self, html_content: str) -> str:
        """Extract text content from HTML.
        
        Args:
            html_content: Raw HTML content.
            
        Returns:
            Extracted text content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def summarize(self, url: str, prompt: Optional[str] = None) -> str:
        """Fetch content from a web page and generate a summary.
        
        Args:
            url: URL of the web page.
            prompt: Optional custom prompt for the summarization.
            
        Returns:
            Generated summary.
            
        Raises:
            requests.RequestException: If there's an error fetching the page.
            Exception: If there's an error during summarization.
        """
        # Fetch content
        html_content = self.fetch_content(url)
        
        # Extract text
        text = self.extract_text(html_content)
        
        if not text.strip():
            return "No text content could be extracted from this page."
        
        # Prepare the prompt for summarization
        if prompt is None:
            prompt = "Please provide a concise summary of the following web page content:"
        
        full_prompt = f"{prompt}\n\nWeb page content:\n{text[:25000]}"  # Limit to avoid token limits
        
        # Generate summary using OpenAI
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise and accurate summaries of web content."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
