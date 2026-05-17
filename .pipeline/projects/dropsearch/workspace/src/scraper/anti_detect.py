"""Anti-detection headers and configuration for browser automation."""

import random
import time


class AntiDetect:
    """Provides realistic browser headers to avoid detection."""

    # Common user agent strings
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    ]

    # Common viewport sizes
    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1440, "height": 900},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1600, "height": 900},
    ]

    @classmethod
    def get_headers(cls) -> dict:
        """Get realistic HTTP headers."""
        return {
            "User-Agent": cls._random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": cls._random_accept_language(),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-Ch-Ua": cls._random_sec_ch_ua(),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": cls._random_platform(),
            "Sec-Ch-Ua-Platform-Version": cls._random_platform_version(),
            "Sec-Ch-Ua-Full-Version-List": cls._random_full_version_list(),
            "Sec-Ch-Ua-Arch": cls._random_arch(),
            "Sec-Ch-Ua-Bitness": "64",
            "Sec-Ch-Ua-Model": "",
            "Sec-Ch-Ua-Platform-Bitness": "64",
            "Sec-Ch-Ua-Full-Version": cls._random_full_version(),
            "Sec-Ch-Ua-Wow64": "false",
            "Sec-Ch-Ua-Platform-Version": cls._random_platform_version(),
            "Cache-Control": "max-age=0",
            "If-None-Match": cls._random_etag(),
            "If-Modified-Since": cls._random_if_modified_since(),
        }

    @classmethod
    def get_user_agent(cls) -> str:
        """Get a random user agent string."""
        return cls._random_user_agent()

    @classmethod
    def get_viewport(cls) -> dict:
        """Get a random viewport size."""
        return cls._random_viewport()

    @classmethod
    def _random_user_agent(cls) -> str:
        """Get a random user agent string."""
        return random.choice(cls.USER_AGENTS)

    @classmethod
    def _random_accept_language(cls) -> str:
        """Get a random accept language header."""
        languages = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "en-CA,en;q=0.9",
            "en-AU,en;q=0.9",
            "de-DE,de;q=0.9,en;q=0.8",
            "fr-FR,fr;q=0.9,en;q=0.8",
            "es-ES,es;q=0.9,en;q=0.8",
            "it-IT,it;q=0.9,en;q=0.8",
            "pt-BR,pt;q=0.9,en;q=0.8",
            "nl-NL,nl;q=0.9,en;q=0.8",
        ]
        return random.choice(languages)

    @classmethod
    def _random_sec_ch_ua(cls) -> str:
        """Get a random Sec-Ch-Ua header."""
        browsers = [
            '"Chromium";v="120", "Google Chrome";v="120"',
            '"Not_A Brand";v="8", "Chromium";v="120"',
            '"Microsoft Edge";v="120", "Chromium";v="120"',
        ]
        return random.choice(browsers)

    @classmethod
    def _random_platform(cls) -> str:
        """Get a random platform header."""
        platforms = ['"Windows"', '"macOS"', '"Linux"']
        return random.choice(platforms)

    @classmethod
    def _random_platform_version(cls) -> str:
        """Get a random platform version header."""
        versions = ['"10.0"', '"13.0"', '"14.0"', '"15.0"']
        return random.choice(versions)

    @classmethod
    def _random_full_version_list(cls) -> str:
        """Get a random full version list header."""
        versions = [
            '"Chromium";v="120.0.6099.130", "Google Chrome";v="120.0.6099.130"',
            '"Not_A Brand";v="8.0.0.0", "Chromium";v="120.0.6099.130"',
            '"Microsoft Edge";v="120.0.2210.91", "Chromium";v="120.0.6099.130"',
        ]
        return random.choice(versions)

    @classmethod
    def _random_arch(cls) -> str:
        """Get a random architecture header."""
        return random.choice(['"x86"', '"arm"'])

    @classmethod
    def _random_full_version(cls) -> str:
        """Get a random full version header."""
        versions = ['"120.0.6099.130"', '"119.0.6045.199"', '"121.0.6147.82"']
        return random.choice(versions)

    @classmethod
    def _random_viewport(cls) -> dict:
        """Get a random viewport size."""
        return random.choice(cls.VIEWPORTS)

    @classmethod
    def _random_etag(cls) -> str:
        """Generate a random ETag."""
        return f'"{random.randint(100000, 999999)}-{random.randint(1000, 9999)}"'

    @classmethod
    def _random_if_modified_since(cls) -> str:
        """Generate a random If-Modified-Since date."""
        # Random date in the last 30 days
        days_ago = random.randint(0, 30)
        timestamp = time.time() - (days_ago * 86400)
        from email.utils import formatdate
        return formatdate(timestamp, usegmt=True)
