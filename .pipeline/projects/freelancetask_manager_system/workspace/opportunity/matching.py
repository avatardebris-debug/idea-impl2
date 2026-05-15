"""Opportunity Matcher — advanced matching algorithms for client-offering alignment."""

from __future__ import annotations

import re
from typing import Any

from core.client_profile import ClientProfile
from core.service_offering import ServiceOffering
from opportunity.models import Opportunity, OpportunityStage


# Industry-specific keyword mappings for enhanced matching
INDUSTRY_KEYWORDS = {
    "Technology": ["software", "app", "digital", "platform", "api", "cloud", "saas", "tech"],
    "E-commerce": ["shop", "store", "ecommerce", "product", "cart", "checkout", "payment", "shipping"],
    "Healthcare": ["health", "medical", "patient", "clinic", "hospital", "wellness", "care"],
    "Education": ["learn", "course", "student", "training", "school", "university", "academy"],
    "Real Estate": ["property", "home", "house", "rental", "mortgage", "listing", "agent"],
    "Finance": ["bank", "finance", "investment", "loan", "credit", "insurance", "trading"],
    "Food & Beverage": ["food", "restaurant", "menu", "catering", "organic", "kitchen", "dining"],
    "SaaS": ["subscription", "platform", "cloud", "api", "integration", "automation", "workflow"],
    "Digital Agency": ["marketing", "seo", "brand", "design", "creative", "content", "social"],
    "Consulting": ["strategy", "advisory", "consulting", "optimization", "framework", "roadmap"],
}

# Service type keywords
SERVICE_KEYWORDS = {
    "Website Development": ["website", "web", "site", "development", "design", "layout", "page"],
    "E-commerce": ["shop", "store", "ecommerce", "product", "cart", "checkout", "payment"],
    "SEO": ["seo", "search", "ranking", "keyword", "organic", "traffic", "audit"],
    "Content Marketing": ["content", "blog", "article", "copy", "writing", "story"],
    "Social Media": ["social", "instagram", "facebook", "twitter", "linkedin", "engagement"],
    "Email Marketing": ["email", "newsletter", "campaign", "automation", "drip"],
    "Branding": ["brand", "logo", "identity", "visual", "style", "guidelines"],
    "Consulting": ["consulting", "strategy", "advisory", "framework", "roadmap"],
    "Photography": ["photo", "image", "visual", "shoot", "portfolio"],
    "Video Production": ["video", "film", "animation", "motion", "production"],
}


