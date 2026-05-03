"""Scraper for Scott Adams' blog at scottadamsslog.com.

Fetches blog post pages, extracts title, date, and body text.
Handles pagination to collect multiple posts.
"""

import os
import re
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://scottadamsslog.com"
MAX_POSTS = 200  # Number of posts to scrape per run


def fetch_page(url: str, timeout: int = 30) -> Optional[requests.Response]:
    """Fetch a page with proper headers and error handling."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def extract_article_body(soup: BeautifulSoup) -> str:
    """Extract the main article body from a blog post page.

    Looks for common WordPress article containers.
    """
    # Try common WordPress article selectors
    selectors = [
        "article .entry-content",
        "article .post-content",
        "div.entry-content",
        "div.post-content",
        "article",
        "div.article-body",
        "div.content",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator="\n", strip=True)
            if len(text) > 100:  # Only accept if substantial content
                return text
    # Fallback: get all paragraph text
    paragraphs = soup.find_all("p")
    if paragraphs:
        return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    return ""


def extract_date(soup: BeautifulSoup) -> Optional[str]:
    """Extract the publication date from a blog post page."""
    # Try various date selectors
    date_selectors = [
        "time[datetime]",
        "meta[property='article:published_time']",
        "meta[name='date']",
        "span.published",
        "time.published",
    ]
    for selector in date_selectors:
        element = soup.select_one(selector)
        if element:
            if element.get("datetime"):
                return element["datetime"][:10]  # YYYY-MM-DD
            if element.get("content"):
                return element["content"][:10]
            text = element.get_text(strip=True)
            # Try to parse common date formats
            for fmt in ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"]:
                try:
                    dt = datetime.strptime(text, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


def extract_title(soup: BeautifulSoup) -> str:
    """Extract the article title."""
    title_selectors = [
        "h1.entry-title",
        "h1.post-title",
        "h1",
        "meta[property='og:title']",
    ]
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element:
            if element.get("content"):
                return element["content"]
            return element.get_text(strip=True)
    return ""


def scrape_blog_posts(start_url: str = BASE_URL, max_posts: int = MAX_POSTS) -> List[Dict]:
    """Scrape blog posts from scottadamsslog.com.

    Args:
        start_url: URL to start scraping from (usually the blog index).
        max_posts: Maximum number of posts to collect.

    Returns:
        List of sample dictionaries conforming to the corpus schema.
    """
    samples = []
    seen_urls = set()

    # First, get the blog index page to find post links
    logger.info(f"Fetching blog index: {start_url}")
    response = fetch_page(start_url)
    if not response:
        return samples

    soup = BeautifulSoup(response.text, "lxml")

    # Find all links to blog posts
    post_links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        # Match blog post URLs
        if re.search(r"/\d{4}/\d{2}/", href) and "/blog/" in href:
            if href not in seen_urls:
                seen_urls.add(href)
                post_links.append(href)

    logger.info(f"Found {len(post_links)} blog post links on index page")

    # Also try to paginate through the blog
    page = 2
    while len(post_links) < max_posts and page <= 10:
        page_url = f"{start_url}/page/{page}/"
        response = fetch_page(page_url)
        if not response:
            break
        soup = BeautifulSoup(response.text, "lxml")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if re.search(r"/\d{4}/\d{2}/", href) and "/blog/" in href:
                if href not in seen_urls:
                    seen_urls.add(href)
                    post_links.append(href)
        page += 1
        time.sleep(1)  # Be polite

    # Now scrape each post
    for i, post_url in enumerate(post_links[:max_posts]):
        logger.info(f"Scraping post {i+1}/{len(post_links[:max_posts])}: {post_url}")
        response = fetch_page(post_url)
        if not response:
            continue

        time.sleep(1.5)  # Rate limiting

        soup = BeautifulSoup(response.text, "lxml")
        body_text = extract_article_body(soup)
        pub_date = extract_date(soup)
        title = extract_title(soup)

        if not body_text or len(body_text) < 50:
            logger.warning(f"Skipping post with insufficient content: {post_url}")
            continue

        sample = {
            "id": f"blog_{i+1:04d}",
            "text": body_text,
            "source_type": "blog",
            "source_url": post_url,
            "date": pub_date or datetime.now().strftime("%Y-%m-%d"),
            "author": "Scott Adams",
            "raw_html": response.text[:5000] if response.text else None,
        }
        samples.append(sample)

        logger.info(f"  Collected: '{title[:60]}...' ({len(body_text)} chars)")

    logger.info(f"Total blog posts collected: {len(samples)}")
    return samples


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    posts = scrape_blog_posts()
    print(f"\nCollected {len(posts)} blog posts")
    if posts:
        print(f"First post date: {posts[0]['date']}")
        print(f"First post length: {len(posts[0]['text'])} chars")
