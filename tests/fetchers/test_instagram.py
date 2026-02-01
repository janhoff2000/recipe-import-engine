"""Tests for Instagram fetcher."""

import pytest

from recipe_importer.fetchers.instagram import INSTAGRAM_URL_PATTERN, InstagramFetcher


class TestInstagramUrlPattern:
    """Test URL pattern matching."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.instagram.com/p/ABC123/",
            "https://instagram.com/p/ABC123/",
            "https://www.instagram.com/reel/ABC123/",
            "https://instagram.com/reel/XYZ789/",
            "https://www.instagram.com/reels/ABC123/",
            "http://instagram.com/p/test-post/",
            "https://www.instagram.com/p/ABC_123-xyz/",
        ],
    )
    def test_valid_instagram_urls(self, url: str) -> None:
        """Should match valid Instagram post and reel URLs."""
        assert INSTAGRAM_URL_PATTERN.match(url) is not None

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.instagram.com/username/",
            "https://www.instagram.com/",
            "https://www.tiktok.com/@user/video/123",
            "https://youtube.com/watch?v=abc",
            "https://facebook.com/post/123",
            "https://www.instagram.com/stories/user/123/",
            "not a url",
            "",
        ],
    )
    def test_invalid_instagram_urls(self, url: str) -> None:
        """Should not match non-post/reel URLs."""
        assert INSTAGRAM_URL_PATTERN.match(url) is None


class TestInstagramFetcher:
    """Test InstagramFetcher class."""

    def test_can_handle_valid_url(self) -> None:
        """Should return True for valid Instagram URLs."""
        fetcher = InstagramFetcher(meta_app_token="test_token")
        assert fetcher.can_handle("https://www.instagram.com/p/ABC123/") is True
        assert fetcher.can_handle("https://instagram.com/reel/XYZ789/") is True

    def test_can_handle_invalid_url(self) -> None:
        """Should return False for non-Instagram URLs."""
        fetcher = InstagramFetcher(meta_app_token="test_token")
        assert fetcher.can_handle("https://tiktok.com/@user/video/123") is False
        assert fetcher.can_handle("https://youtube.com/watch?v=abc") is False
