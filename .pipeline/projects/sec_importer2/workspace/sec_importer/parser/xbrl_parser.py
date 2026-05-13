"""XBRL/iXBRL parser for SEC EDGAR filings.

Downloads and parses XBRL instance documents from SEC filings to extract
financial facts (revenue, net income, EPS, etc.) in a structured format.
"""

from __future__ import annotations

import io
import json
import logging
import re
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class XBRLParser:
    """Parse XBRL/iXBRL instance documents from SEC filings.

    The SEC provides XBRL instance documents (usually .xml files) for
    filings that include them (e.g., 10-K, 10-Q). This parser extracts
    key financial facts from the XBRL data.
    """

    # Common XBRL taxonomy concepts we care about (20+ financial metrics)
    KEY_CONCEPTS = {
        # ── Income Statement ──────────────────────────────────────────────
        "revenue": [
            "us-gaap_Revenue",
            "us-gaap_SalesRevenueNet",
            "us-gaap_NetSalesRevenue",
            "us-gaap_RevenueFromContractWithCustomerNet",
            "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
        ],
        "cost_of_revenue": [
            "us-gaap_CostOfGoodsAndServicesSold",
            "us-gaap_CostOfRevenue",
            "us-gaap_CostOfProductsSold",
            "us-gaap_CostOfServices",
        ],
        "gross_profit": [
            "us-gaap_GrossProfit",
            "us-gaap_GrossProfitMargin",
        ],
        "operating_expenses": [
            "us-gaap_OperatingExpenses",
            "us-gaap_OperatingExpensesAbstract",
        ],
        "selling_general_and_administrative_expenses": [
            "us-gaap_SellingGeneralAndAdministrativeExpense",
            "us-gaap_SellingAndMarketingExpense",
            "us-gaap_GeneralAndAdministrativeExpense",
        ],
        "research_and_development_expense": [
            "us-gaap_ResearchAndDevelopmentExpense",
            "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcess",
        ],
        "operating_income": [
            "us-gaap_OperatingIncomeLoss",
            "us-gaap_IncomeFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        ],
        "interest_expense": [
            "us-gaap_InterestExpense",
            "us-gaap_InterestExpenseDebt",
            "us-gaap_InterestExpenseOperatingLease",
        ],
        "interest_income": [
            "us-gaap_InvestmentIncomeInterest",
            "us-gaap_InterestIncome",
            "us-gaap_InterestIncomeOperatingLease",
        ],
        "other_income_expense": [
            "us-gaap_OtherNonoperatingIncomeExpense",
            "us-gaap_OtherNonoperatingIncomeExpenseNet",
            "us-gaap_GainLossOnExtinguishmentOfDebt",
        ],
        "income_before_tax": [
            "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            "us-gaap_IncomeFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        ],
        "income_tax_expense": [
            "us-gaap_IncomeTaxExpenseBenefit",
            "us-gaap_ProvisionForIncomeTax",
            "us-gaap_IncomeTaxExpenseBenefitContinuingOperations",
        ],
        "net_income": [
            "us-gaap_NetIncomeLoss",
            "us-gaap_NetIncome",
            "us-gaap_NetIncomeLossAvailableToCommonStockholdersBasic",
            "us-gaap_EarningsPerShareAccumulatedOtherComprehensiveIncome",
        ],
        "net_income_noncontrolling_interest": [
            "us-gaap_NetIncomeLossNoncontrollingInterest",
        ],
        "net_income_controlling_interest": [
            "us-gaap_NetIncomeLossControllingInterest",
        ],
        "comprehensive_income": [
            "us-gaap_ComprehensiveIncomeNetOfTax",
            "us-gaap_ComprehensiveIncomeNetOfTaxIncludingPortionAttributableToNoncontrollingInterest",
        ],
        "basic_eps": [
            "us-gaap_EarningsPerShareBasic",
            "us-gaap_IncomeStatementTextBlock",
        ],
        "diluted_eps": [
            "us-gaap_EarningsPerShareDiluted",
            "us-gaap_IncomeStatementTextBlockDiluted",
        ],
        "weighted_average_shares_outstanding_basic": [
            "us-gaap_WeightedAverageNumberOfShareOutstandingBasic",
        ],
        "weighted_average_shares_outstanding_diluted": [
            "us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding",
        ],
        # ── Balance Sheet ─────────────────────────────────────────────────
        "total_assets": [
            "us-gaap_Assets",
            "us-gaap_AssetsAbstract",
        ],
        "current_assets": [
            "us-gaap_AssetsCurrent",
            "us-gaap_AssetsCurrentAbstract",
        ],
        "cash_and_equivalents": [
            "us-gaap_CashAndCashEquivalentsPeriodIncreaseDecrease",
            "us-gaap_CashAndCashEquivalents",
            "us-gaap_CashAndCashEquivalentsAtCarryingValue",
        ],
        "short_term_investments": [
            "us-gaap_ShortTermInvestments",
            "us-gaap_ShortTermInvestmentsCurrent",
        ],
        "accounts_receivable_net": [
            "us-gaap_AccountsReceivableNetCurrent",
            "us-gaap_AccountsReceivableNet",
            "us-gaap_AccountsReceivableNetCurrentAndNoncurrent",
        ],
        "inventory_net": [
            "us-gaap_InventoryNet",
            "us-gaap_InventoryNetCurrent",
        ],
        "prepaid_expenses_and_other_assets": [
            "us-gaap_PrepaidExpenseAndOtherAssetsCurrent",
            "us-gaap_PrepaidExpenseAndOtherAssets",
        ],
        "property_plant_equipment_net": [
            "us-gaap_PropertyPlantAndEquipmentNet",
            "us-gaap_PropertyPlantAndEquipmentNetCurrentAndNoncurrent",
        ],
        "goodwill": [
            "us-gaap_Goodwill",
            "us-gaap_GoodwillAndOtherIntangibleAssetsNet",
        ],
        "intangible_assets_net": [
            "us-gaap_IntangibleAssetsNetExcludingGoodwill",
            "us-gaap_IntangibleAssetsNetExcludingGoodwillCurrentAndNoncurrent",
        ],
        "other_long_term_assets": [
            "us-gaap_OtherAssetsNoncurrent",
            "us-gaap_OtherAssets",
        ],
        "total_liabilities": [
            "us-gaap_Liabilities",
            "us-gaap_LiabilitiesAbstract",
        ],
        "current_liabilities": [
            "us-gaap_LiabilitiesCurrent",
            "us-gaap_LiabilitiesCurrentAbstract",
        ],
        "accounts_payable": [
            "us-gaap_AccountsPayableCurrent",
            "us-gaap_AccountsPayable",
        ],
        "accrued_liabilities": [
            "us-gaap_AccruedLiabilitiesCurrent",
            "us-gaap_AccruedLiabilities",
        ],
        "short_term_debt": [
            "us-gaap_LongTermDebtCurrent",
            "us-gaap_ShortTermBorrowings",
            "us-gaap_CurrentPortionOfLongTermDebt",
        ],
        "current_portion_long_term_debt": [
            "us-gaap_CurrentPortionOfLongTermDebt",
            "us-gaap_CurrentPortionOfLongTermDebtAndCapitalLeaseObligations",
        ],
        "long_term_debt": [
            "us-gaap_LongTermDebtNoncurrent",
            "us-gaap_LongTermDebt",
            "us-gaap_LongTermDebtNoncurrentExcludingCurrentPortion",
        ],
        "deferred_revenue": [
            "us-gaap_ContractWithCustomerLiabilityDeferredRevenue",
            "us-gaap_ContractWithCustomerLiabilityDeferredRevenueCurrent",
            "us-gaap_ContractWithCustomerLiabilityDeferredRevenueNoncurrent",
        ],
        "other_long_term_liabilities": [
            "us-gaap_OtherLiabilitiesNoncurrent",
            "us-gaap_OtherLiabilities",
        ],
        "total_equity": [
            "us-gaap_StockholdersEquity",
            "us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ],
        "retained_earnings": [
            "us-gaap_RetainedEarningsAccumulatedDeficit",
            "us-gaap_RetainedEarnings",
        ],
        "common_stock": [
            "us-gaap_CommonStockValue",
            "us-gaap_CommonStockValueIncludingAdditionalPaidInCapital",
        ],
        # ── Cash Flow Statement ───────────────────────────────────────────
        "operating_cash_flow": [
            "us-gaap_NetCashProvidedByUsedInContinuingOperations",
            "us-gaap_NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
            "us-gaap_NetCashProvidedByUsedInOperatingActivities",
        ],
        "investing_cash_flow": [
            "us-gaap_NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
            "us-gaap_NetCashProvidedByUsedInInvestingActivities",
        ],
        "financing_cash_flow": [
            "us-gaap_NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
            "us-gaap_NetCashProvidedByUsedInFinancingActivities",
        ],
        "capital_expenditures": [
            "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
            "us-gaap_PaymentsToAcquirePropertyPlantAndEquipmentAndIntangibleAssets",
        ],
        "free_cash_flow": [
            "us-gaap_FreeCashFlow",
        ],
        # ── Other / Derived ───────────────────────────────────────────────
        "effective_tax_rate": [
            "us-gaap_EffectiveIncomeTaxRateContinuingOperations",
            "us-gaap_EffectiveIncomeTaxRateReconciliationIncomeTaxExpenseBenefit",
        ],
        "ebitda": [
            "us-gaap_EarningsBeforeInterestTaxesDepreciationAndAmortization",
            "us-gaap_EarningsBeforeInterestTaxesDepreciationAndAmortizationNoncontrollingInterest",
        ],
        "depreciation_and_amortization": [
            "us-gaap_DepreciationDepletionAndAmortization",
            "us-gaap_DepreciationDepletionAndAmortizationIncomeStatement",
        ],
        "operating_lease_liability": [
            "us-gaap_OperatingLeaseLiability",
            "us-gaap_OperatingLeaseLiabilityCurrent",
            "us-gaap_OperatingLeaseLiabilityNoncurrent",
        ],
        "finance_lease_liability": [
            "us-gaap_FinanceLeaseLiability",
            "us-gaap_FinanceLeaseLiabilityCurrent",
            "us-gaap_FinanceLeaseLiabilityNoncurrent",
        ],
    }

    def __init__(self, timeout: int = 60):
        """Initialize the XBRL parser.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self._session = httpx.Client(
            headers={
                "User-Agent": "SECImporter/0.1.0 (contact: sec-importer@example.com)",
                "Accept": "application/xml, text/xml, */*",
            },
            timeout=self.timeout,
        )

    def parse_from_url(self, url: str) -> dict[str, Any]:
        """Download and parse XBRL data from a URL.

        Args:
            url: URL to the XBRL instance document.

        Returns:
            Dict of extracted financial facts.
        """
        try:
            response = self._session.get(url)
            response.raise_for_status()
            return self.parse_xbrl(response.text)
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch XBRL from {url}: {e}")
            return {"error": str(e), "status": "failed"}

    def parse_xbrl(self, xml_content: str) -> dict[str, Any]:
        """Parse XBRL XML content and extract financial facts.

        Args:
            xml_content: Raw XBRL XML string.

        Returns:
            Dict of extracted financial facts with concept names as keys.
        """
        if not xml_content or not xml_content.strip():
            return {"error": "Empty XBRL content", "status": "failed"}

        try:
            soup = BeautifulSoup(xml_content, "xml")
        except Exception as e:
            logger.error(f"Failed to parse XBRL XML: {e}")
            return {"error": f"XML parse error: {e}", "status": "failed"}

        facts = self._extract_facts(soup)
        key_metrics = self._extract_key_metrics(facts)

        result = {
            "status": "success",
            "total_facts": len(facts),
            "key_metrics": key_metrics,
            "all_facts": facts,
        }

        logger.info(f"XBRL parsed: {len(facts)} facts, {len(key_metrics)} key metrics")
        return result

    def _extract_facts(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract all XBRL facts from the parsed XML.

        Args:
            soup: Parsed BeautifulSoup object.

        Returns:
            Dict mapping concept names to their values and metadata.
        """
        facts = {}
        nsmap = {
            "xbrli": "http://www.xbrl.org/2003/instance",
            "xbrldt": "http://xbrl.org/2005/xbrldt",
            "link": "http://www.xbrl.org/2003/linkbase",
        }

        # Find all concept elements (they have a namespace)
        for elem in soup.find_all(True):
            tag = elem.name
            # XBRL facts are typically in the xbrli namespace
            if "xbrli" in tag.lower() or elem.get("contextRef") or elem.get("unitRef"):
                concept = self._get_concept_name(elem)
                if concept:
                    value = self._get_fact_value(elem)
                    if value is not None:
                        facts[concept] = {
                            "value": value,
                            "unit": elem.get("unitRef", ""),
                            "context": elem.get("contextRef", ""),
                            "start_date": self._get_context_start(elem, soup),
                            "end_date": self._get_context_end(elem, soup),
                            "label": self._get_fact_label(elem, soup),
                        }

        return facts

    def _get_concept_name(self, elem) -> Optional[str]:
        """Extract the concept name from an XBRL element."""
        # Try to get the local name (after namespace prefix)
        tag = elem.name
        if "}" in tag:
            return tag.split("}")[-1]
        return tag

    def _get_fact_value(self, elem) -> Optional[Any]:
        """Extract the text value from an XBRL fact element."""
        text = elem.get_text(strip=True)
        if not text:
            return None
        # Try to convert to number
        try:
            return float(text)
        except ValueError:
            return text

    def _get_context_start(self, elem, soup: BeautifulSoup) -> Optional[str]:
        """Get the start date from the context of an XBRL fact."""
        context_ref = elem.get("contextRef")
        if not context_ref:
            return None
        context = soup.find("context", {"id": context_ref})
        if context:
            start = context.find("xbrli:startDate", namespaces={"xbrli": "http://www.xbrl.org/2003/instance"})
            if start:
                return start.get_text(strip=True)
            # Try without namespace
            start = context.find("startDate")
            if start:
                return start.get_text(strip=True)
        return None

    def _get_context_end(self, elem, soup: BeautifulSoup) -> Optional[str]:
        """Get the end date from the context of an XBRL fact."""
        context_ref = elem.get("contextRef")
        if not context_ref:
            return None
        context = soup.find("context", {"id": context_ref})
        if context:
            end = context.find("xbrli:endDate", namespaces={"xbrli": "http://www.xbrl.org/2003/instance"})
            if end:
                return end.get_text(strip=True)
            end = context.find("endDate")
            if end:
                return end.get_text(strip=True)
        return None

    def _get_fact_label(self, elem, soup: BeautifulSoup) -> Optional[str]:
        """Get the human-readable label for an XBRL fact from the linkbase."""
        concept = self._get_concept_name(elem)
        if not concept:
            return None

        # Look for label in linkbase
        for label_elem in soup.find_all("link:label"):
            if label_elem.get("conceptName") == concept:
                return label_elem.get_text(strip=True)

        return None

    def _extract_key_metrics(self, facts: dict[str, Any]) -> dict[str, Any]:
        """Extract key financial metrics from all facts.

        Args:
            facts: Dict of all XBRL facts.

        Returns:
            Dict of key financial metrics.
        """
        metrics = {}

        for metric_name, concept_list in self.KEY_CONCEPTS.items():
            for concept in concept_list:
                if concept in facts:
                    value = facts[concept]["value"]
                    if isinstance(value, (int, float)):
                        metrics[metric_name] = {
                            "value": value,
                            "unit": facts[concept].get("unit", ""),
                            "start_date": facts[concept].get("start_date"),
                            "end_date": facts[concept].get("end_date"),
                            "label": facts[concept].get("label", concept),
                            "source_concept": concept,
                        }
                        break  # Use first matching concept

        return metrics

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
