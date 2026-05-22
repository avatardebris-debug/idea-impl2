"""
sources/pubmed.py — PubMed/NCBI search via the E-utilities REST API (no key required).

API docs: https://www.ncbi.nlm.nih.gov/books/NBK25497/
Rate limit: 3 req/s without key, 10 req/s with NCBI_API_KEY env var.
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from research1.sources.arxiv import Result

_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_HEADERS = {"User-Agent": "research1/0.1 (contact: research1@example.com)"}


def _api_params() -> dict:
    params: dict = {"retmode": "json"}
    key = os.environ.get("NCBI_API_KEY")
    if key:
        params["api_key"] = key
    return params


def search(query: str, max_results: int = 5, timeout: int = 15) -> list[Result]:
    """Search PubMed and return up to max_results article summaries."""
    # Step 1: esearch — get PMIDs
    params = _api_params()
    params.update({
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "relevance",
    })
    search_url = f"{_ESEARCH}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(search_url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pmids = data.get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []

    if not pmids:
        return []

    time.sleep(0.35)  # respect rate limit

    # Step 2: efetch — get abstracts in XML
    fetch_params = _api_params()
    fetch_params.update({
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    })
    fetch_url = f"{_EFETCH}?{urllib.parse.urlencode(fetch_params)}"
    try:
        req = urllib.request.Request(fetch_url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_text = resp.read().decode("utf-8")
    except Exception:
        return []

    return _parse_pubmed_xml(xml_text)


def _parse_pubmed_xml(xml_text: str) -> list[Result]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    results: list[Result] = []
    for article in root.findall(".//PubmedArticle"):
        medline = article.find(".//MedlineCitation")
        if medline is None:
            continue

        pmid_el   = medline.find(".//PMID")
        title_el  = medline.find(".//ArticleTitle")
        abs_texts = medline.findall(".//AbstractText")

        pmid    = pmid_el.text if pmid_el is not None else ""
        title   = _clean(_el_text(title_el))
        abstract = " ".join(_clean(_el_text(el)) for el in abs_texts if el.text)

        # Authors
        authors = []
        for au in medline.findall(".//Author")[:5]:
            last  = au.findtext("LastName", "")
            first = au.findtext("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())

        # Published date
        pub_date = medline.find(".//PubDate")
        year  = (pub_date.findtext("Year",  "") if pub_date is not None else "")
        month = (pub_date.findtext("Month", "") if pub_date is not None else "")
        published = f"{year}-{month}" if month else year

        results.append(Result(
            source="pubmed",
            title=title,
            authors=authors,
            abstract=abstract[:1500],
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            published=published,
            relevance_score=1.0,
        ))
    return results


def _el_text(el) -> str:
    if el is None:
        return ""
    return "".join(el.itertext())


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()) if text else ""
