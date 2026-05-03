"""Qualitative style analysis for the Scott Adams corpus.

Performs deeper stylistic analysis including:
- Rhetorical device detection
- Sentence structure patterns
- Tone and register analysis
- Thematic category classification
- Stylistic signature extraction
"""

import json
import logging
import os
import re
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Rhetorical devices patterns
RHETORICAL_DEVICES = {
    "rhetorical_question": {
        "pattern": r"\?(\s|$)",
        "description": "Rhetorical questions",
    },
    "direct_address": {
        "pattern": r"\b(you|your|yours)\b",
        "description": "Direct address to reader",
    },
    "first_person": {
        "pattern": r"\b(i|my|mine|me)\b",
        "description": "First-person narration",
    },
    "imperative": {
        "pattern": r"\b(stop|start|remember|realize|understand|think|know|forget|ignore|focus|build|create|manage|never|always|always)\b\s+\w+",
        "description": "Imperative commands",
    },
    "contrast": {
        "pattern": r"\b(but|however|yet|although|whereas|instead|rather|conversely|on the other hand)\b",
        "description": "Contrastive transitions",
    },
    "emphasis": {
        "pattern": r"\b(not|never|nothing|nobody|no one|absolutely|definitely|certainly|truly|actually|honestly|frankly)\b",
        "description": "Emphatic language",
    },
    "generalization": {
        "pattern": r"\b(most people|everyone|nobody|all people|few people|anyone|everybody)\b",
        "description": "Universal generalizations",
    },
    "conditional": {
        "pattern": r"\b(if|when|unless|provided that|as long as)\b",
        "description": "Conditional statements",
    },
    "metaphor": {
        "pattern": r"\b(is|are|was|were)\s+(a|an)\s+(game|battle|war|journey|path|key|secret|formula|art|science|magic|power|weapon|tool|foundation|cornerstone)\b",
        "description": "Metaphorical language",
    },
    "anecdote_marker": {
        "pattern": r"\b(i remember|i used to|i learned|i discovered|i noticed|i found|i realized|i saw|i witnessed)\b",
        "description": "Anecdotal framing",
    },
}

# Sentence pattern templates
SENTENCE_PATTERNS = {
    "statement": r"\.(\s|$)",
    "question": r"\?(\s|$)",
    "exclamation": r"!(\s|$)",
    "ellipsis": r"\.{3}(\s|$)",
    "dash": r"—(\s|$)|—$",
    "colon": r":(\s|$)",
}

# Thematic categories
THEMATIC_CATEGORIES = {
    "success": [
        "success", "win", "winning", "achieve", "achievement", "accomplish",
        "goal", "goals", "goal-setting", "outcome", "results", "victory",
        "triumph", "prosperity", "wealth", "rich", "riches", "fortune",
    ],
    "failure": [
        "fail", "failure", "mistake", "mistakes", "error", "errors",
        "lose", "losing", "loss", "defeat", "setback", "disaster",
        "wrong", "incorrect", "bad", "poor", "worse", "worst",
    ],
    "management": [
        "management", "manager", "managers", "leader", "leaders",
        "leadership", "team", "teams", "organization", "organizations",
        "company", "companies", "corporate", "hierarchy", "boss", "bosses",
        "employee", "employees", "staff", "workforce", "subordinate",
    ],
    "systems": [
        "system", "systems", "process", "processes", "framework", "frameworks",
        "structure", "structures", "mechanism", "mechanisms", "design",
        "architecture", "workflow", "procedure", "procedures", "method",
        "methods", "approach", "approaches", "strategy", "strategies",
    ],
    "habits": [
        "habit", "habits", "routine", "routines", "pattern", "patterns",
        "behavior", "behaviors", "practice", "practices", "discipline",
        "consistency", "consistent", "repeated", "repetition", "automatic",
        "compulsion", "ritual", "rituals", "custom", "customs",
    ],
    "probability": [
        "probability", "probable", "probabilities", "chance", "chances",
        "odds", "likelihood", "uncertainty", "risk", "risks", "bet",
        "bets", "wager", "wagers", "gamble", "gambling", "random",
        "randomness", "stochastic", "distribution", "variance", "variations",
    ],
    "psychology": [
        "psychology", "psychological", "mind", "minds", "brain", "brains",
        "cognitive", "cognition", "thinking", "thoughts", "perception",
        "perceptions", "emotion", "emotions", "feeling", "feelings",
        "motivation", "motivations", "drive", "drives", "desire", "desires",
        "belief", "beliefs", "attitude", "attitudes", "bias", "biases",
    ],
    "communication": [
        "communication", "communicate", "communicating", "message", "messages",
        "word", "words", "language", "languages", "speech", "speeches",
        "writing", "writings", "text", "texts", "tone", "tones", "voice",
        "voices", "style", "styles", "clarity", "clear", "confusion",
        "misunderstanding", "misunderstandings", "persuasion", "persuade",
    ],
    "time": [
        "time", "times", "moment", "moments", "now", "then", "later",
        "soon", "early", "late", "always", "never", "sometimes", "often",
        "frequently", "rarely", "occasionally", "period", "periods",
        "duration", "length", "short", "long", "quick", "slow", "fast",
    ],
    "money": [
        "money", "moneys", "cash", "currency", "dollars", "dollar",
        "income", "incomes", "revenue", "revenues", "profit", "profits",
        "loss", "losses", "expense", "expenses", "cost", "costs",
        "price", "prices", "value", "values", "worth", "wealth", "wealthy",
        "poor", "poverty", "bank", "banks", "investment", "investments",
        "salary", "salaries", "wage", "wages", "pay", "paid", "payment",
    ],
}


