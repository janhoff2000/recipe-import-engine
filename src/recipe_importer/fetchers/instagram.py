"""Instagram oEmbed fetcher using Meta's Graph API."""

import re
from html import unescape

import httpx

from recipe_importer.config import get_settings
from recipe_importer.core.exceptions import (
    ContentNotFoundError,
    FetchError,
    PlatformAuthError,
    PlatformRateLimitError,
)
from recipe_importer.fetchers.base import FetchResult

INSTAGRAM_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]+)",
    re.IGNORECASE,
)

OEMBED_ENDPOINT = "https://graph.facebook.com/v21.0/instagram_oembed"


class InstagramFetcher:
    """Fetches Instagram post/reel content via Meta oEmbed API."""

    def __init__(self, meta_app_token: str | None = None) -> None:
        """Initialize with optional custom Meta App Token (BYOK support)."""
        self._custom_token = meta_app_token

    @property
    def _token(self) -> str:
        """Get the Meta App Token to use."""
        if self._custom_token:
            return self._custom_token

        settings = get_settings()
        token = settings.effective_meta_token
        if token:
            return token

        raise PlatformAuthError(
            "No Meta App Token configured. "
            "Set META_APP_TOKEN or META_APP_ID+META_APP_SECRET env vars, "
            "or provide via X-Meta-App-Token header."
        )

    def can_handle(self, url: str) -> bool:
        """Check if URL is an Instagram post or reel."""
        return bool(INSTAGRAM_URL_PATTERN.match(url))

    async def fetch(self, url: str) -> FetchResult:
        """Fetch Instagram post content via oEmbed API."""
        if not self.can_handle(url):
            raise FetchError(f"URL is not a valid Instagram post/reel: {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                OEMBED_ENDPOINT,
                params={
                    "url": url,
                    "access_token": self._token,
                    "omitscript": "true",
                },
            )

        if response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                raise ContentNotFoundError(f"Instagram post not found: {url}")
            raise FetchError(f"Instagram API error: {error_msg}")

        if response.status_code == 429:
            raise PlatformRateLimitError("Instagram API rate limit exceeded")

        if response.status_code in (401, 403):
            raise PlatformAuthError("Invalid or expired Meta App Token")

        response.raise_for_status()

        data = response.json()
        caption = self._extract_caption(data.get("html", ""))

        return FetchResult(
            url=url,
            platform="instagram",
            caption=caption,
            title=data.get("title"),
            image_url=None,  # Deprecated in Nov 2025
            author=None,  # Deprecated in Nov 2025
        )

    def _extract_caption(self, embed_html: str) -> str | None:
        """Extract caption text from oEmbed HTML response.

        The oEmbed HTML contains the caption within a blockquote element.
        We parse it to extract just the text content.
        """
        if not embed_html:
            return None

        # The caption is typically in a <p> tag within the blockquote
        # Pattern: <p>caption text</p>
        caption_match = re.search(
            r"<p[^>]*>([^<]+)</p>",
            embed_html,
            re.DOTALL,
        )

        if caption_match:
            caption = caption_match.group(1).strip()
            return unescape(caption) if caption else None

        # Fallback: try to get any text content between blockquote tags
        blockquote_match = re.search(
            r"<blockquote[^>]*>(.*?)</blockquote>",
            embed_html,
            re.DOTALL | re.IGNORECASE,
        )

        if blockquote_match:
            # Strip all HTML tags
            text = re.sub(r"<[^>]+>", " ", blockquote_match.group(1))
            text = " ".join(text.split())  # Normalize whitespace
            return unescape(text) if text else None

        return None
