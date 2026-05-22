"""PDF summarization module.

This module provides functionality to extract text from PDF files and generate summaries using an LLM.
"""

import os
from typing import Optional
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


class PDFSummarizer:
    """Summarizer for PDF documents."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the PDF summarizer.
        
        Args:
            api_key: OpenAI API key. If None, will be read from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Extracted text content.
            
        Raises:
            FileNotFoundError: If the PDF file does not exist.
            Exception: If there's an error reading the PDF.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        reader = PdfReader(pdf_path)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        
        return "\n".join(text)
    
    def summarize(self, pdf_path: str, prompt: Optional[str] = None) -> str:
        """Extract text from a PDF and generate a summary.
        
        Args:
            pdf_path: Path to the PDF file.
            prompt: Optional custom prompt for the summarization.
            
        Returns:
            Generated summary.
            
        Raises:
            FileNotFoundError: If the PDF file does not exist.
            Exception: If there's an error during summarization.
        """
        # Extract text from PDF
        text = self.extract_text(pdf_path)
        
        if not text.strip():
            return "No text could be extracted from the PDF."
        
        # Prepare the prompt for summarization
        if prompt is None:
            prompt = "Please provide a concise summary of the following document:"
        
        full_prompt = f"{prompt}\n\nDocument content:\n{text[:25000]}"  # Limit to avoid token limits
        
        # Generate summary using OpenAI
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise and accurate summaries of documents."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