def detect_rhetorical_devices(text: str) -> Dict[str, int]:
    """Detect rhetorical devices in text.

    Args:
        text: Input text.

    Returns:
        Dictionary mapping device names to counts.
    """
    counts = {}
    for device_name, device_info in RHETORICAL_DEVICES.items():
        matches = re.findall(device_info["pattern"], text, re.IGNORECASE)
        counts[device_name] = len(matches)
    return counts


def analyze_sentence_patterns(text: str) -> Dict[str, int]:
    """Analyze sentence structure patterns.

    Args:
        text: Input text.

    Returns:
        Dictionary mapping pattern names to counts.
    """
    counts = {}
    for pattern_name, pattern in SENTENCE_PATTERNS.items():
        matches = re.findall(pattern, text)
        counts[pattern_name] = len(matches)
    return counts


def classify_themes(text: str) -> Dict[str, int]:
    """Classify text into thematic categories.

    Args:
        text: Input text.

    Returns:
        Dictionary mapping theme names to counts.
    """
    text_lower = text.lower()
    counts = {}
    for theme, keywords in THEMATIC_CATEGORIES.items():
        count = 0
        for keyword in keywords:
            count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        counts[theme] = count
    return counts


def compute_sentence_length_distribution(text: str) -> Dict:
    """Compute sentence length distribution.

    Args:
        text: Input text.

    Returns:
        Dictionary with sentence length statistics.
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return {}

    lengths = [len(s.split()) for s in sentences]

    return {
        "count": len(lengths),
        "mean": sum(lengths) / len(lengths),
        "min": min(lengths),
        "max": max(lengths),
        "distribution": Counter(lengths),
    }


def analyze_paragraph_structure(text: str) -> Dict:
    """Analyze paragraph structure.

    Args:
        text: Input text.

    Returns:
        Dictionary with paragraph structure metrics.
    """
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return {}

    paragraph_lengths = [len(p.split()) for p in paragraphs]

    # Analyze paragraph types
    short_paragraphs = sum(1 for l in paragraph_lengths if l <= 20)
    medium_paragraphs = sum(1 for l in paragraph_lengths if 20 < l <= 50)
    long_paragraphs = sum(1 for l in paragraph_lengths if l > 50)

    return {
        "count": len(paragraphs),
        "mean_length": sum(paragraph_lengths) / len(paragraph_lengths),
        "short_paragraphs": short_paragraphs,
        "medium_paragraphs": medium_paragraphs,
        "long_paragraphs": long_paragraphs,
        "short_pct": short_paragraphs / len(paragraphs) * 100,
        "medium_pct": medium_paragraphs / len(paragraphs) * 100,
        "long_pct": long_paragraphs / len(paragraphs) * 100,
    }


def extract_stylistic_signature(samples: List[Dict]) -> Dict:
    """Extract overall stylistic signature from corpus.

    Args:
        samples: List of corpus samples.

    Returns:
        Dictionary with stylistic signature metrics.
    """
    total_rhetorical = Counter()
    total_themes = Counter()
    total_sentence_patterns = Counter()
    total_paragraph_structure = []

    for sample in samples:
        text = sample.get("text", "")

        # Rhetorical devices
        rhetorical = detect_rhetorical_devices(text)
        for device, count in rhetorical.items():
            total_rhetorical[device] += count

        # Themes
        themes = classify_themes(text)
        for theme, count in themes.items():
            total_themes[theme] += count

        # Sentence patterns
        patterns = analyze_sentence_patterns(text)
        for pattern, count in patterns.items():
            total_sentence_patterns[pattern] += count

        # Paragraph structure
        para_struct = analyze_paragraph_structure(text)
        if para_struct:
            total_paragraph_structure.append(para_struct)

    # Normalize rhetorical devices
    total_words = sum(len(s.get("text", "").split()) for s in samples)
    rhetorical_per_1000 = {
        device: (count / total_words * 1000) if total_words > 0 else 0
        for device, count in total_rhetorical.items()
    }

    # Normalize themes
    theme_percentages = {
        theme: (count / total_words * 100) if total_words > 0 else 0
        for theme, count in total_themes.items()
    }

    # Average paragraph structure
    avg_para_struct = {}
    if total_paragraph_structure:
        avg_para_struct = {
            "count": statistics.mean([p["count"] for p in total_paragraph_structure]),
            "mean_length": statistics.mean([p["mean_length"] for p in total_paragraph_structure]),
            "short_pct": statistics.mean([p["short_pct"] for p in total_paragraph_structure]),
            "medium_pct": statistics.mean([p["medium_pct"] for p in total_paragraph_structure]),
            "long_pct": statistics.mean([p["long_pct"] for p in total_paragraph_structure]),
        }

    return {
        "rhetorical_devices_per_1000": rhetorical_per_1000,
        "theme_percentages": theme_percentages,
        "sentence_patterns": dict(total_sentence_patterns),
        "avg_paragraph_structure": avg_para_struct,
    }


def run_qualitative_analysis(corpus_path: str) -> Dict:
    """Run all qualitative analyses on the corpus.

    Args:
        corpus_path: Path to corpus.jsonl file.

    Returns:
        Dictionary with all qualitative analysis results.
    """
    logger.info("Starting qualitative analysis...")

    samples = load_corpus(corpus_path)

    results = {
        "stylistic_signature": extract_stylistic_signature(samples),
        "sample_rhetorical": [],
        "sample_themes": [],
    }

    # Analyze top 100 samples for detailed breakdown
    for sample in samples[:100]:
        text = sample.get("text", "")
        results["sample_rhetorical"].append({
            "id": sample.get("id", ""),
            "rhetorical_devices": detect_rhetorical_devices(text),
        })
        results["sample_themes"].append({
            "id": sample.get("id", ""),
            "themes": classify_themes(text),
        })

    logger.info("Qualitative analysis complete.")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    corpus_path = os.path.join(os.path.dirname(__file__), "..", "corpus", "processed", "corpus.jsonl")
    if not os.path.exists(corpus_path):
        logger.error(f"Corpus file not found: {corpus_path}")
        logger.info("Run scraper/main.py first to generate the corpus.")
        exit(1)

    results = run_qualitative_analysis(corpus_path)

    # Print summary
    print("\n" + "=" * 60)
    print("QUALITATIVE ANALYSIS SUMMARY")
    print("=" * 60)

    if results["stylistic_signature"]:
        sig = results["stylistic_signature"]
        print(f"\nStylistic Signature:")
        print(f"  Top rhetorical devices (per 1000 words):")
        for device, count in sorted(sig["rhetorical_devices_per_1000"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {device}: {count:.2f}")

        print(f"\n  Top themes (% of text):")
        for theme, pct in sorted(sig["theme_percentages"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {theme}: {pct:.2f}%")

        print(f"\n  Sentence patterns:")
        for pattern, count in sorted(sig["sentence_patterns"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {pattern}: {count}")

        if sig["avg_paragraph_structure"]:
            ps = sig["avg_paragraph_structure"]
            print(f"\n  Average paragraph structure:")
            print(f"    Count: {ps['count']:.1f}")
            print(f"    Mean length: {ps['mean_length']:.1f} words")
            print(f"    Short (<20 words): {ps['short_pct']:.1f}%")
            print(f"    Medium (20-50 words): {ps['medium_pct']:.1f}%")
            print(f"    Long (>50 words): {ps['long_pct']:.1f}%")

    print("\n" + "=" * 60)
