"""Risk analysis module — calculates risk scores for companies based on multiple factors."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from osint_corp.correlation import Relationship
from osint_corp.models.entities import Company, Filing

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    """A single risk factor."""
    name: str
    score: float  # 0-100
    weight: float  # 0-1 (relative importance)
    description: str
    evidence: list[str] = field(default_factory=list)

    def weighted_score(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "description": self.description,
            "evidence": self.evidence,
        }


@dataclass
class RiskAssessment:
    """Overall risk assessment for a company."""
    company_name: str
    ticker: Optional[str]
    cik: Optional[str]
    overall_score: float = 0.0  # 0-100
    risk_level: str = "unknown"  # "low", "medium", "high", "critical"
    factors: list[RiskFactor] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    trend: Optional[str] = None  # "improving", "stable", "deteriorating"
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "ticker": self.ticker,
            "cik": self.cik,
            "overall_score": self.overall_score,
            "risk_level": self.risk_level,
            "factors": [f.to_dict() for f in self.factors],
            "recommendations": self.recommendations,
            "trend": self.trend,
            "last_updated": self.last_updated,
        }


class RiskAnalyzer:
    """Analyzes and scores risk for companies."""

    # Risk level thresholds
    RISK_LEVELS = {
        "low": (0, 25),
        "medium": (25, 50),
        "high": (50, 75),
        "critical": (75, 101),
    }

    def __init__(self):
        self._cache: dict[str, RiskAssessment] = {}

    def assess(
        self,
        company: Company,
        filings: Optional[list[Filing]] = None,
        relationships: Optional[list[Relationship]] = None,
    ) -> RiskAssessment:
        """Assess the risk profile for a company.

        Args:
            company: The target Company.
            filings: Optional list of SEC filings.
            relationships: Optional list of relationships.

        Returns:
            RiskAssessment with overall score and breakdown.
        """
        cache_key = f"{company.cik}_{company.ticker}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        assessment = self._assess_company(company, filings, relationships)
        self._cache[cache_key] = assessment
        return assessment

    def assess_multiple(self, companies: list[Company]) -> list[RiskAssessment]:
        """Assess risk for multiple companies.

        Args:
            companies: List of Company instances.

        Returns:
            List of RiskAssessment instances.
        """
        return [self.assess(c) for c in companies]

    def compare_risk(self, assessments: list[RiskAssessment]) -> dict[str, Any]:
        """Compare risk assessments across companies.

        Args:
            assessments: List of RiskAssessment instances.

        Returns:
            Dictionary with comparison data.
        """
        if not assessments:
            return {"error": "No assessments provided"}

        sorted_assessments = sorted(assessments, key=lambda a: a.overall_score, reverse=True)

        return {
            "highest_risk": sorted_assessments[0].to_dict(),
            "lowest_risk": sorted_assessments[-1].to_dict(),
            "average_score": sum(a.overall_score for a in assessments) / len(assessments),
            "companies": [a.to_dict() for a in sorted_assessments],
        }

    def _assess_company(
        self,
        company: Company,
        filings: Optional[list[Filing]],
        relationships: Optional[list[Relationship]],
    ) -> RiskAssessment:
        """Internal method to assess a single company's risk."""
        assessment = RiskAssessment(
            company_name=company.name,
            ticker=company.ticker,
            cik=company.cik,
            last_updated="now",
        )

        # Evaluate risk factors
        factors = []

        # 1. Litigation Risk
        litigation_score = self._evaluate_litigation_risk(company, filings)
        factors.append(RiskFactor(
            name="Litigation Risk",
            score=litigation_score["score"],
            weight=0.20,
            description=litigation_score["description"],
            evidence=litigation_score["evidence"],
        ))

        # 2. Financial Risk
        financial_score = self._evaluate_financial_risk(company, filings)
        factors.append(RiskFactor(
            name="Financial Risk",
            score=financial_score["score"],
            weight=0.25,
            description=financial_score["description"],
            evidence=financial_score["evidence"],
        ))

        # 3. Regulatory Risk
        regulatory_score = self._evaluate_regulatory_risk(company, filings)
        factors.append(RiskFactor(
            name="Regulatory Risk",
            score=regulatory_score["score"],
            weight=0.15,
            description=regulatory_score["description"],
            evidence=regulatory_score["evidence"],
        ))

        # 4. Operational Risk
        operational_score = self._evaluate_operational_risk(company, filings)
        factors.append(RiskFactor(
            name="Operational Risk",
            score=operational_score["score"],
            weight=0.15,
            description=operational_score["description"],
            evidence=operational_score["evidence"],
        ))

        # 5. Reputational Risk
        reputational_score = self._evaluate_reputational_risk(company, relationships)
        factors.append(RiskFactor(
            name="Reputational Risk",
            score=reputational_score["score"],
            weight=0.10,
            description=reputational_score["description"],
            evidence=reputational_score["evidence"],
        ))

        # 6. Compliance Risk
        compliance_score = self._evaluate_compliance_risk(company, filings)
        factors.append(RiskFactor(
            name="Compliance Risk",
            score=compliance_score["score"],
            weight=0.15,
            description=compliance_score["description"],
            evidence=compliance_score["evidence"],
        ))

        assessment.factors = factors

        # Calculate composite risk score
        assessment.overall_score = sum(f.weighted_score() for f in factors) / sum(f.weight for f in factors)

        # Determine risk level
        assessment.risk_level = self._get_risk_level(assessment.overall_score)

        # Generate recommendations
        assessment.recommendations = self._generate_recommendations(factors)

        # Determine trend (simplified — in production, compare with historical data)
        assessment.trend = self._determine_trend(factors)

        return assessment

    def _evaluate_litigation_risk(
        self,
        company: Company,
        filings: Optional[list[Filing]],
    ) -> dict:
        """Evaluate litigation risk."""
        score = 0
        evidence = []
        description = "No significant litigation risk identified"

        if filings:
            for filing in filings:
                # Check for litigation mentions in metadata
                if filing.metadata and "raw_filing" in filing.metadata:
                    raw = filing.metadata["raw_filing"]
                    if isinstance(raw, dict):
                        # Look for litigation indicators
                        legal_proceedings = raw.get("legal_proceedings", [])
                        if isinstance(legal_proceedings, list) and legal_proceedings:
                            score += 20
                            evidence.append(f"Found {len(legal_proceedings)} legal proceedings in {filing.accession_number}")

                        lawsuits = raw.get("lawsuits", [])
                        if isinstance(lawsuits, list) and lawsuits:
                            score += 15
                            evidence.append(f"Found {len(lawsuits)} lawsuits in {filing.accession_number}")

                        # Check for contingent liabilities
                        contingent = raw.get("contingent_liabilities", 0) or 0
                        if contingent > 1000000:  # > $1M
                            score += 10
                            evidence.append(f"Contingent liabilities: ${contingent:,.0f}")

        # Check company metadata for litigation history
        if company.metadata and "litigation_history" in company.metadata:
            lit_history = company.metadata["litigation_history"]
            if isinstance(lit_history, list):
                score += len(lit_history) * 5
                evidence.append(f"Litigation history: {len(lit_history)} past cases")

        score = min(score, 100)
        description = f"Litigation risk score: {score}/100"
        if score > 50:
            description += " — High litigation exposure"
        elif score > 25:
            description += " — Moderate litigation exposure"

        return {"score": score, "description": description, "evidence": evidence}

    def _evaluate_financial_risk(
        self,
        company: Company,
        filings: Optional[list[Filing]],
    ) -> dict:
        """Evaluate financial risk."""
        score = 0
        evidence = []
        description = "Financial risk score: 0/100"

        if filings:
            for filing in filings:
                if filing.metadata and "raw_filing" in filing.metadata:
                    raw = filing.metadata["raw_filing"]
                    if isinstance(raw, dict):
                        # Check for bankruptcy indicators
                        bankruptcy = raw.get("bankruptcy_filed", False)
                        if bankruptcy:
                            score += 50
                            evidence.append("Bankruptcy filing detected")

                        # Check for going concern warnings
                        going_concern = raw.get("going_concern_warning", False)
                        if going_concern:
                            score += 30
                            evidence.append("Going concern warning present")

                        # Check debt levels
                        total_debt = raw.get("total_debt", 0) or 0
                        total_equity = raw.get("total_equity", 0) or 0
                        if total_equity > 0 and total_debt / total_equity > 2.0:
                            score += 15
                            evidence.append(f"High debt-to-equity ratio: {total_debt/total_equity:.2f}")

                        # Check for negative cash flow
                        operating_cash = raw.get("operating_cash_flow", 0) or 0
                        if operating_cash < 0:
                            score += 10
                            evidence.append("Negative operating cash flow")

        score = min(score, 100)
        description = f"Financial risk score: {score}/100"
        if score > 50:
            description += " — High financial risk"
        elif score > 25:
            description += " — Moderate financial risk"

        return {"score": score, "description": description, "evidence": evidence}

    def _evaluate_regulatory_risk(
        self,
        company: Company,
        filings: Optional[list[Filing]],
    ) -> dict:
        """Evaluate regulatory risk."""
        score = 0
        evidence = []
        description = "No significant regulatory risk identified"

        if filings:
            for filing in filings:
                if filing.metadata and "raw_filing" in filing.metadata:
                    raw = filing.metadata["raw_filing"]
                    if isinstance(raw, dict):
                        # Check for regulatory actions
                        regulatory_actions = raw.get("regulatory_actions", [])
                        if isinstance(regulatory_actions, list) and regulatory_actions:
                            score += 25
                            evidence.append(f"Found {len(regulatory_actions)} regulatory actions")

                        # Check for fines/penalties
                        fines = raw.get("fines_penalties", 0) or 0
                        if fines > 0:
                            score += 15
                            evidence.append(f"Regulatory fines/penalties: ${fines:,.0f}")

                        # Check for consent decrees
                        consent_decrees = raw.get("consent_decrees", [])
                        if isinstance(consent_decrees, list) and consent_decrees:
                            score += 20
                            evidence.append(f"Found {len(consent_decrees)} consent decrees")

        # Check company metadata
        if company.metadata and "regulatory_history" in company.metadata:
            reg_history = company.metadata["regulatory_history"]
            if isinstance(reg_history, list):
                score += len(reg_history) * 5
                evidence.append(f"Regulatory history: {len(reg_history)} past actions")

        score = min(score, 100)
        description = f"Regulatory risk score: {score}/100"
        if score > 50:
            description += " — High regulatory risk"
        elif score > 25:
            description += " — Moderate regulatory risk"

        return {"score": score, "description": description, "evidence": evidence}

    def _evaluate_operational_risk(
        self,
        company: Company,
        filings: Optional[list[Filing]],
    ) -> dict:
        """Evaluate operational risk."""
        score = 0
        evidence = []
        description = "No significant operational risk identified"

        if filings:
            for filing in filings:
                if filing.metadata and "raw_filing" in filing.metadata:
                    raw = filing.metadata["raw_filing"]
                    if isinstance(raw, dict):
                        # Check for operational issues
                        operational_issues = raw.get("operational_issues", [])
                        if isinstance(operational_issues, list) and operational_issues:
                            score += 15
                            evidence.append(f"Found {len(operational_issues)} operational issues")

                        # Check for supply chain risks
                        supply_chain = raw.get("supply_chain_risks", [])
                        if isinstance(supply_chain, list) and supply_chain:
                            score += 10
                            evidence.append(f"Supply chain risks identified: {len(supply_chain)}")

                        # Check for key person dependency
                        key_person = raw.get("key_person_dependency", False)
                        if key_person:
                            score += 10
                            evidence.append("Key person dependency identified")

        score = min(score, 100)
        description = f"Operational risk score: {score}/100"
        if score > 50:
            description += " — High operational risk"
        elif score > 25:
            description += " — Moderate operational risk"

        return {"score": score, "description": description, "evidence": evidence}

    def _evaluate_reputational_risk(
        self,
        company: Company,
        relationships: Optional[list[Relationship]],
    ) -> dict:
        """Evaluate reputational risk."""
        score = 0
        evidence = []
        description = "No significant reputational risk identified"

        if relationships:
            # Check for relationships with high-risk entities
            high_risk_types = ["sanctioned_entity", "fraudulent_entity", "blacklisted_entity"]
            for rel in relationships:
                if rel.target_type in high_risk_types or rel.source_type in high_risk_types:
                    score += 20
                    evidence.append(f"Relationship with high-risk entity: {rel.target_name or rel.source_name}")

            # Check for controversial relationships
            controversial_types = ["lobbyist", "politically_exposed_person"]
            for rel in relationships:
                if rel.target_type in controversial_types or rel.source_type in controversial_types:
                    score += 10
                    evidence.append(f"Relationship with controversial entity: {rel.target_name or rel.source_name}")

        score = min(score, 100)
        description = f"Reputational risk score: {score}/100"
        if score > 50:
            description += " — High reputational risk"
        elif score > 25:
            description += " — Moderate reputational risk"

        return {"score": score, "description": description, "evidence": evidence}

    def _evaluate_compliance_risk(
        self,
        company: Company,
        filings: Optional[list[Filing]],
    ) -> dict:
        """Evaluate compliance risk."""
        score = 0
        evidence = []
        description = "No significant compliance risk identified"

        if filings:
            for filing in filings:
                if filing.metadata and "raw_filing" in filing.metadata:
                    raw = filing.metadata["raw_filing"]
                    if isinstance(raw, dict):
                        # Check for compliance violations
                        violations = raw.get("compliance_violations", [])
                        if isinstance(violations, list) and violations:
                            score += 20
                            evidence.append(f"Found {len(violations)} compliance violations")

                        # Check for internal controls weaknesses
                        internal_controls = raw.get("internal_controls_weakness", False)
                        if internal_controls:
                            score += 15
                            evidence.append("Internal controls weakness identified")

                        # Check for audit qualifications
                        audit_qualification = raw.get("audit_qualification", False)
                        if audit_qualification:
                            score += 10
                            evidence.append("Audit qualification present")

        score = min(score, 100)
        description = f"Compliance risk score: {score}/100"
        if score > 50:
            description += " — High compliance risk"
        elif score > 25:
            description += " — Moderate compliance risk"

        return {"score": score, "description": description, "evidence": evidence}

    def _get_risk_level(self, score: float) -> str:
        """Get risk level from score."""
        for level, (low, high) in self.RISK_LEVELS.items():
            if low <= score < high:
                return level
        return "critical"

    def _generate_recommendations(self, factors: list[RiskFactor]) -> list[str]:
        """Generate recommendations based on risk factors."""
        recommendations = []

        for factor in factors:
            if factor.score > 50:
                if "Litigation" in factor.name:
                    recommendations.append("Review litigation strategy and consider legal counsel")
                elif "Financial" in factor.name:
                    recommendations.append("Assess financial health and consider debt restructuring")
                elif "Regulatory" in factor.name:
                    recommendations.append("Enhance regulatory compliance programs")
                elif "Operational" in factor.name:
                    recommendations.append("Review operational processes and risk mitigation")
                elif "Reputational" in factor.name:
                    recommendations.append("Evaluate public relations and stakeholder communications")
                elif "Compliance" in factor.name:
                    recommendations.append("Strengthen compliance monitoring and reporting")

        if not recommendations:
            recommendations.append("Continue monitoring — no immediate action required")

        return recommendations

    def _determine_trend(self, factors: list[RiskFactor]) -> str:
        """Determine risk trend (simplified)."""
        avg_score = sum(f.score for f in factors) / len(factors) if factors else 0

        if avg_score > 60:
            return "deteriorating"
        elif avg_score < 30:
            return "improving"
        else:
            return "stable"

    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()
