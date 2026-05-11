"""Corporate registry data source — queries public corporate registries."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from osint_corp.models.entities import Company

logger = logging.getLogger(__name__)


class CorporateRegistry:
    """Queries public corporate registry data sources."""

    def __init__(self, user_agent: str = "osint-corp/0.1.0"):
        self.user_agent = user_agent
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=30.0,
        )

    def search_by_name(
        self,
        name: str,
        jurisdiction: Optional[str] = None,
        limit: int = 10,
    ) -> list[Company]:
        """Search for companies by name across public registries.

        Args:
            name: Company name to search for.
            jurisdiction: Optional jurisdiction filter (e.g., 'US-DE' for Delaware).
            limit: Maximum number of results.

        Returns:
            List of Company model instances.
        """
        results = []

        # Try OpenCorporates API (public, no key required for basic usage)
        oc_results = self._search_opencorporates(name, jurisdiction, limit)
        results.extend(oc_results)

        # If jurisdiction is US, also try state Secretary of State APIs
        if jurisdiction and jurisdiction.startswith("US-"):
            state = jurisdiction.split("-")[1]
            sos_results = self._search_sos(name, state, limit - len(results))
            results.extend(sos_results)

        return results[:limit]

    def search_by_cik(self, cik: str) -> Optional[Company]:
        """Look up a company by SEC CIK number."""
        url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
        try:
            response = self._client.get(url)
            response.raise_for_status()
            data = response.json()

            company = Company(
                name=data.get("companyName", "Unknown"),
                ticker=data.get("tickers", [""])[0] if data.get("tickers") else None,
                cik=cik,
                jurisdiction="US",
                industry=data.get("insiderTransactionForOwnerExists", False) and "public" or "unknown",
                sic_code=data.get("sic"),
                source="sec_edgar",
                metadata={"cik_submissions_url": data.get("cik_submissions_url")},
            )
            logger.info(f"Found company via CIK: {company.name}")
            return company
        except httpx.HTTPError as e:
            logger.error(f"CIK lookup failed for {cik}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during CIK lookup: {e}")
            return None

    def _search_opencorporates(
        self,
        name: str,
        jurisdiction: Optional[str],
        limit: int,
    ) -> list[Company]:
        """Search OpenCorporates API for companies."""
        results = []
        try:
            params = {"q": name, "limit": limit}
            if jurisdiction:
                params["jurisdiction_code"] = jurisdiction

            response = self._client.get(
                "https://api.opencorporates.com/companies/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            companies = data.get("results", {}).get("companies", [])
            for comp in companies:
                company_data = comp.get("company", {})
                results.append(Company(
                    name=company_data.get("name", "Unknown"),
                    ticker=company_data.get("ticker"),
                    jurisdiction=company_data.get("jurisdiction_code"),
                    registration_number=company_data.get("company_number"),
                    incorporation_date=company_data.get("incorporation_date"),
                    status=company_data.get("status"),
                    industry=company_data.get("industry_code"),
                    source="opencorporates",
                    metadata={
                        "oc_id": comp.get("id"),
                        "url": company_data.get("url"),
                    },
                ))
        except httpx.HTTPError as e:
            logger.warning(f"OpenCorporates search failed: {e}")
        except Exception as e:
            logger.warning(f"OpenCorporates search error: {e}")

        return results

    def _search_sos(
        self,
        name: str,
        state: str,
        limit: int,
    ) -> list[Company]:
        """Search a state Secretary of State business registry.

        Note: This is a simplified implementation. Real implementations
        would need to handle different state API formats.
        """
        results = []
        # State SOS API endpoints (some states have public APIs)
        sos_endpoints = {
            "DE": "https://corp.delaware.gov/",
            "CA": "https://bizfileonline.sos.ca.gov/",
            "NY": "https://dos.ny.gov/business-filing-system",
            "TX": "https://direct.sos.texas.gov/",
            "FL": "https://dos.myflorida.com/",
        }

        if state not in sos_endpoints:
            logger.warning(f"No SOS API configured for state {state}")
            return results

        # For MVP, we note that SOS APIs typically require web scraping
        # or specific API keys. We return a placeholder.
        logger.info(f"SOS search for '{name}' in {state} — API at {sos_endpoints[state]}")
        return results

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class RegistryError(Exception):
    """Exception raised when registry query fails."""
    pass
