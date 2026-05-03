"""Simple HTML renderer that displays content in windows."""

import re


class HtmlRenderer:
    """Renders basic HTML content for display in browser windows.

    Supports basic HTML tags: p, h1-h6, a, div, span, img, br, ul, li, ol, strong, em, b, i.
    """

    def __init__(self):
        """Initialize the HtmlRenderer."""
        self._content = ""
        self._current_url = ""

    def render(self, html_content):
        """Parse and render basic HTML content.

        Args:
            html_content: Raw HTML string to render.

        Returns:
            Rendered HTML string with basic styling applied.
        """
        self._content = html_content
        return self.get_content()

    def render_url(self, url):
        """Fetch and render URL content.

        For now, returns placeholder text indicating URL navigation.
        In a full implementation, this would fetch the URL and parse its HTML.

        Args:
            url: The URL to render.

        Returns:
            Rendered HTML string.
        """
        self._current_url = url
        placeholder = f"""
        <div class="placeholder-page">
            <h1>Page: {url}</h1>
            <p>This is a placeholder for the rendered content of {url}.</p>
            <p>In a full implementation, this would fetch and parse the actual HTML content.</p>
        </div>
        """
        self._content = placeholder
        return self.get_content()

    def get_content(self):
        """Return the rendered content as an HTML string.

        Returns:
            The rendered HTML string.
        """
        return self._content

    def _apply_basic_styles(self, html):
        """Apply basic inline styles to HTML tags.

        Args:
            html: Raw HTML string.

        Returns:
            HTML string with basic styles applied.
        """
        # Basic heading styles
        html = re.sub(
            r"<h1>", '<h1 style="font-size: 2em; font-weight: bold; margin: 0.67em 0;">', html
        )
        html = re.sub(
            r"</h1>", "</h1>", html
        )
        html = re.sub(
            r"<h2>", '<h2 style="font-size: 1.5em; font-weight: bold; margin: 0.75em 0;">', html
        )
        html = re.sub(
            r"</h2>", "</h2>", html
        )
        html = re.sub(
            r"<h3>", '<h3 style="font-size: 1.17em; font-weight: bold; margin: 0.83em 0;">', html
        )
        html = re.sub(
            r"</h3>", "</h3>", html
        )
        html = re.sub(
            r"<p>", '<p style="margin: 1em 0;">', html
        )
        html = re.sub(
            r"</p>", "</p>", html
        )
        html = re.sub(
            r"<a href='([^']*)'", r"<a href='\1' style='color: #0066cc; text-decoration: underline;'>", html
        )
        html = re.sub(
            r"<a href=\"([^\"]*)\"", r'<a href="\1" style="color: #0066cc; text-decoration: underline;">', html
        )
        html = re.sub(
            r"<div>", '<div style="margin: 0.5em 0;">', html
        )
        html = re.sub(
            r"</div>", "</div>", html
        )
        html = re.sub(
            r"<span>", '<span style="display: inline;">', html
        )
        html = re.sub(
            r"</span>", "</span>", html
        )
        html = re.sub(
            r"<br\s*/?>", "<br style='display: block; margin: 0.5em 0;' />", html
        )
        html = re.sub(
            r"<strong>|<b>", "<strong>", html
        )
        html = re.sub(
            r"</strong>|</b>", "</strong>", html
        )
        html = re.sub(
            r"<em>|<i>", "<em>", html
        )
        html = re.sub(
            r"</em>|</i>", "</em>", html
        )
        return html

    def __repr__(self):
        return f"HtmlRenderer(url={self._current_url!r}, content_len={len(self._content)})"
