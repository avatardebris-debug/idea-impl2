"""Browser-based HTML fetching with anti-detection."""

import logging
import time
from typing import Optional

from src.scraper.anti_detect import AntiDetect

logger = logging.getLogger(__name__)


class BrowserFetcher:
    """Fetches HTML from URLs using a headless browser with anti-detection."""

    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.headers = AntiDetect.get_headers()
        self.viewport = AntiDetect.get_viewport()

    def fetch(self, url: str) -> Optional[str]:
        """Fetch HTML from a URL.

        Args:
            url: The URL to fetch.

        Returns:
            HTML string or None if fetch fails.
        """
        logger.info(f"Fetching URL: {url}")

        try:
            # Use Playwright for rendering
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ],
                )

                context = browser.new_context(
                    viewport=self.viewport,
                    user_agent=AntiDetect.get_user_agent(),
                    locale="en-US",
                    timezone_id="America/New_York",
                )

                # Add headers
                context.set_extra_http_headers(self.headers)

                page = context.new_page()

                # Navigate to URL
                response = page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)

                if response is None or response.status >= 400:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status if response else 'N/A'}")
                    browser.close()
                    return None

                # Wait for content to load
                page.wait_for_timeout(2000)

                # Get HTML
                html = page.content()

                browser.close()

                if not html:
                    logger.warning(f"No HTML content from {url}")
                    return None

                logger.info(f"Successfully fetched {url} ({len(html)} bytes)")
                return html

        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch HTML with retry logic.

        Args:
            url: The URL to fetch.
            max_retries: Maximum number of retries.

        Returns:
            HTML string or None if all retries fail.
        """
        for attempt in range(max_retries):
            html = self.fetch(url)
            if html:
                return html

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {url} in {wait_time}s")
                time.sleep(wait_time)

        logger.error(f"All {max_retries} retries failed for {url}")
        return None
