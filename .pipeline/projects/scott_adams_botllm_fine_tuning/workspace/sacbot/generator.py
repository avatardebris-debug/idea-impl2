"""Generator module for creating content using LLMs."""

import json
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

import openai
from sacbot.types import CONTENT_SPECS, ContentType

# Expose OpenAI at module level for test patching
OpenAI = openai.OpenAI


@dataclass
class FewShotSample:
    """A sample for few-shot prompting."""

    text: str
    source_type: str = ""
    topic: str = ""
    length: int | None = None

    def __post_init__(self):
        """Calculate length after initialization if not provided."""
        if self.length is None:
            self.length = len(self.text.split())


@dataclass
class GenerationResult:
    """Result of a generation attempt."""

    content: Optional[str]
    model: str
    tokens_used: int
    latency_seconds: float
    prompt_tokens: int
    few_shot_count: int
    content_type: str
    topic: str
    error: Optional[str] = None


SYSTEM_PROMPT = """You are a content generator that creates engaging, persuasive content in the style of Scott Adams (creator of Dilbert).

Your writing style is characterized by:
- Direct address to the reader ("you", "your")
- Probability language ("likely", "probably", "chance")
- Rhetorical questions
- Clear, simple language
- Practical advice
- Humorous observations
- Systems thinking

Generate content that is:
- Engaging and persuasive
- Written in Scott Adams' style
- Appropriate for the specified content type
- Focused on the given topic"""


def _topic_overlap(topic1: str, topic2: str) -> float:
    """Calculate topic overlap between two topics.

    Args:
        topic1: First topic string
        topic2: Second topic string

    Returns:
        Float between 0 and 1 indicating overlap
    """
    if not topic1 or not topic2:
        return 0.0

    words1 = set(topic1.lower().split())
    words2 = set(topic2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)


def _length_similarity(length1: int, length2: int) -> float:
    """Calculate similarity between two lengths.

    Args:
        length1: First length
        length2: Second length

    Returns:
        Float between 0 and 1 indicating similarity
    """
    if length1 == 0 and length2 == 0:
        return 1.0
    if length1 == 0 or length2 == 0:
        return 0.0

    longer = max(length1, length2)
    shorter = min(length1, length2)

    return shorter / longer


def _load_corpus(corpus_path: str) -> List[FewShotSample]:
    """Load corpus from JSONL file.

    Args:
        corpus_path: Path to JSONL file

    Returns:
        List of FewShotSample objects
    """
    samples = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                sample = FewShotSample(
                    text=data.get("text", ""),
                    source_type=data.get("source_type", ""),
                    topic=data.get("topic", ""),
                )
                samples.append(sample)
            except (json.JSONDecodeError, KeyError):
                continue
    return samples


def select_few_shot(
    corpus_path: str,
    topic: str,
    content_type: str,
    target_length: int = 100,
    n: int = 3,
) -> List[FewShotSample]:
    """Select few-shot examples from corpus.

    Args:
        corpus_path: Path to JSONL corpus file
        topic: Target topic
        content_type: Target content type
        target_length: Target length for similarity scoring
        n: Number of examples to select

    Returns:
        List of FewShotSample objects
    """
    samples = _load_corpus(corpus_path)

    scored_samples = []
    for sample in samples:
        topic_score = _topic_overlap(sample.topic, topic)
        length_score = _length_similarity(sample.length, target_length)
        type_score = 1.0 if sample.source_type == content_type else 0.5
        score = topic_score * 0.5 + length_score * 0.3 + type_score * 0.2
        scored_samples.append((score, sample))

    scored_samples.sort(key=lambda x: x[0], reverse=True)
    return [sample for _, sample in scored_samples[:n]]


def build_prompt(
    few_shot: List[FewShotSample],
    topic: str,
    content_type: str,
    target_length: int = 100,
    output_format: str = "blog",
) -> str:
    """Build prompt for LLM.

    Args:
        few_shot: List of few-shot examples
        topic: Target topic
        content_type: Target content type
        target_length: Target length
        output_format: Output format (for compatibility)

    Returns:
        Prompt string
    """
    spec = CONTENT_SPECS.get(content_type)
    output_instruction = spec.output_instruction if spec else ""

    prompt = SYSTEM_PROMPT + f"\n\nTopic: {topic}\nContent Type: {content_type}\nTarget Length: {target_length} words\n\n"

    if output_instruction:
        prompt += f"Output Format: {output_instruction}\n\n"

    if few_shot:
        prompt += "Examples:\n\n"
        for i, sample in enumerate(few_shot, 1):
            prompt += f"Example {i}:\n"
            prompt += f"Topic: {sample.topic}\n"
            prompt += f"Content Type: {sample.source_type}\n"
            prompt += f"Content:\n{sample.text}\n\n"

    prompt += "Generate content:"
    return prompt


def call_llm(
    prompt: str,
    model: str = "gpt-4o",
    api_key: str | None = None,
    temperature: float = 0.7,
    seed: int | None = None,
    max_tokens: int | None = None,
) -> GenerationResult:
    """Call LLM API.

    Args:
        prompt: Prompt string
        model: OpenAI model name
        api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        temperature: Sampling temperature
        seed: Random seed for reproducibility
        max_tokens: Maximum tokens for the response

    Returns:
        GenerationResult object
    """
    start_time = time.time()
    try:
        client = OpenAI(api_key=api_key)
        kwargs: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if seed is not None:
            kwargs["seed"] = seed
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        prompt_tokens = response.usage.prompt_tokens
        latency = time.time() - start_time

        return GenerationResult(
            content=content,
            model=model,
            tokens_used=tokens_used,
            latency_seconds=latency,
            prompt_tokens=prompt_tokens,
            few_shot_count=0,
            content_type="",
            topic="",
        )
    except Exception as e:
        latency = time.time() - start_time
        return GenerationResult(
            content=None,
            model=model,
            tokens_used=0,
            latency_seconds=latency,
            prompt_tokens=0,
            few_shot_count=0,
            content_type="",
            topic="",
            error=str(e),
        )


def generate(
    topic: str,
    content_type: str,
    corpus_path: str,
    n_few_shot: int = 3,
    model: str = "gpt-4o",
    api_key: str | None = None,
    temperature: float = 0.7,
    seed: int | None = None,
    output_format: str = "text",
) -> GenerationResult:
    """Generate content using LLM.

    Args:
        topic: Target topic
        content_type: Target content type
        corpus_path: Path to corpus file
        n_few_shot: Number of few-shot examples
        model: OpenAI model name
        api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        temperature: Sampling temperature
        seed: Random seed for reproducibility
        output_format: Output format (text or json)

    Returns:
        GenerationResult object
    """
    spec = CONTENT_SPECS[content_type]
    target_length = spec.target_length

    few_shot = select_few_shot(
        corpus_path=corpus_path,
        topic=topic,
        content_type=content_type,
        target_length=target_length,
        n=n_few_shot,
    )

    prompt = build_prompt(
        few_shot=few_shot,
        topic=topic,
        content_type=content_type,
        target_length=target_length,
        output_format=output_format,
    )

    result = call_llm(
        prompt=prompt,
        model=model,
        api_key=api_key,
        temperature=temperature,
        seed=seed,
        max_tokens=spec.max_tokens,
    )

    # Update result with generation metadata
    result.few_shot_count = len(few_shot)
    result.content_type = content_type
    result.topic = topic

    return result
