"""Keyword extractor for PodcastSEO.

Uses TF-IDF scoring, spaCy NER for entity boosting, and custom stopwords
to produce ranked keywords from transcript text.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler


class KeywordExtractor:
    """Extracts and ranks keywords from clean transcript text."""

    # spaCy NER label -> category mapping
    NER_CATEGORIES = {
        "PERSON": "person",
        "ORG": "brand",
        "GPE": "topic",
        "LOC": "topic",
        "PRODUCT": "tech",
        "EVENT": "topic",
        "WORK_OF_ART": "topic",
        "LAW": "topic",
        "LANGUAGE": "topic",
        "DATE": "topic",
        "MONEY": "topic",
        "PERCENT": "topic",
        "TIME": "topic",
    }

    # Tech-related keywords that should be boosted
    TECH_KEYWORDS = {
        "api", "sdk", "framework", "library", "software", "hardware",
        "cloud", "server", "database", "algorithm", "machine learning",
        "artificial intelligence", "neural network", "deep learning",
        "python", "javascript", "react", "docker", "kubernetes",
        "blockchain", "crypto", "web3", "devops", "ci/cd",
        "microservice", "rest", "graphql", "typescript", "rust",
        "go", "golang", "java", "c++", "swift", "kotlin",
        "tensorflow", "pytorch", "aws", "azure", "gcp",
        "git", "github", "gitlab", "linux", "windows", "macos",
        "mobile", "ios", "android", "web", "frontend", "backend",
        "fullstack", "database", "sql", "nosql", "redis", "mongodb",
        "postgresql", "mysql", "elastic", "kafka", "rabbitmq",
        "nginx", "apache", "webpack", "babel", "npm", "pip",
        "maven", "gradle", "svelte", "angular", "vue", "nextjs",
        "nuxt", "flask", "django", "fastapi", "spring", "rails",
        "laravel", "express", "node", "deno", "bun",
    }

    # Brand-related keywords (common company/product names)
    BRAND_KEYWORDS = {
        "apple", "google", "microsoft", "amazon", "meta", "facebook",
        "twitter", "youtube", "netflix", "spotify", "openai", "anthropic",
        "nvidia", "intel", "amd", "ibm", "oracle", "salesforce",
        "adobe", "sap", "vmware", "cisco", "salesforce", "hubspot",
        "stripe", "paypal", "shopify", "slack", "zoom", "teams",
        "discord", "whatsapp", "telegram", "tiktok", "instagram",
        "linkedin", "reddit", "medium", "wordpress", "squarespace",
        "wix", "godaddy", "namecheap", "digitalocean", "heroku",
        "vercel", "netlify", "cloudflare", "fastly", "akamai",
    }

    def __init__(self, nlp_model: str = "en_core_web_sm", top_n: int = 20):
        """Initialize the keyword extractor.

        Args:
            nlp_model: spaCy model name to load.
            top_n: Maximum number of keywords to return.
        """
        self.nlp_model = nlp_model
        self.top_n = top_n
        self.nlp = spacy.load(nlp_model)
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self) -> set:
        """Load custom stopwords, extending spaCy's defaults."""
        sw = set(spacy.lang.en.stop_words.STOP_WORDS)
        sw.add("")
        sw.add(" ")

        # Load custom stopwords file
        stopwords_path = Path(__file__).parent / "stopwords.txt"
        if stopwords_path.exists():
            with open(stopwords_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().lower()
                    if word and len(word) > 1:
                        sw.add(word)

        return sw

    def _get_entities(self, text: str) -> Dict[str, str]:
        """Extract NER entities and their categories from text."""
        doc = self.nlp(text)
        entities: Dict[str, str] = {}
        for ent in doc.ents:
            key = ent.text.lower()
            if key not in entities:
                category = self.NER_CATEGORIES.get(ent.label_, "other")
                entities[key] = category
        return entities

    def _count_occurrences(self, text: str, keyword: str) -> int:
        """Count case-insensitive occurrences of a keyword in text."""
        return len(re.findall(re.escape(keyword), text, re.IGNORECASE))

    def _extract_bigrams_trigrams(self, text: str) -> List[str]:
        """Extract bigrams and trigrams from tokenized text."""
        doc = self.nlp(text)
        phrases: List[str] = []

        # Extract noun phrases and multi-word tokens
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip().lower()
            if phrase and len(phrase) > 2 and phrase not in self.stopwords:
                phrases.append(phrase)

        # Also extract consecutive noun/adjective sequences
        tokens = doc
        for i in range(len(tokens) - 1):
            if tokens[i].pos_ in ("NOUN", "PROPN", "ADJ") and tokens[i + 1].pos_ in ("NOUN", "PROPN"):
                bigram = f"{tokens[i].text.lower()} {tokens[i + 1].text.lower()}"
                if bigram not in self.stopwords and len(bigram) > 3:
                    phrases.append(bigram)

        for i in range(len(tokens) - 2):
            if (tokens[i].pos_ in ("NOUN", "PROPN", "ADJ") and
                    tokens[i + 1].pos_ in ("NOUN", "PROPN", "ADJ") and
                    tokens[i + 2].pos_ in ("NOUN", "PROPN")):
                trigram = f"{tokens[i].text.lower()} {tokens[i + 1].text.lower()} {tokens[i + 2].text.lower()}"
                if trigram not in self.stopwords and len(trigram) > 4:
                    phrases.append(trigram)

        return phrases

    def _classify_keyword(self, keyword: str, ner_entities: Dict[str, str]) -> str:
        """Classify a keyword into topic/brand/tech/person/other."""
        kw_lower = keyword.lower()

        # Check if it's a person entity
        if kw_lower in ner_entities and ner_entities[kw_lower] == "PERSON":
            return "person"

        # Check if it's a brand entity
        if kw_lower in ner_entities and ner_entities[kw_lower] == "ORG":
            return "brand"

        # Check against predefined keyword lists
        for tech_kw in self.TECH_KEYWORDS:
            if tech_kw in kw_lower:
                return "technical"

        for brand_kw in self.BRAND_KEYWORDS:
            if brand_kw in kw_lower:
                return "brand"

        # Health-related keywords
        health_keywords = {
            "nutrition", "gut", "health", "probiotics", "prebiotics", "inflammation",
            "diet", "vitamin", "mineral", "protein", "carbohydrate", "fat",
            "fiber", "enzyme", "metabolism", "immune", "allergy", "symptom",
            "therapy", "treatment", "diagnosis", "clinical", "medical",
            "hospital", "doctor", "patient", "disease", "cancer", "diabetes",
            "heart", "brain", "lung", "liver", "kidney", "blood",
            "exercise", "fitness", "weight", "muscle", "bone", "joint",
            "sleep", "stress", "anxiety", "depression", "mental", "wellness",
        }
        for hw in health_keywords:
            if hw in kw_lower:
                return "health"

        # Business-related keywords
        business_keywords = {
            "remote", "hybrid", "business", "strategy", "leadership", "innovation",
            "management", "marketing", "sales", "revenue", "profit", "cost",
            "budget", "investment", "startup", "entrepreneur", "company", "corporate",
            "enterprise", "client", "customer", "market", "industry", "sector",
            "team", "project", "goal", "objective", "target", "performance",
            "productivity", "efficiency", "growth", "development", "training",
            "hire", "recruit", "employee", "manager", "director", "executive",
            "ceo", "cto", "cfo", "coo", "vp", "cto", "cto",
        }
        for bw in business_keywords:
            if bw in kw_lower:
                return "business"

        # Default to general
        return "general"

    def extract(self, text: str, top_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract ranked keywords from clean transcript text.

        Args:
            text: Clean transcript text.
            top_n: Override the default top_n count.

        Returns:
            List of dicts with keys: keyword, score, category, occurrences.
        """
        if not text or not text.strip():
            return []

        if top_n is None:
            top_n = self.top_n

        # Handle single word
        if len(text.split()) == 1:
            word = text.strip().lower()
            if word in self.stopwords:
                return []
            return [{
                "keyword": word,
                "score": 1.0,
                "category": "topic",
                "occurrences": 1,
            }]

        # Get NER entities for boosting
        ner_entities = self._get_entities(text)

        # Extract phrases (bigrams/trigrams)
        phrases = self._extract_bigrams_trigrams(text)

        # Combine single words and phrases for TF-IDF
        # Single words: tokens that are nouns, proper nouns, or adjectives
        doc = self.nlp(text)
        single_words: List[str] = []
        for token in doc:
            if (token.pos_ in ("NOUN", "PROPN", "ADJ") and
                    len(token.text) > 2 and
                    token.text.lower() not in self.stopwords):
                single_words.append(token.text.lower())

        # Use phrases as documents for TF-IDF
        if not phrases and not single_words:
            return []

        # Build candidate keywords with initial scores
        candidates: List[Tuple[str, float, str, int]] = []

        # TF-IDF on phrases
        if phrases:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words=None,  # We handle stopwords manually
            )
            tfidf_matrix = vectorizer.fit_transform(phrases)
            feature_names = vectorizer.get_feature_names_out()

            # Get top phrases by TF-IDF score
            scores = tfidf_matrix.toarray().sum(axis=0)
            for i, phrase in enumerate(feature_names):
                score = float(scores[i])
                if score > 0:
                    category = self._classify_keyword(phrase, ner_entities)
                    occurrences = self._count_occurrences(text, phrase)
                    candidates.append((phrase, score, category, occurrences))

        # TF-IDF on single words
        if single_words:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words=None,
            )
            tfidf_matrix = vectorizer.fit_transform(single_words)
            feature_names = vectorizer.get_feature_names_out()

            scores = tfidf_matrix.toarray().sum(axis=0)
            for i, word in enumerate(feature_names):
                score = float(scores[i])
                if score > 0:
                    category = self._classify_keyword(word, ner_entities)
                    occurrences = self._count_occurrences(text, word)
                    candidates.append((word, score, category, occurrences))

        # Boost NER entities
        for entity, category in ner_entities.items():
            if entity not in [c[0] for c in candidates]:
                occurrences = self._count_occurrences(text, entity)
                if occurrences > 0:
                    candidates.append((entity, 0.5, category, occurrences))

        # Normalize scores using MinMaxScaler
        if candidates:
            scores = [[c[1]] for c in candidates]
            scaler = MinMaxScaler()
            normalized = scaler.fit_transform(scores).flatten()
            candidates = [
                (c[0], float(normalized[i]), c[2], c[3])
                for i, c in enumerate(candidates)
            ]

        # Sort by score descending, then by occurrences descending
        candidates.sort(key=lambda x: (x[1], x[3]), reverse=True)

        # Remove duplicates (keep highest score)
        seen: set = set()
        unique_candidates: List[Tuple[str, float, str, int]] = []
        for c in candidates:
            if c[0] not in seen:
                seen.add(c[0])
                unique_candidates.append(c)

        # Return top N
        result = []
        for keyword, score, category, occurrences in unique_candidates[:top_n]:
            result.append({
                "keyword": keyword,
                "score": round(score, 4),
                "category": category,
                "occurrences": occurrences,
            })

        return result