class OpportunityMatcher:
    """
    Advanced matching engine that evaluates client-offering alignment
    using multiple scoring dimensions.
    """

    def __init__(self, weights: dict[str, float] | None = None):
        """
        Initialize the matcher with configurable weights.
        
        Default weights:
        - keyword_overlap: 0.35
        - industry_alignment: 0.25
        - budget_compatibility: 0.20
        - urgency_match: 0.10
        - goal_alignment: 0.10
        """
        self.weights = weights or {
            "keyword_overlap": 0.35,
            "industry_alignment": 0.25,
            "budget_compatibility": 0.20,
            "urgency_match": 0.10,
            "goal_alignment": 0.10,
        }

    def match(
        self,
        offering: ServiceOffering,
        client: ClientProfile,
    ) -> dict[str, Any]:
        """
        Perform a comprehensive match between an offering and a client.
        
        Returns a dict with:
        - score: overall match score (0.0-1.0)
        - breakdown: individual component scores
        - matched_keywords: list of matched keywords
        - recommendations: suggestions for improving the match
        """
        breakdown = {}
        matched_keywords = []

        # Calculate each component
        breakdown["keyword_overlap"] = self._score_keyword_overlap(offering, client)
        breakdown["industry_alignment"] = self._score_industry_alignment(offering, client)
        breakdown["budget_compatibility"] = self._score_budget_compatibility(offering, client)
        breakdown["urgency_match"] = self._score_urgency_match(offering, client)
        breakdown["goal_alignment"] = self._score_goal_alignment(offering, client)

        # Calculate weighted total
        total_score = sum(
            breakdown[component] * weight
            for component, weight in self.weights.items()
        )

        # Find matched keywords
        matched_keywords = self._find_matched_keywords(offering, client)

        # Generate recommendations
        recommendations = self._generate_recommendations(breakdown, offering, client)

        return {
            "score": round(total_score, 4),
            "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
            "matched_keywords": matched_keywords,
            "recommendations": recommendations,
        }

    def _score_keyword_overlap(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Score keyword overlap between client needs and offering deliverables."""
        # Collect all words from client fields
        client_text = " ".join(
            client.needs + client.pain_points + client.goals + [client.industry]
        ).lower()
        
        # Collect all words from offering
        offering_text = " ".join(
            offering.title + " " + " ".join(offering.deliverables) + " " + " ".join(offering.features)
        ).lower()

        # Tokenize
        client_words = set(re.findall(r'\b\w+\b', client_text))
        offering_words = set(re.findall(r'\b\w+\b', offering_text))

        if not client_words or not offering_words:
            return 0.0

        # Calculate overlap
        intersection = client_words & offering_words
        union = client_words | offering_words

        if not union:
            return 0.0

        # Use Dice coefficient for better small-set overlap
        dice = 2 * len(intersection) / (len(client_words) + len(offering_words))
        
        # Boost for industry-specific keywords
        industry_boost = self._get_industry_keyword_boost(offering, client)
        
        return min(dice + industry_boost * 0.2, 1.0)

    def _get_industry_keyword_boost(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Get a boost score for industry-specific keyword matches."""
        client_industry = client.industry
        if client_industry not in INDUSTRY_KEYWORDS:
            return 0.0

        industry_keywords = set(INDUSTRY_KEYWORDS[client_industry])
        
        # Check if offering title or deliverables contain industry keywords
        offering_text = " ".join(offering.title + " " + " ".join(offering.deliverables)).lower()
        offering_words = set(re.findall(r'\b\w+\b', offering_text))
        
        matches = industry_keywords & offering_words
        if matches:
            return len(matches) / len(industry_keywords)
        return 0.0

    def _score_industry_alignment(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Score industry alignment between offering and client."""
        client_industry = client.industry
        
        # Check if client industry is in our known industries
        if client_industry not in INDUSTRY_KEYWORDS:
            return 0.5  # Neutral for unknown industries

        # Check if offering targets this industry
        offering_text = " ".join(offering.title + " " + " ".join(offering.deliverables)).lower()
        
        for industry, keywords in INDUSTRY_KEYWORDS.items():
            if any(kw in offering_text for kw in keywords):
                if industry == client_industry:
                    return 1.0
                # Partial match (related industry)
                return 0.7
        
        return 0.3  # No alignment found

    def _score_budget_compatibility(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Score budget compatibility between offering prices and client budget."""
        prices = [t.price for t in offering.pricing]
        if not prices:
            return 0.5

        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        # Parse client budget
        client_budget = self._parse_budget_range(client.budget_range)
        if client_budget is None:
            return 0.5

        client_min, client_max = client_budget

        # Check if any offering tier fits within client budget
        for price in prices:
            if client_min <= price <= client_max:
                return 1.0

        # Check overlap
        overlap_start = max(min_price, client_min)
        overlap_end = min(max_price, client_max)
        
        if overlap_start <= overlap_end:
            overlap_size = overlap_end - overlap_start
            total_size = max_price - min_price
            if total_size == 0:
                return 0.8
            return overlap_size / total_size

        # No overlap - calculate distance
        if max_price < client_min:
            gap = client_min - max_price
        else:
            gap = min_price - client_max

        # Normalize gap (assume $20k is max reasonable gap)
        return max(0, 1.0 - gap / 20000)

    def _parse_budget_range(self, budget_data: Any) -> tuple[float, float] | None:
        """Parse a budget range into (min, max). Handles both strings and dicts."""
        if isinstance(budget_data, dict):
            if "min" in budget_data and "max" in budget_data:
                return (float(budget_data["min"]), float(budget_data["max"]))
            return None
            
        if not isinstance(budget_data, str):
            return None
            
        import re
        match = re.search(r'\$?(\d+)[\s-]*[\$]?(\d+)', budget_data)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        match = re.search(r'\$(\d+)[\s-]*\$?(\d+)', budget_data)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        return None

    def _score_urgency_match(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Score urgency match based on client timeline and offering scope."""
        # Parse client timeline
        timeline = self._parse_timeline(client.timeline)
        if timeline is None:
            return 0.5

        # Check if offering timeline is compatible
        offering_timeline = self._get_offering_timeline(offering)
        
        if offering_timeline is None:
            return 0.5

        # If client wants it ASAP and offering is quick, high score
        if timeline == "urgent" and offering_timeline <= 14:
            return 1.0
        
        # If client has flexible timeline, any offering works
        if timeline == "flexible":
            return 0.8

        # Check if timelines are compatible
        if timeline == "short" and offering_timeline <= 30:
            return 0.9
        elif timeline == "medium" and offering_timeline <= 60:
            return 0.8
        elif timeline == "long" and offering_timeline <= 90:
            return 0.7

        return 0.3

    def _parse_timeline(self, timeline_str: str) -> str | None:
        """Parse timeline string to a standard format."""
        timeline_lower = timeline_str.lower()
        if any(word in timeline_lower for word in ["asap", "urgent", "immediate", "quick"]):
            return "urgent"
        elif any(word in timeline_lower for word in ["short", "1-2", "1-3", "month"]):
            return "short"
        elif any(word in timeline_lower for word in ["medium", "3-6", "quarter"]):
            return "medium"
        elif any(word in timeline_lower for word in ["long", "flexible", "open", "no rush"]):
            return "long"
        return None

    def _get_offering_timeline(self, offering: ServiceOffering) -> int | None:
        """Get the total timeline days from an offering."""
        if hasattr(offering, 'timeline') and offering.timeline:
            return offering.timeline.get('total_days', None)
        return None

    def _score_goal_alignment(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Score how well offering deliverables align with client goals."""
        if not client.goals:
            return 0.5

        # Check if offering features/deliverables support client goals
        goal_keywords = set()
        for goal in client.goals:
            goal_keywords.update(re.findall(r'\b\w+\b', goal.lower()))

        offering_text = " ".join(offering.deliverables + offering.features).lower()
        offering_words = set(re.findall(r'\b\w+\b', offering_text))

        if not goal_keywords or not offering_words:
            return 0.5

        matches = goal_keywords & offering_words
        if not matches:
            return 0.2

        # Score based on coverage of goals
        coverage = len(matches) / len(goal_keywords)
        return min(coverage + 0.3, 1.0)  # Base 0.3 + coverage

    def _find_matched_keywords(self, offering: ServiceOffering, client: ClientProfile) -> list[str]:
        """Find keywords that match between client and offering."""
        client_text = " ".join(client.needs + client.pain_points).lower()
        offering_text = " ".join(offering.deliverables + offering.features).lower()

        client_words = set(re.findall(r'\b\w+\b', client_text))
        offering_words = set(re.findall(r'\b\w+\b', offering_text))

        # Filter for meaningful keywords (length > 3)
        matched = [
            word for word in client_words & offering_words
            if len(word) > 3
        ]
        return sorted(matched)

    def _generate_recommendations(
        self,
        breakdown: dict[str, float],
        offering: ServiceOffering,
        client: ClientProfile,
    ) -> list[str]:
        """Generate recommendations for improving the match."""
        recommendations = []

        if breakdown.get("budget_compatibility", 0) < 0.5:
            recommendations.append(
                "Budget mismatch: Consider discussing custom pricing or adjusting scope."
            )

        if breakdown.get("industry_alignment", 0) < 0.5:
            recommendations.append(
                "Industry alignment is low: Highlight relevant case studies or adjust messaging."
            )

        if breakdown.get("urgency_match", 0) < 0.5:
            recommendations.append(
                "Timeline mismatch: Clarify delivery expectations or adjust project scope."
            )

        if breakdown.get("goal_alignment", 0) < 0.5:
            recommendations.append(
                "Goal alignment is weak: Emphasize how deliverables address specific client goals."
            )

        if breakdown.get("keyword_overlap", 0) < 0.3:
            recommendations.append(
                "Low keyword overlap: Review service description to better match client language."
            )

        if not recommendations:
            recommendations.append("Strong match! Proceed with proposal.")

        return recommendations

    def rank_matches(
        self,
        offering: ServiceOffering,
        clients: list[ClientProfile],
    ) -> list[dict[str, Any]]:
        """
        Rank all clients by match score for a given offering.
        
        Returns a list of dicts sorted by score (descending).
        """
        matches = []
        for client in clients:
            result = self.match(offering, client)
            result["client_name"] = client.name
            result["client_email"] = client.email
            result["client_industry"] = client.industry
            matches.append(result)

        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches
