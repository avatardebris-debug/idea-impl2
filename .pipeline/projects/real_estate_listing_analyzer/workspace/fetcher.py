"""
real_estate_listing_analyzer/fetcher.py
Adapters for public/RapidAPI real estate data sources.
"""
from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any

CACHE_DIR = pathlib.Path.home() / ".real_estate_cache"


@dataclass
class Listing:
    """Normalised property listing."""
    zpid: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    bedrooms: int = 0
    bathrooms: float = 0.0
    sqft: int = 0
    price: int = 0
    price_per_sqft: float = 0.0
    days_on_market: int = 0
    list_date: str = ""
    home_type: str = ""
    lat: float = 0.0
    lon: float = 0.0
    zestimate: int = 0
    price_history: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


def _get(url: str, headers: dict | None = None, timeout: int = 15) -> dict:
    """Simple urllib GET → dict."""
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class ZillowFetcher:
    """
    Fetches listings via the Zillow RapidAPI endpoint.
    Requires env var: RAPIDAPI_KEY
    """
    BASE = "https://zillow-com1.p.rapidapi.com"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("RAPIDAPI_KEY", "")
        if not self.api_key:
            raise EnvironmentError(
                "RAPIDAPI_KEY not set. "
                "Get a key at https://rapidapi.com/apimaker/api/zillow-com1"
            )
        self._headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com",
        }

    def search_by_zip(self, zip_code: str, count: int = 40) -> list[Listing]:
        """Search listings for a ZIP code."""
        url = (
            f"{self.BASE}/propertyExtendedSearch"
            f"?location={zip_code}&home_type=Houses&resultsPerPage={min(count, 40)}"
        )
        data = _get(url, headers=self._headers)
        return [self._parse(p) for p in data.get("props", [])]

    def _parse(self, raw: dict) -> Listing:
        price = raw.get("price", 0) or 0
        sqft  = raw.get("livingArea", 0) or 0
        return Listing(
            zpid=str(raw.get("zpid", "")),
            address=raw.get("streetAddress", ""),
            city=raw.get("city", ""),
            state=raw.get("state", ""),
            zip_code=raw.get("zipcode", ""),
            bedrooms=int(raw.get("bedrooms", 0) or 0),
            bathrooms=float(raw.get("bathrooms", 0) or 0),
            sqft=int(sqft),
            price=int(price),
            price_per_sqft=round(price / sqft, 2) if sqft else 0.0,
            days_on_market=int(raw.get("daysOnZillow", 0) or 0),
            home_type=raw.get("homeType", ""),
            lat=float(raw.get("latitude", 0) or 0),
            lon=float(raw.get("longitude", 0) or 0),
            zestimate=int(raw.get("zestimate", 0) or 0),
            raw=raw,
        )


class HUDFetcher:
    """
    Fetches Fair Market Rents from HUD API (free, no key required).
    https://www.huduser.gov/portal/datasets/fmr.html
    """
    BASE = "https://www.huduser.gov/hudapi/public/fmr"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("HUD_API_KEY", "")

    def get_fmr(self, zip_code: str, year: int = 2024) -> dict:
        """Return Fair Market Rent data for a ZIP code."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.BASE}/listCounties/{zip_code[:2]}?year={year}"
        try:
            return _get(url, headers=headers)
        except Exception:
            return {}


def save_cache(slug: str, data: list[dict]) -> pathlib.Path:
    """Persist fetched listings to local JSON cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{slug}_{int(time.time())}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_latest_cache(zip_code: str) -> list[dict] | None:
    """Load most recent cached result for a zip code."""
    if not CACHE_DIR.exists():
        return None
    slug = f"{zip_code}_"
    candidates = sorted(
        [p for p in CACHE_DIR.iterdir() if p.name.startswith(slug)],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception:
        return None
