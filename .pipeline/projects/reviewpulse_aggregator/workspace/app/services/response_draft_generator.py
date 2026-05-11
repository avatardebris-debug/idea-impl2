"""LLM-powered response draft generator for business reviews.

Generates professional response drafts for customer reviews using
an LLM API (OpenAI, Anthropic, etc.).
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from app.config import settings
from app.models.unified_review import ReviewData

logger = logging.getLogger(__name__)


class ResponseDraftGenerator:
    """Generates response drafts for reviews using an LLM."""

    def __init__(self, provider: str = "openai"):
        self.provider = provider.lower()

    def generate_draft(
        self,
        review: ReviewData,
        business_name: str,
        tone: str = "professional",
        include_thanks: bool = True,
    ) -> Optional[str]:
        """Generate a response draft for a review.

        Args:
            review: The review to respond to.
            business_name: Name of the business.
            tone: Response tone (professional, friendly, concise).
            include_thanks: Whether to include a thank-you note.

        Returns:
            Generated response draft or None if generation fails.
        """
        if not review.text:
            return None

        prompt = self._build_prompt(
            review=review,
            business_name=business_name,
            tone=tone,
            include_thanks=include_thanks,
        )

        try:
            if self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "anthropic":
                return self._call_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Failed to generate response draft: {e}")
            return None

    def generate_batch(
        self,
        reviews: list[ReviewData],
        business_name: str,
        tone: str = "professional",
        include_thanks: bool = True,
    ) -> list[Optional[str]]:
        """Generate response drafts for a batch of reviews.

        Args:
            reviews: List of reviews to respond to.
            business_name: Name of the business.
            tone: Response tone.
            include_thanks: Whether to include a thank-you note.

        Returns:
            List of generated response drafts.
        """
        return [
            self.generate_draft(review, business_name, tone, include_thanks)
            for review in reviews
        ]

    def _build_prompt(
        self,
        review: ReviewData,
        business_name: str,
        tone: str,
        include_thanks: bool,
    ) -> str:
        """Build the prompt for the LLM."""
        sentiment = review.sentiment_label or "neutral"
        rating = review.rating or 3

        tone_instructions = {
            "professional": "Maintain a professional and courteous tone.",
            "friendly": "Use a warm and friendly tone.",
            "concise": "Keep the response brief and to the point.",
        }

        thanks_instruction = (
            "Start with a thank-you for the review."
            if include_thanks
            else "Do not include a thank-you note."
        )

        return f"""You are a customer service representative for {business_name}.
Write a response to the following customer review.

Review Details:
- Rating: {rating}/5
- Sentiment: {sentiment}
- Review Text: "{review.text}"

Guidelines:
- {tone_instructions.get(tone, tone_instructions["professional"])}
- {thanks_instruction}
- Address any specific concerns mentioned in the review.
- If the review is positive, express appreciation and invite them back.
- If the review is negative, apologize, acknowledge the issue, and offer to make it right.
- Keep the response under 150 words.
- Do not include any placeholders like [Name] or [Date].
- Do not include any markdown formatting.

Response:"""

    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API to generate response."""
        try:
            import openai

            client = openai.OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful customer service assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic API to generate response."""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            message = client.messages.create(
                model=settings.anthropic_model or "claude-3-haiku-20240307",
                max_tokens=200,
                temperature=0.7,
                system="You are a helpful customer service assistant.",
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
